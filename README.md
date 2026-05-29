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
date-bounded Tavily evidence) — then checks whether the magnitude of the
Crupi–Tentori confirmation measure |Z| rank-correlates with the per-question
Brier-score improvement.

## Method

1. Load ForecastBench question + resolution sets dated **2025-10-26** and keep
   only entries with binary outcomes (`resolved_to ∈ {0, 1}`). When a question
   resolves at multiple horizons, keep only the **earliest** `resolution_date`
   per `(id, source)`. Fill templated variables in question text
   (`{resolution_date}`, `{forecast_due_date}`).
2. Elicit **P(H)** from `claude-haiku-4-5-20251001` (temperature 0) using only
   the question text, criteria, and background.
3. Retrieve evidence with **Tavily** bounded to
   `[freeze_datetime − 60 days, freeze_datetime]` to prevent post-forecast
   information leakage. Advanced search depth, markdown raw content, top 8
   results truncated to 2 000 chars each.
4. Elicit **P(H|E)** from the same model with question + retrieved snippets.
5. Compute **Brier scores** `(p − outcome)²` against the resolved outcome.
6. Compute the **Crupi–Tentori Z** confirmation measure:
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
cp .env.example .env  # fill in ANTHROPIC_API_KEY and TAVILY_API_KEY
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
without re-spending tokens on already-processed questions. Each output CSV is
a full superset of all prior runs it resumes from — always pass the *latest*
CSV to `analyze_results.py`.

```bash
# Pass 1: 100 random samples
python scripts/run_experiment.py --max-questions 100 --random --seed 1 \
    --out data/results/pass1.csv

# Pass 2: 100 more, excluding the first 100, merged into pass2.csv
python scripts/run_experiment.py --max-questions 100 --random --seed 2 \
    --resume-from data/results/pass1.csv \
    --out data/results/pass2.csv

# Pass 3: 100 more
python scripts/run_experiment.py --max-questions 100 --random --seed 3 \
    --resume-from data/results/pass2.csv \
    --out data/results/pass3.csv

python scripts/analyze_results.py data/results/pass3.csv
```

### Rate limits

Anthropic calls are throttled in-process against three per-minute budgets
(requests, input tokens, output tokens) to stay under Tier-1 limits without
tripping 429s. Defaults are set to Sonnet's Tier-1 budget — the tightest of
the three active models — with a ~10% safety margin, so the same settings are
safe for Haiku and well below Opus:

| setting | default | Tier-1 limit (Sonnet / Haiku / Opus) |
| --- | --- | --- |
| `requests_per_minute` | `45` | 50 / 50 / 50 |
| `input_tokens_per_minute` | `28_000` | 30K / 50K / 500K |
| `output_tokens_per_minute` | `7_500` | 8K / 10K / 80K |

Each call reserves its budget conservatively up front (input estimated from
prompt length, output reserved at `max_tokens`) and then commits the real
`usage.input_tokens` / `usage.output_tokens` from the response so windows
self-correct. On a 429 that survives the SDK's built-in `retry-after`-aware
retries, the limiter parks for the server-supplied cool-down and retries with
exponential backoff + jitter (`llm_max_retries=3` outer attempts,
`llm_sdk_max_retries=5` inside the SDK). Override any of these on the `Config`
dataclass if you are on a different tier.

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

A positive `rho` with a low p-value supports the hypothesis: questions where
the LLM updates more strongly on evidence are also the ones where retrieval
most improves its calibrated forecast.

## Results

The latest run (`run3.csv`, `run3_summary.json`) covers **100 binary
questions** sampled across 9 ForecastBench sources:

| source | n |
| --- | --- |
| polymarket | 20 |
| wikipedia | 16 |
| yfinance | 14 |
| fred | 13 |
| acled | 12 |
| dbnomics | 11 |
| manifold | 9 |
| infer | 3 |
| metaculus | 2 |

Headline numbers:

| metric | value |
| --- | --- |
| `spearman_abs_z_vs_brier_delta` | **ρ = 0.448, p = 2.9 × 10⁻⁶** |
| `mean_brier_h` (prior) | 0.182 |
| `mean_brier_he` (posterior) | 0.150 |
| `mean_brier_delta` (improvement) | +0.032 |
| `frac_brier_improved` | 0.520 |
| `mean_abs_z` | 0.358 |
| `frac_z_positive` | 0.400 |

**The hypothesis is supported.** The magnitude of the self-reported
Crupi–Tentori update `|Z|` is positively and significantly rank-correlated
with the per-question Brier improvement (ρ = 0.45, p ≈ 2.9 × 10⁻⁶ over
n = 100): questions where the model updates more strongly on retrieved
evidence are also the ones where retrieval most improves its calibrated
forecast. Retrieval helped on average (mean Brier dropped 0.182 → 0.150),
though only on a slim majority of questions (52%), and the model's updates were
more often downward than upward (`frac_z_positive` = 0.40).

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
fixture-based tests of the question/resolution loader (binary filtering,
joining, and earliest-`resolution_date` selection per `(id, source)`), and the
sliding-window rate limiter (acquire/commit, window expiry, `retry-after`
parsing, concurrency safety).

## Design choices

- **Evidence cutoff**: Tavily `end_date` is each question's `freeze_datetime`
  (not the resolution date), treating "dated before the resolution" as "dated
  before the forecast was due" to avoid retrieving news that effectively
  reveals the outcome.
- **Lookback**: 60 days before `freeze_datetime` — captures recent reporting
  without flooding the LLM with stale context.
- **Question scope**: a single set (`2025-10-26-llm.json`) holds 500 questions;
  1 073 are resolved with binary outcomes across multiple resolution horizons,
  which collapse to **348 unique questions** (one per `(id, source)`, earliest
  `resolution_date`) spanning 9 sources (acled, dbnomics, fred, infer, manifold,
  metaculus, polymarket, wikipedia, yfinance).
- **Caching**: required — reruns during analysis would otherwise burn API
  credits.
- **Throttling over erroring**: proactive rate limiting plus
  `retry-after`-aware backoff is preferred over letting the SDK raise
  `RateLimitError` mid-run, because a long sweep across ~1 000 questions
  compounds 429 noise.
- **Temperature 0**: maximizes reproducibility; relies on the model's
  chain-of-reasoning at decoding time rather than ensembling samples.

## References

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- Tavily Python SDK: <https://github.com/tavily-ai/tavily-python>
- Crupi & Tentori, *Confirmation Theory*: <https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf>
