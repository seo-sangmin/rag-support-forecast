from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FORECASTBENCH_QUESTION_URL = (
    "https://raw.githubusercontent.com/forecastingresearch/forecastbench-datasets/"
    "main/datasets/question_sets/{date}-llm.json"
)
FORECASTBENCH_RESOLUTION_URL = (
    "https://raw.githubusercontent.com/forecastingresearch/forecastbench-datasets/"
    "main/datasets/resolution_sets/{date}_resolution_set.json"
)


@dataclass(frozen=True)
class Config:
    model: str = "claude-haiku-4-5-20251001"
    temperature: float = 0.0
    max_tokens: int = 1024

    question_set_dates: tuple[str, ...] = ("2025-10-26",)
    lookback_days: int = 60
    # AskNews bills 5 credits per archive /news request regardless of article
    # count, so we request the SDK default of 10 for more evidence per credit.
    asknews_n_articles: int = 10
    asknews_method: str = "nl"
    asknews_snippet_chars: int = 2000

    # AskNews HTTP rate limits (token bucket): 1 request / 2s steady state with a
    # burst of 2. Concurrency (3, below) is enforced separately by the semaphore.
    asknews_request_interval_s: float = 2.0
    asknews_burst: int = 2

    # Separate concurrency caps so each external service throttles on its own:
    # retrieval (AskNews) and prompting (Anthropic) run as distinct phases.
    # AskNews caps concurrent requests at 3.
    asknews_concurrency: int = 3
    llm_concurrency: int = 8
    # Outer-loop retries for our own backoff; the SDK does its own retries
    # underneath (see ``llm_sdk_max_retries``).
    llm_max_retries: int = 3
    # Retries inside the Anthropic SDK; the SDK respects ``retry-after``
    # headers and applies exponential backoff between attempts.
    llm_sdk_max_retries: int = 5

    # Anthropic Tier-1 per-minute budgets. Defaults match Sonnet (the
    # tightest of the three active-tier limits) so the same settings are
    # safe for Haiku and well below Opus.
    requests_per_minute: int = 45
    input_tokens_per_minute: int = 28_000
    output_tokens_per_minute: int = 7_500

    raw_dir: Path = field(default_factory=lambda: REPO_ROOT / "data" / "raw")
    cache_dir: Path = field(default_factory=lambda: REPO_ROOT / "data" / "cache")
    results_dir: Path = field(default_factory=lambda: REPO_ROOT / "data" / "results")
