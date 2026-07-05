from __future__ import annotations

from .data import ResolvedQuestion

SYSTEM_PRIOR = (
    "You are a calibrated probabilistic forecaster. "
    "You will be given a binary forecasting question. "
    "Use only your prior knowledge; do not assume access to real-time information. "
    "Reply with a single JSON object on one line and nothing else: "
    '{"reasoning": "<brief reasoning, <= 80 words>", '
    '"probability": <number in [0, 1] giving P(question resolves YES)>}.'
)

SYSTEM_POSTERIOR = (
    "You are a calibrated probabilistic forecaster. "
    "You will be given a binary forecasting question and a set of retrieved evidence "
    "snippets. Treat sources skeptically; weigh evidence against your prior. "
    "Reply with a single JSON object on one line and nothing else: "
    '{"reasoning": "<brief reasoning that references the evidence, <= 120 words>", '
    '"probability": <number in [0, 1] giving P(question resolves YES | evidence)>}.'
)


def render_question(q: ResolvedQuestion) -> str:
    parts = [f"Question: {q.question}"]
    if q.resolution_criteria:
        parts.append(f"Resolution criteria: {q.resolution_criteria}")
    if q.background:
        parts.append(f"Background: {q.background}")
    return "\n\n".join(parts)


def render_evidence(snippets: list[dict], max_chars: int) -> str:
    """Render retrieved snippets for the posterior prompt.

    Snippets are cached in full (see ``retrieval.AskNewsRetriever.retrieve``);
    ``max_chars`` bounds each snippet's contribution to the prompt here, at the
    last moment before the LLM sees it.
    """
    if not snippets:
        return "No evidence retrieved."
    lines = []
    for i, s in enumerate(snippets, 1):
        url = s.get("url", "")
        published = s.get("published_date") or s.get("date") or "unknown date"
        title = s.get("title", "")
        content = (s.get("content") or s.get("raw_content") or "").strip()
        if len(content) > max_chars:
            content = content[:max_chars] + "…"
        lines.append(
            f"[snippet {i}] {title} ({url}, published {published})\n{content}"
        )
    return "\n\n".join(lines)
