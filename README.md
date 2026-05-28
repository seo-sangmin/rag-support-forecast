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
   only entries with binary outcomes (`resolved_to ∈ {0, 1}`). When a question
   is resolved at multiple horizons, only the **earliest** `resolution_date`
   per `(id, source)` is kept. Templated variables in question text
   (`{resolution_date}`, `{forecast_due_date}`) are filled in.
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
| `--random` | off | with `--max-questions N`, pick N at random instead of the first N |
| `--seed` | `0` | RNG seed for `--random` (fixed default = reproducible) |
| `--resume-from` | none | one or more prior result CSV paths; their `(id, source)` rows are excluded from sampling and merged into the new output |
| `--lookback-days` | `60` | Tavily `start_date` offset before `freeze_datetime` |
| `--out` | timestamped | output CSV path |

Both LLM and Tavily calls are cached on disk under `data/cache/` keyed by a
SHA-256 of their inputs, so reruns are free.

### Iterative runs

`--resume-from` lets you chip away at the full dataset across multiple runs
without re-spending tokens on questions you've already processed. Each
output CSV is a full superset of all prior runs it resumes from — always
pass the *latest* CSV to `analyze_results.py`.

```bash
# Pass 1: 100 random samples
python scripts/run_experiment.py --max-questions 100 --random --seed 1 \
    --out data/results/iter1.csv

# Pass 2: 100 more, excluding the first 100, merged into iter2.csv
python scripts/run_experiment.py --max-questions 100 --random --seed 2 \
    --resume-from data/results/iter1.csv \
    --out data/results/iter2.csv

# Pass 3: 100 more again
python scripts/run_experiment.py --max-questions 100 --random --seed 3 \
    --resume-from data/results/iter2.csv \
    --out data/results/iter3.csv

python scripts/analyze_results.py data/results/iter3.csv
```

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

## Results

The latest run (`data/results/iter2.csv`, `iter2_summary.json`) covers
**99 binary questions** sampled across 7 ForecastBench sources:

| source | n |
| --- | --- |
| yfinance | 21 |
| wikipedia | 20 |
| fred | 20 |
| dbnomics | 15 |
| acled | 14 |
| polymarket | 8 |
| infer | 1 |

Headline numbers:

| metric | value |
| --- | --- |
| `spearman_abs_z_vs_brier_delta` | **ρ = 0.453, p = 2.5 × 10⁻⁶** |
| `mean_brier_h` (prior) | 0.160 |
| `mean_brier_he` (posterior) | 0.137 |
| `mean_brier_delta` (improvement) | +0.023 |
| `frac_brier_improved` | 0.556 |
| `mean_abs_z` | 0.385 |
| `frac_z_positive` | 0.404 |

**The hypothesis is supported.** The magnitude of the self-reported
Crupi–Tentori update `|Z|` is positively and significantly rank-correlated
with the per-question Brier improvement (ρ = 0.45, p ≈ 2.5 × 10⁻⁶ over
n = 99): questions where the model updates more strongly on retrieved
evidence are also the ones where retrieval most improves its calibrated
forecast. Retrieval helped on average (mean Brier dropped 0.160 → 0.137),
though only on a slim majority of questions (55.6%), and the model's updates
were more often downward than upward (`frac_z_positive` = 0.40).

These figures supersede the earlier 9-question smoke run
(`iter1_summary.json`), where the same correlation (ρ = 0.55) was not yet
significant (p ≈ 0.12) at that sample size.

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
fixture-based tests of the question/resolution loader (binary filtering /
joining and earliest-`resolution_date` selection per `(id, source)`), and the
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
