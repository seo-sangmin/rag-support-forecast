from __future__ import annotations

import asyncio
import csv
import random
from dataclasses import asdict, dataclass
from pathlib import Path

from .config import Config
from .data import ResolvedQuestion, load_resolved_questions
from .forecasting import ForecastClient
from .metrics import brier, z_crupi_tentori
from .retrieval import AskNewsRetriever


@dataclass
class Row:
    id: str
    source: str
    question: str
    freeze_datetime: str
    resolution_date: str
    outcome: float
    p_h: float
    p_he: float
    n_evidence: int
    brier_h: float
    brier_he: float
    brier_delta: float
    z: float
    abs_z: float


def _key(q: ResolvedQuestion) -> tuple[str, str]:
    return (q.id, q.source)


def _build_row(
    q: ResolvedQuestion,
    prior: dict,
    posterior: dict,
    evidence: list[dict],
) -> Row:
    p_h = prior["probability"]
    p_he = posterior["probability"]
    bh = brier(p_h, q.outcome)
    bhe = brier(p_he, q.outcome)
    z = z_crupi_tentori(p_h, p_he)
    return Row(
        id=q.id,
        source=q.source,
        question=q.question,
        freeze_datetime=q.freeze_datetime.isoformat(),
        resolution_date=q.resolution_date,
        outcome=q.outcome,
        p_h=p_h,
        p_he=p_he,
        n_evidence=len(evidence),
        brier_h=bh,
        brier_he=bhe,
        brier_delta=bh - bhe,
        z=z,
        abs_z=abs(z),
    )


async def _retrieve_all(
    questions: list[ResolvedQuestion],
    retriever: AskNewsRetriever,
    cfg: Config,
) -> dict[tuple[str, str], list[dict]]:
    """Phase 1 -- fetch evidence for every question (AskNews only).

    Returns a map from ``(id, source)`` to that question's evidence. A retrieval
    error drops the question from the map (and so from prompting); an empty
    result list is kept, since "no articles" is valid evidence.
    """
    sem = asyncio.Semaphore(cfg.asknews_concurrency)

    async def one(
        q: ResolvedQuestion,
    ) -> tuple[tuple[str, str], list[dict] | None]:
        async with sem:
            try:
                return _key(q), await retriever.retrieve(q)
            except Exception as e:  # noqa: BLE001
                print(f"  ! retrieval skipped {q.id}: {e}")
                return _key(q), None

    evidence: dict[tuple[str, str], list[dict]] = {}
    tasks = [one(q) for q in questions]
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        k, v = await coro
        if v is not None:
            evidence[k] = v
        if i % 5 == 0 or i == len(tasks):
            print(f"  retrieval progress: {i}/{len(tasks)}")
    return evidence


async def _forecast_all(
    questions: list[ResolvedQuestion],
    evidence: dict[tuple[str, str], list[dict]],
    forecaster: ForecastClient,
    cfg: Config,
) -> list[Row]:
    """Phase 2 -- prompt prior + posterior for each retrieved question (Anthropic only).

    Questions absent from ``evidence`` (retrieval failed) are skipped; a
    prompting error skips just that question's row.
    """
    sem = asyncio.Semaphore(cfg.llm_concurrency)

    async def one(q: ResolvedQuestion) -> Row | None:
        ev = evidence.get(_key(q))
        if ev is None:
            return None
        async with sem:
            try:
                prior = await forecaster.estimate_p_h(q)
                posterior = await forecaster.estimate_p_h_given_e(q, ev)
            except Exception as e:  # noqa: BLE001
                print(f"  ! forecast skipped {q.id}: {e}")
                return None
        return _build_row(q, prior, posterior, ev)

    rows: list[Row] = []
    tasks = [one(q) for q in questions]
    for i, coro in enumerate(asyncio.as_completed(tasks), 1):
        row = await coro
        if row is not None:
            rows.append(row)
        if i % 5 == 0 or i == len(tasks):
            print(f"  forecast progress: {i}/{len(tasks)}")
    return rows


def _load_processed(
    paths: list[Path] | None,
) -> tuple[set[tuple[str, str]], list[dict]]:
    """Return ((id, source) keys already processed, prior rows verbatim).

    First-seen wins on duplicates across paths, so passing the most recent
    CSV last preserves the earliest recorded values.
    """
    if not paths:
        return set(), []
    keys: set[tuple[str, str]] = set()
    rows: list[dict] = []
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"--resume-from path not found: {p}")
        with p.open(newline="") as f:
            reader = csv.DictReader(f)
            missing = {"id", "source"} - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"{p}: missing required columns {sorted(missing)}")
            for r in reader:
                k = (r["id"], r["source"])
                if k in keys:
                    continue
                keys.add(k)
                rows.append(r)
    return keys, rows


def _filter_questions(
    questions: list[ResolvedQuestion], processed: set[tuple[str, str]]
) -> list[ResolvedQuestion]:
    return [q for q in questions if (q.id, q.source) not in processed]


def _sample_questions(
    questions: list[ResolvedQuestion], n: int, seed: int
) -> list[ResolvedQuestion]:
    """Random subsample of size min(n, len(questions)) using a seeded RNG."""
    k = min(n, len(questions))
    return random.Random(seed).sample(questions, k)


def _write_combined_csv(
    prior_rows: list[dict], new_rows: list[Row], out_csv: Path
) -> None:
    fieldnames = list(Row.__annotations__.keys())
    seen: set[tuple[str, str]] = set()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in prior_rows:
            k = (r.get("id", ""), r.get("source", ""))
            if k in seen:
                continue
            seen.add(k)
            w.writerow({c: r.get(c, "") for c in fieldnames})
        for r in new_rows:
            k = (r.id, r.source)
            if k in seen:
                continue
            seen.add(k)
            w.writerow(asdict(r))


async def run(
    cfg: Config,
    max_questions: int | None,
    out_csv: Path,
    *,
    random_sample: bool = False,
    seed: int = 0,
    resume_from: list[Path] | None = None,
) -> int:
    questions: list[ResolvedQuestion] = []
    for date in cfg.question_set_dates:
        questions.extend(load_resolved_questions(date, cfg))
    total_loaded = len(questions)

    processed_keys, prior_rows = _load_processed(resume_from)
    if processed_keys:
        questions = _filter_questions(questions, processed_keys)
        print(
            f"Loaded {total_loaded}; excluding {len(processed_keys)} "
            f"already-processed; {len(questions)} remain"
        )
    else:
        print(f"Loaded {total_loaded} resolved binary questions")

    if max_questions is not None:
        if random_sample:
            if max_questions > len(questions):
                print(
                    f"  ! requested N={max_questions} > pool={len(questions)}, "
                    f"sampling all"
                )
            questions = _sample_questions(questions, max_questions, seed)
        else:
            questions = questions[:max_questions]

    if not questions:
        print(
            f"Nothing new to process; rewriting prior {len(prior_rows)} "
            f"rows to {out_csv}"
        )
        _write_combined_csv(prior_rows, [], out_csv)
        return 0

    forecaster = ForecastClient(cfg)
    retriever = AskNewsRetriever(cfg)

    print(f"Retrieving evidence for {len(questions)} questions…")
    evidence = await _retrieve_all(questions, retriever, cfg)
    print(f"  retrieved evidence for {len(evidence)}/{len(questions)} questions")

    print("Prompting prior + posterior…")
    rows = await _forecast_all(questions, evidence, forecaster, cfg)

    _write_combined_csv(prior_rows, rows, out_csv)
    total = len(prior_rows) + len(rows)
    print(f"Wrote {len(rows)} new rows ({total} total) to {out_csv}")
    return len(rows)
