from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.prompts import render_evidence


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
