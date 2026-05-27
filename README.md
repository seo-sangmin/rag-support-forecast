***\*This project is under verification and correction.***

# rag-support-forecast

Does an LLM's *self-reported* update from retrieved evidence track its *actual*
forecasting improvement? This repository runs a minimum viable experiment to
test the following hypothesis on binary forecasting questions from
[ForecastBench](https://www.forecastbench.org/):

> **For binary forecasting questions, LLM-estimated Bayesian confirmation
> measures computed from P(H) and P(H|E) are positively associated with
> improvements in LLM forecasting performance after retrieval, as evaluated by
> proper scoring rules against resolved outcomes.**

The experiment elicits two probabilities from Claude Haiku 4.5 for each
question — the prior P(H) (no retrieval) and the posterior P(H|E) (with
date-bounded Tavily evidence) — and then checks whether the magnitude of the
Crupi–Tentori confirmation measure |Z| ranks-correlates with the per-question
Brier-score improvement.

## Method

1. Load ForecastBench question + resolution sets dated **2025-10-26** and keep
   only entries with binary outcomes (`resolved_to ∈ {0, 1}`). Templated
   variables in question text (`{resolution_date}`, `{forecast_due_date}`)
   are filled in.
2. Elicit **P(H)** from `claude-haiku-4-5-20251001` (temperature 0) using only
   the question text, criteria, and background.
3. Retrieve evidence with **Tavily** bounded to
   `[freeze_datetime − 60 days, freeze_datetime]` so no post-forecast
   information leaks back. Advanced search depth, markdown raw content, top 8
   results truncated to 2000 chars each.
4. Elicit **P(H|E)** from the same model with the question + retrieved
   snippets.
5. Compute **Brier scores** `(p − outcome)²` against the resolved outcome.
6. Compute the **Crupi–Tentori Z** confirmation measure
   - `Z = (P(H|E) − P(H)) / (1 − P(H))` if `P(H|E) ≥ P(H)`
   - `Z = (P(H|E) − P(H)) / P(H)` otherwise
7. Report the **Spearman rank correlation** between `|Z|` and
   `Brier(P(H)) − Brier(P(H|E))`.

## Setup

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in ANTHROPIC_API_KEY and TAVILY_API_KEY
```

## Running

Smoke run (5 questions, ~10 LLM calls + 5 Tavily calls):

```bash
python scripts/run_experiment.py --question-sets 2025-10-26 --max-questions 5
python scripts/analyze_results.py data/results/run_*.csv
```

Full run on the 2025-10-26 set:

```bash
python scripts/run_experiment.py --question-sets 2025-10-26
python scripts/analyze_results.py data/results/run_*.csv
```

CLI flags for `run_experiment.py`:

| flag | default | meaning |
| --- | --- | --- |
| `--question-sets` | `2025-10-26` | comma-separated YYYY-MM-DD ForecastBench dates |
| `--max-questions` | (no cap) | process at most N questions |
| `--lookback-days` | `60` | Tavily `start_date` offset before `freeze_datetime` |
| `--out` | timestamped | output CSV path |

Both LLM and Tavily calls are cached on disk under `data/cache/` keyed by a
SHA-256 of their inputs, so reruns are free.

### Rate limits

Anthropic calls are throttled in-process against three per-minute budgets
(requests, input tokens, output tokens) so a full run stays under Tier-1
limits without tripping 429s. Defaults match Sonnet's Tier-1 budget — the
tightest of the three active models — with a ~10% safety margin, so the same
settings are safe for Haiku and well below Opus:

| setting | default | Tier-1 limit (Sonnet / Haiku / Opus) |
| --- | --- | --- |
| `requests_per_minute` | `45` | 50 / 50 / 50 |
| `input_tokens_per_minute` | `28_000` | 30K / 50K / 500K |
| `output_tokens_per_minute` | `7_500` | 8K / 10K / 80K |

Each call reserves its budget conservatively up front (input estimated from
prompt length, output reserved at `max_tokens`) and then commits the real
`usage.input_tokens` / `usage.output_tokens` from the response so the
windows self-correct. On a 429 that survives the SDK's built-in
`retry-after`-aware retries, the limiter is parked for the server-supplied
cool-down and the call is re-tried with exponential backoff + jitter
(`llm_max_retries=3` outer attempts, `llm_sdk_max_retries=5` inside the
SDK). Override any of these on the `Config` dataclass if you are on a
different tier.

## Outputs

`data/results/run_<timestamp>.csv` — one row per question with columns:
`id, source, question, freeze_datetime, resolution_date, outcome, p_h, p_he,
n_evidence, brier_h, brier_he, brier_delta, z, abs_z`.

`run_<timestamp>_summary.json` — written by `analyze_results.py`:

```json
{
  "n": ...,
  "mean_brier_h": ...,
  "mean_brier_he": ...,
  "mean_brier_delta": ...,
  "frac_brier_improved": ...,
  "mean_abs_z": ...,
  "frac_z_positive": ...,
  "spearman_abs_z_vs_brier_delta": {"rho": ..., "p_value": ...}
}
```

A positive `rho` (with low p-value) supports the hypothesis: questions where
the LLM updates more strongly given evidence are also the ones where
retrieval improves its calibrated forecast.

## Project layout

```
src/rag_forecast/
  config.py        — Config dataclass (model, paths, dates, concurrency, rate limits)
  data.py          — ForecastBench fetch + join + binary filter + template fill
  retrieval.py     — Tavily wrapper, date-bounded, snippet-truncated, cached
  forecasting.py   — Anthropic AsyncAnthropic, rate-limited + retrying, strict-JSON parse, cached
  rate_limiter.py  — async sliding-window RPM/ITPM/OTPM limiter with self-correction
  prompts.py       — system prompts for prior and posterior elicitation
  metrics.py       — brier, z_tentori_crupi, spearman
  cache.py         — content-hash JSON cache
  pipeline.py      — async orchestration, writes per-question CSV
scripts/
  run_experiment.py
  analyze_results.py
tests/             — unit tests for metrics, the data loader, and the rate limiter
```

## Tests

```bash
pytest -q
```

Covers the Brier formula at extremes, both branches and bounds of the
Crupi–Tentori Z, Spearman on perfect / anti-correlated / degenerate inputs,
a fixture-based smoke test of the question/resolution loader, and the
sliding-window rate limiter (acquire/commit, window expiry, `retry-after`
parsing, concurrency safety).

## Design choices

- **Evidence cutoff**: Tavily `end_date` is each question's `freeze_datetime`
  (not the resolution date). This re-reads the spec's "dated before the
  resolution" as "dated before the forecast was due", to avoid retrieving
  news that effectively reveals the outcome.
- **Lookback**: 60 days before `freeze_datetime` — captures recent reporting
  without flooding the LLM with stale context.
- **Question scope**: a single set (`2025-10-26-llm.json`) yields ~1000
  binary-resolved questions across 9 sources (acled, dbnomics, fred, infer,
  manifold, metaculus, polymarket, wikipedia, yfinance).
- **Caching**: required, since reruns during analysis would otherwise burn
  API credits.
- **Throttling over erroring**: proactive rate limiting plus
  `retry-after`-aware backoff is preferred over letting the SDK raise
  `RateLimitError` mid-run, because cached partial progress is small and a
  long sweep across ~1000 questions otherwise compounds 429 noise.
- **Temperature 0**: maximizes reproducibility; relies on the model's chain of
  reasoning at decoding time rather than ensembling samples.

## References

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- Tavily Python SDK: <https://github.com/tavily-ai/tavily-python>
- Crupi & Tentori, *Confirmation Theory*: <https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf>
