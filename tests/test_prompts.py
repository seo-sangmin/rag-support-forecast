from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.config import Config
from rag_forecast.data import ResolvedQuestion
from rag_forecast.forecasting import ForecastClient
from rag_forecast.prompts import (
    SYSTEM_POSTERIOR,
    SYSTEM_PRIOR,
    render_evidence,
    render_question,
)


def _question() -> ResolvedQuestion:
    return ResolvedQuestion(
        id="q1",
        source="metaculus",
        question="Will X happen?",
        background="Some context.",
        resolution_criteria="Use the platform's final outcome.",
        freeze_datetime=datetime(2025, 10, 16, tzinfo=timezone.utc),
        freeze_value=None,
        resolution_date="2025-12-01",
        outcome=1.0,
        question_set_date="2025-10-26",
    )


def test_market_criteria_default_preserves_existing_prompt() -> None:
    assert render_question(_question()) == (
        "Question: Will X happen?\n\n"
        "Resolution criteria: Use the platform's final outcome.\n\n"
        "Background: Some context."
    )


@pytest.mark.parametrize("criteria", ["", " \t\n", "N/A", "n/a", "  N/a\n"])
def test_unavailable_market_criteria_preserves_existing_prompt(criteria: str) -> None:
    question = _question()
    assert render_question(replace(question, market_info_resolution_criteria=criteria)) == (
        render_question(question)
    )


def test_market_criteria_supplements_existing_criteria_and_background() -> None:
    question = replace(
        _question(),
        market_info_resolution_criteria=(
            " \nOnly accounts held before January 1, 2025 count.\n"
            "Reports may arrive by March 1, 2026.\t "
        ),
    )
    assert render_question(question) == (
        "Question: Will X happen?\n\n"
        "Resolution criteria: Use the platform's final outcome.\n\n"
        "Market-specific rules and clarifications: "
        "Only accounts held before January 1, 2025 count.\n"
        "Reports may arrive by March 1, 2026.\n\n"
        "Background: Some context."
    )


async def test_both_forecast_prompts_include_market_criteria(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    question = replace(
        _question(),
        market_info_resolution_criteria=(
            "Only accounts held before January 1, 2025 count."
        ),
    )
    calls = []

    async def capture_call(system: str, user: str, date: str) -> dict:
        calls.append((system, user, date))
        return {"probability": 0.5, "reasoning": "Test response."}

    # Skip initialization so prompt coverage requires neither an API key nor a client.
    client = ForecastClient.__new__(ForecastClient)
    client.cfg = Config()
    monkeypatch.setattr(client, "_call", capture_call)

    await client.estimate_p_h(question)
    await client.estimate_p_h_given_e(question, [_snippet("Relevant evidence.")])

    assert [call[0] for call in calls] == [SYSTEM_PRIOR, SYSTEM_POSTERIOR]
    for _, prompt, date in calls:
        assert (
            "Market-specific rules and clarifications: "
            "Only accounts held before January 1, 2025 count."
        ) in prompt
        assert "Resolution criteria: Use the platform's final outcome." in prompt
        assert "Background: Some context." in prompt
        assert date == "2025-10-26"
    assert calls[0][1] == render_question(question)
    assert calls[1][1].startswith(calls[0][1] + "\n\nEvidence:\n")
    assert "Relevant evidence." in calls[1][1]


def _snippet(content: str) -> dict:
    return {
        "title": "Example headline",
        "url": "https://example.com/a",
        "content": content,
        "published_date": "2025-10-01T00:00:00+00:00",
        "source_id": "example",
    }


def test_long_content_capped_with_ellipsis() -> None:
    rendered = render_evidence([_snippet("x" * 3000)], max_chars=2000)
    body = rendered.split("\n", 1)[1]
    assert body == "x" * 2000 + "…"


def test_short_content_unchanged() -> None:
    rendered = render_evidence([_snippet("brief update")], max_chars=2000)
    assert "brief update" in rendered
    assert "…" not in rendered


def test_empty_snippets() -> None:
    assert render_evidence([], max_chars=2000) == "No evidence retrieved."
