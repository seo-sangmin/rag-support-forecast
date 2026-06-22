# rag-support-forecast

Existing work shows that retrieval-augmented forecasting systems can improve LLM forecasts, but it is unclear when and why retrieved evidence helps. This project tests whether the model’s own probability shift after retrieval provides a measurable signal of retrieval’s actual forecasting value. This repo runs a minimum viable experiment on binary
forecasting questions from [ForecastBench](https://www.forecastbench.org/) to
test one hypothesis:

> **For binary forecasting questions, LLM-estimated Bayesian confirmation
> measures computed from P(H) and P(H|E) are positively associated with
> improvements in LLM forecasting performance after retrieval, as evaluated by
> proper scoring rules against resolved outcomes.**

For each question we elicit two probabilities from Claude Haiku 4.5 — the prior
P(H) (no retrieval) and the posterior P(H|E) (with date-bounded AskNews
evidence) — then check whether the magnitude of the Crupi–Tentori confirmation
measure |Z| rank-correlates with the per-question Brier-score improvement.

## Method

1. Load the ForecastBench question + resolution sets dated **2025-10-26** and
   keep only binary outcomes (`resolved_to ∈ {0, 1}`), taking the **earliest**
   `resolution_date` per `(id, source)`. Fill templated variables
   (`{resolution_date}`, `{forecast_due_date}`).
2. Elicit **P(H)** from `claude-haiku-4-5-20251001` (temperature 0) from the
   question text, criteria, and background only.
3. Retrieve evidence with **AskNews**, bounded to
   `[freeze_datetime − 60 days, freeze_datetime]` to prevent post-forecast
   leakage (natural-language search, top 8 results, 2 000 chars each).
4. Elicit **P(H|E)** from the same model with the retrieved snippets added.
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
cp .env.example .env  # fill in ANTHROPIC_API_KEY and ASKNEWS_API_KEY
```

## Running

```bash
# Quick smoke test (~5 questions); drop --max-questions for the full set.
python scripts/run_experiment.py --question-sets 2025-10-26 --max-questions 5
python scripts/analyze_results.py data/results/run_*.csv
python scripts/audit_leakage.py  # offline: flag cached evidence dated after each freeze
```

CLI flags for `run_experiment.py`:

| flag | default | meaning |
| --- | --- | --- |
| `--question-sets` | `2025-10-26` | comma-separated YYYY-MM-DD ForecastBench dates |
| `--max-questions` | (no cap) | process at most N questions |
| `--random` | off | with `--max-questions N`, pick N at random instead of the first N |
| `--seed` | `0` | RNG seed for `--random` (fixed default = reproducible) |
| `--resume-from` | none | one or more prior result CSV paths; their `(id, source)` rows are excluded from sampling and merged into the new output |
| `--lookback-days` | `60` | AskNews search-window start offset before `freeze_datetime` |
| `--out` | timestamped | output CSV path |

LLM and AskNews calls are cached on disk under `data/cache/` keyed by a SHA-256
of their inputs, so reruns are free.

### Iterative runs

`--resume-from` lets you chip away at the full dataset across multiple runs
without re-spending tokens on already-processed questions. Each output CSV is a
superset of the runs it resumes from, so always pass the *latest* CSV to
`analyze_results.py`.

```bash
python scripts/run_experiment.py --max-questions 100 --random --seed 2 \
    --resume-from data/results/pass1.csv --out data/results/pass2.csv
```

### Rate limits

Anthropic calls are throttled in-process against three per-minute budgets
(requests, input tokens, output tokens) to stay under Tier-1 limits without
tripping 429s. Each call reserves its budget up front and then commits the real
`usage` from the response so the windows self-correct; a surviving 429 backs
off on the server-supplied `retry-after`. Defaults match Sonnet's Tier-1 budget
(the tightest active model) with a ~10% margin — safe for Haiku, well below
Opus. Override them on the `Config` dataclass for a different tier.

| setting | default | Tier-1 limit (Sonnet / Haiku / Opus) |
| --- | --- | --- |
| `requests_per_minute` | `45` | 50 / 50 / 50 |
| `input_tokens_per_minute` | `28_000` | 30K / 50K / 500K |
| `output_tokens_per_minute` | `7_500` | 8K / 10K / 80K |

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

## Results

The latest run (data/results/run3) covers **100 binary
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

**The hypothesis is supported:** `|Z|` is positively and significantly
rank-correlated with the per-question Brier improvement (ρ = 0.45,
p ≈ 2.9 × 10⁻⁶, n = 100). Retrieval helped on average (mean Brier 0.182 →
0.150), though only on a slim 52% majority of questions, and the model's
updates were more often downward than upward (`frac_z_positive` = 0.40).

## Project layout

```
src/rag_forecast/
  config.py        — Config dataclass (model, paths, dates, concurrency, rate limits)
  data.py          — ForecastBench fetch, join, binary filter, template fill
  retrieval.py     — date-bounded, cached AskNews wrapper
  forecasting.py   — rate-limited Anthropic client, strict-JSON parse, cached
  rate_limiter.py  — async sliding-window RPM/ITPM/OTPM limiter
  prompts.py       — prior/posterior elicitation prompts
  metrics.py       — brier, z_crupi_tentori, spearman
  cache.py         — content-hash JSON cache
  audit.py         — evidence-cutoff leakage audit over the AskNews cache
  pipeline.py      — async orchestration, writes per-question CSV
scripts/
  run_experiment.py
  analyze_results.py
  audit_leakage.py
tests/             — metrics, data loader, rate limiter, leakage audit
```

## Tests

```bash
pytest -q
```

Cover the Brier and Crupi–Tentori Z formulas (extremes, both branches, bounds),
Spearman edge cases, the question/resolution loader (binary filtering, joining,
earliest-`resolution_date` selection), and the sliding-window rate limiter
(acquire/commit, window expiry, `retry-after` parsing, concurrency).

## Design choices

- **Evidence cutoff**: the AskNews search window ends at each question's `freeze_datetime`
  (not the resolution date), so retrieval can't surface news that reveals the
  outcome. `python scripts/audit_leakage.py` verifies this held for the cached
  evidence — it flags any retrieved article published after its question's
  `freeze_datetime`, and fails closed on articles whose `published_date` is missing
  or unparseable (reported under `evidence_unverifiable` / `n_unverifiable`, since
  their provenance can't be verified as pre-freeze). Exits non-zero if it finds
  either (offline; reads the cache, never calls AskNews).
- **Model cutoff**: `claude-haiku-4-5-20251001`'s Jul 2025 training cutoff
  precedes every question's `freeze_datetime` and AskNews's search window, so
  neither the outcomes nor the retrieved evidence were in training.
- **Lookback**: 60 days before `freeze_datetime` — recent reporting without
  flooding the LLM with stale context.
- **Question scope**: the `2025-10-26-llm.json` set holds 500 questions; 1 073
  resolved binary outcomes across horizons collapse to **348 unique questions**
  (one per `(id, source)`, earliest `resolution_date`) across 9 sources.
- **Caching**: required — reruns during analysis would otherwise burn API
  credits.
- **Throttling over erroring**: proactive rate limiting plus `retry-after`
  backoff beats letting the SDK raise `RateLimitError` mid-run, since a sweep
  across ~1 000 questions compounds 429 noise.
- **Temperature 0**: maximizes reproducibility; relies on decode-time reasoning
  rather than ensembling samples.

## References

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- AskNews Python SDK: <https://github.com/emergentmethods/asknews-python-sdk>
- Crupi & Tentori, *Confirmation Theory*: <https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf>
