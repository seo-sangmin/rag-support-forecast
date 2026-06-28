from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .config import (
    FORECASTBENCH_QUESTION_URL,
    FORECASTBENCH_RESOLUTION_URL,
    Config,
)


@dataclass(frozen=True)
class ResolvedQuestion:
    id: str
    source: str
    question: str
    background: str
    resolution_criteria: str
    freeze_datetime: datetime
    freeze_value: float | None
    resolution_date: str
    outcome: float
    # ForecastBench question-set snapshot this question was loaded from (the value
    # passed to ``--question-sets``); used to namespace its cache entries by date.
    question_set_date: str = ""


def _download(url: str, dest: Path) -> dict:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            r = client.get(url)
            r.raise_for_status()
            dest.write_bytes(r.content)
    return json.loads(dest.read_text())


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _parse_dt(value: str) -> datetime:
    # ForecastBench uses ISO 8601 with offsets like "+00:00"; Python 3.11 handles "Z" too.
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def load_resolved_questions(date: str, cfg: Config) -> list[ResolvedQuestion]:
    """Download (if needed) and join question + resolution sets for a given date."""
    q_path = cfg.raw_dir / f"{date}-llm.json"
    r_path = cfg.raw_dir / f"{date}_resolution_set.json"
    questions = _download(FORECASTBENCH_QUESTION_URL.format(date=date), q_path)
    resolutions = _download(FORECASTBENCH_RESOLUTION_URL.format(date=date), r_path)

    forecast_due_date = str(questions.get("forecast_due_date", date))
    by_key: dict[tuple[str, str], dict] = {
        (str(q["id"]), q["source"]): q for q in questions["questions"]
    }

    def _fill(template: str, resolution_date: str) -> str:
        return template.replace("{resolution_date}", resolution_date).replace(
            "{forecast_due_date}", forecast_due_date
        )

    # ForecastBench resolves some questions at multiple horizons; keep only the
    # earliest resolution_date per (id, source). resolution_date is ISO
    # YYYY-MM-DD, so string comparison is chronological.
    earliest: dict[tuple[str, str], ResolvedQuestion] = {}
    for r in resolutions["resolutions"]:
        if not r.get("resolved"):
            continue
        outcome = r.get("resolved_to")
        if outcome not in (0.0, 1.0, 0, 1):
            continue
        key = (str(r["id"]), r["source"])
        q = by_key.get(key)
        if q is None:
            continue
        resolution_date = str(r["resolution_date"])
        prev = earliest.get(key)
        if prev is not None and prev.resolution_date <= resolution_date:
            continue
        earliest[key] = ResolvedQuestion(
            id=str(q["id"]),
            source=q["source"],
            question=_fill(q["question"], resolution_date),
            background=_fill(q.get("background") or "", resolution_date),
            resolution_criteria=_fill(
                q.get("resolution_criteria") or "", resolution_date
            ),
            freeze_datetime=_parse_dt(q["freeze_datetime"]),
            freeze_value=_safe_float(q.get("freeze_datetime_value")),
            resolution_date=resolution_date,
            outcome=float(outcome),
            question_set_date=date,
        )
    return list(earliest.values())
