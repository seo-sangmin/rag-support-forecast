from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.retrieval import _shorten_query


def test_short_query_unchanged() -> None:
    q = "Will San Diego FC make the playoffs in 2025?"
    assert _shorten_query(q) == q


def test_acled_worked_example_stripped() -> None:
    q = (
        "Will there be more than ten times as many 'Violence against civilians' "
        "in Kosovo for the 30 days before 2026-04-24 compared to one plus the "
        "30-day average of 'Violence against civilians' over the 360 days "
        "preceding 2025-10-26?\n\n"
        "e.g. If the forecast due date is 2024-01-01 and we have the following data:\n"
        "Date,'Violence against civilians'\n"
        "2023-11-11,1\n"
        "2023-10-10,2\n"
        "to calculate one plus the 30-day average ... 1+(1+2)/12=1.25.\n\n"
        "In this example, for the question to resolve positively, 13 (10 x 1.25) "
        "or more events would need to occur in the 30 days leading up to resolution."
    )
    assert len(q) > 400
    out = _shorten_query(q)
    assert len(out) <= 400
    assert "e.g." not in out
    assert out.endswith("?")
