# rag-support-forecast

Retrieval-augmented forecasting can improve LLM forecasts, but it is unclear
when and why retrieved evidence helps. This repo runs a minimum viable
experiment on binary forecasting questions from
[ForecastBench](https://www.forecastbench.org/) to test whether the model's own
probability shift after retrieval is a measurable signal of retrieval's actual
forecasting value:

> **For binary forecasting questions, LLM-estimated Bayesian confirmation
> measures computed from P(H) and P(H|E) are positively associated with
> improvements in LLM forecasting performance after retrieval, as evaluated by
> proper scoring rules against resolved outcomes.**

For each question we elicit two probabilities from Claude Haiku 4.5 — the prior
P(H) (no retrieval) and the posterior P(H|E) (with date-bounded AskNews
evidence) — then check whether the magnitude of the Crupi–Tentori confirmation
measure |Z| rank-correlates with the per-question Brier-score improvement.

## Method

1. Load the ForecastBench question + resolution sets dated **2025-10-26**, keep
   binary outcomes only, one row per `(id, source)` (earliest
   `resolution_date`) — **348 unique questions**.
2. Elicit **P(H)** from `claude-haiku-4-5-20251001` (temperature 0) from the
   question text, criteria, and background only.
3. Retrieve evidence with **AskNews**, bounded to
   `[freeze_datetime − 60 days, freeze_datetime]` to prevent post-forecast
   leakage (top 10 results).
4. Elicit **P(H|E)** from the same model with the retrieved snippets added.
5. Compute **Brier scores** `(p − outcome)²` against the resolved outcome.
6. Compute the **Crupi–Tentori Z**: `(P(H|E) − P(H)) / (1 − P(H))` if
   `P(H|E) ≥ P(H)`, else `(P(H|E) − P(H)) / P(H)`.
7. Report the **Spearman rank correlation** between `|Z|` and
   `Brier(P(H)) − Brier(P(H|E))`.

## Results

100 of the 348 questions so far, sampled at random and spanning 8 sources
(Polymarket, Wikipedia, FRED, DBnomics, ACLED, yfinance, Manifold, Metaculus).
Runs are resume-chained, so the latest CSV is the cumulative dataset:
`data/results/run_20260705T105447Z.csv` and its `_summary.json`.

| statistic (n = 100) | value |
| --- | --- |
| Spearman rho, \|Z\| vs Brier improvement | **0.21** (p = 0.039) |
| mean Brier, prior P(H) | 0.186 |
| mean Brier, posterior P(H\|E) | 0.162 |
| mean Brier improvement | +0.024 |
| questions improved by retrieval | 36% |
| mean \|Z\| | 0.227 |
| questions with Z > 0 | 43% |

The hypothesis is supported, modestly: |Z| is positively rank-correlated with
the Brier improvement, significant at the 0.05 level. Retrieval also helped on
average — mean Brier dropped from 0.186 to 0.162 — even though only 36% of
individual questions improved, so the gains where retrieval helped outweighed
the losses where it hurt. Caveats: this is 100 of 348 questions, a single
model, and p is only just below 0.05.

The evidence-cutoff audit over all 100 questions' cached retrievals
(`data/results/leakage_20260705T110757Z.json`) checked 927 articles and found
**zero** published after their question's `freeze_datetime` and zero with
unverifiable publication dates.

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

LLM and AskNews calls are cached on disk
(`data/cache/<date>/<stage>/<backend>/<hash>.json`), so reruns are free;
retrieval is cached per backend, not per model, so runs with different models
share it. Anthropic calls are throttled in-process against per-minute request
and token budgets (defaults fit Tier-1) with `retry-after` backoff on any
surviving 429 — tune them on the `Config` dataclass
(see `src/rag_forecast/rate_limiter.py`).

`--resume-from` chips away at the full set across runs without re-spending
tokens: each output CSV is a superset of the runs it resumes from, so pass the
*latest* CSV to `analyze_results.py`.

```bash
python scripts/run_experiment.py --max-questions 100 --random --seed 2 \
    --resume-from data/results/pass1.csv --out data/results/pass2.csv
```

## Outputs

`data/results/run_<timestamp>.csv` — one row per question with columns:
`id, source, question, freeze_datetime, resolution_date, outcome, p_h, p_he,
n_evidence, brier_h, brier_he, brier_delta, z, abs_z`.
`analyze_results.py` writes the aggregate statistics shown in
[Results](#results) to `run_<timestamp>_summary.json`.

## Project layout

```
src/rag_forecast/
  config.py        — Config dataclass (model, paths, dates, rate limits)
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

Covers the Brier and Crupi–Tentori Z formulas, Spearman edge cases, the
question/resolution loader, and the sliding-window rate limiter.

## Design choices

- **Evidence cutoff**: the AskNews search window ends at each question's
  `freeze_datetime` (not the resolution date), so retrieval can't surface news
  that reveals the outcome. `scripts/audit_leakage.py` verifies this held for
  the cached evidence, offline, and fails closed on articles whose
  `published_date` can't be verified as pre-freeze.
- **Model cutoff**: `claude-haiku-4-5-20251001`'s Jul 2025 training cutoff
  precedes every question's `freeze_datetime` and AskNews search window, so
  neither the outcomes nor the retrieved evidence were in training.
- **Lookback**: 60 days before `freeze_datetime` — recent reporting without
  flooding the LLM with stale context.
- **Temperature 0**: maximizes reproducibility; relies on decode-time
  reasoning rather than ensembling samples.

## References

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- AskNews Python SDK: <https://github.com/emergentmethods/asknews-python-sdk>
- Crupi & Tentori, *Confirmation Theory*: <https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf>
