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
   question text, resolution criteria, market-specific rules (when the source
   provides them), and background, with `freeze_datetime` explicitly stated as
   the forecast-as-of date.
3. Retrieve evidence with **AskNews**, bounded to
   `[freeze_datetime − 60 days, freeze_datetime]` to prevent post-forecast
   leakage (top 10 results).
4. Elicit **P(H|E)** from the same model with the same forecast-as-of date and
   the retrieved snippets added.
5. Compute **Brier scores** `(p − outcome)²` against the resolved outcome.
6. Compute the **Crupi–Tentori Z**: `(P(H|E) − P(H)) / (1 − P(H))` if
   `P(H|E) ≥ P(H)`, else `(P(H|E) − P(H)) / P(H)`.
7. Report the **Spearman rank correlation** between `|Z|` and
   `Brier(P(H)) − Brier(P(H|E))`, plus 95% **bootstrap confidence intervals**
   for it and for the mean Brier improvement. A bootstrap CI resamples the
   questions with replacement 10,000 times, recomputes the statistic each
   time, and keeps the middle 95% of those values.

## Results

**The current run does not support the hypothesis.** |Z| is essentially
uncorrelated with the Brier improvement (rho = 0.05, p = 0.64). Retrieval still
lowered the mean Brier score slightly, but that improvement is not
distinguishable from zero.

The run covers 100 of the 348 questions, sampled at random (seed 0) and
spanning 8 sources (Polymarket, Wikipedia, FRED, DBnomics, ACLED, yfinance,
Manifold, Metaculus). Runs are resume-chained (3 → 10 → 27 → 60 new questions
per batch), so the latest CSV is the cumulative dataset:
`data/results/run_20260914T104832Z.csv`, with its `_summary.json` and
`.meta.json`.

| statistic (n = 100) | current run (Sep 2026) | earlier run (Jul 2026) |
| --- | --- | --- |
| Spearman rho, \|Z\| vs Brier improvement | **0.05** (p = 0.64) | 0.21 (p = 0.039) |
| 95% CI for rho | −0.22 to 0.28 | −0.03 to 0.41 |
| mean Brier, prior P(H) | 0.187 | 0.186 |
| mean Brier, posterior P(H\|E) | 0.165 | 0.162 |
| mean Brier improvement | +0.022 | +0.024 |
| 95% CI for mean improvement | −0.008 to +0.057 | −0.006 to +0.056 |
| questions improved / worse / unchanged | 31% / 50% / 19% | 36% / 42% / 22% |
| mean \|Z\| | 0.194 | 0.227 |
| questions with Z > 0 | 47% | 43% |

**What changed between the runs.** Both runs use the same 100 questions, the
same cached AskNews evidence, and the same model at temperature 0. Only the
prompts differ. The current prompts state `freeze_datetime` as the
forecast-as-of date, add market-specific rules (present for 4 of the 100
questions), and cap the reasoning at 100 words for both prompts (previously 80
for the prior and 120 for the posterior). These prompt edits alone changed 69
of the 100 priors and 56 of the 100 posteriors, and moved rho from 0.21 to
0.05.

**How to read this.**

- The earlier "modest support" was fragile. Its p-value was just under 0.05,
  its bootstrap CI already included zero, and a prompt revision that left the
  questions and evidence unchanged erased it.
- The current CI (−0.22 to 0.28) is wide. The data show no clear association,
  but they cannot rule out a modest positive one (up to about 0.28) either.
  More questions would narrow it.
- Retrieval made forecasts worse on more questions (50%) than it improved
  (31%). The mean still improved because a few gains were large: the five
  biggest gains alone add up to more than the net total.
- Caveats: 100 of 348 questions, one model.

The earlier run is archived in `data/archive/` (results and its prompt cache).
Its CIs in the table come from running the current `analyze_results.py` on
`data/archive/results/run_20260705T105447Z.csv`; the archived `_summary.json`
predates CI reporting.

The evidence-cutoff audit over all 100 questions' cached retrievals
(`data/results/leakage_20260914T110031Z.json`) checked 927 articles and found
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
python scripts/analyze_results.py data/results/run_<timestamp>.csv  # the latest run CSV
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
n_evidence, brier_h, brier_he, brier_delta, z, abs_z, reasoning_h, reasoning_he`.

`data/results/run_<timestamp>.meta.json` — written before retrieval starts,
so a failed run still leaves a record. It stores the seed, sampling flags,
`--resume-from` parents, model and retrieval settings, and the `(id, source)`
pairs selected for this batch. At the end of the run it sets `complete` and
lists any `missing_question_ids` (questions skipped because retrieval or
forecasting failed).

`analyze_results.py` writes the aggregate statistics shown in
[Results](#results), including the bootstrap CIs and the settings used to
compute them, to `run_<timestamp>_summary.json`.

## Project layout

```
src/rag_forecast/
  config.py        — Config dataclass (model, paths, dates, rate limits)
  data.py          — ForecastBench fetch, join, binary filter, template fill
  retrieval.py     — date-bounded, cached AskNews wrapper
  forecasting.py   — rate-limited Anthropic client, strict-JSON parse, cached
  rate_limiter.py  — async sliding-window RPM/ITPM/OTPM limiter
  prompts.py       — prior/posterior elicitation prompts
  metrics.py       — brier, z_crupi_tentori, spearman, bootstrap_ci
  cache.py         — content-hash JSON cache
  audit.py         — evidence-cutoff leakage audit over the AskNews cache
  pipeline.py      — async orchestration, writes per-question CSV and run metadata
scripts/
  run_experiment.py
  analyze_results.py
  audit_leakage.py
tests/             — metrics, prompts, data loader, cache, pipeline, run metadata,
                     rate limiter, leakage audit
```

## Tests

```bash
pytest -q
```

Covers the Brier and Crupi–Tentori Z formulas, Spearman edge cases, bootstrap
CIs, prompt rendering, the question/resolution loader, the cache, resume and CSV
handling, run metadata, the leakage audit, and the sliding-window rate limiter.

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
