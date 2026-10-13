# rag-support-forecast

Retrieval-augmented forecasting can improve LLM forecasts, but it is unclear
when and why retrieved evidence helps. This repo runs a minimum viable
experiment on binary forecasting questions from
[ForecastBench](https://www.forecastbench.org/) to ask whether the model's own
probability shift after retrieval is a measurable signal of retrieval's actual
forecasting value:

> **How strongly are measures, computed from an LLM's forecasts before and
> after retrieval, associated with realized improvements in Brier score and
> log loss?**

For each question we elicit two probabilities from Claude Haiku 4.5 — the prior
p = P(H) (no retrieval) and the posterior q = P(H|E) (with date-bounded AskNews
evidence). From p and q we compute six belief-shift measures (Δ², KL
divergence, two uncertainty reductions, and the Crupi–Tentori and
Kemeny–Oppenheim confirmation measures), then correlate each one (Pearson and
Spearman) with the per-question improvement in Brier score and in log loss.

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
5. Score both forecasts against the resolved outcome y ∈ {0, 1} with the
   **Brier score** `(p − y)²` and the **log loss**
   `−[y·log p + (1 − y)·log(1 − p)]`. A question's **improvement** is
   score(p) − score(q), so positive means retrieval helped. For log loss and
   the log-based measures below, probabilities are clipped to
   `[1e-6, 1 − 1e-6]` so a forecast of exactly 0 or 1 gives a finite value.
6. Compute six **belief-shift measures** from p and q, with Δ = q − p. The
   first four are expected score improvements under a stated assumption; the
   last two are Bayesian confirmation measures.

   | key | formula | why |
   | --- | --- | --- |
   | `delta_sq` | Δ² | If the true probability is t = p + λΔ, the expected Brier improvement is (2λ − 1)·Δ², a positive multiple of Δ² when λ > ½. |
   | `kl` | KL(q‖p) = q·log(q/p) + (1 − q)·log((1 − q)/(1 − p)) | If the true probability is q (λ = 1), this is the expected log-loss improvement. |
   | `ur_brier` | (q − p)(p + q − 1) | E_p[Brier(p)] − E_q[Brier(q)] = p(1 − p) − q(1 − q): the drop in each forecast's own expected Brier score. Signed. |
   | `ur_log` | H(p) − H(q), with H(r) = −r·log r − (1 − r)·log(1 − r) | E_p[LogLoss(p)] − E_q[LogLoss(q)]: the drop in entropy. Signed. |
   | `abs_z` | \|Z\|, with Z = Δ/(1 − p) if q ≥ p, else Δ/p | Crupi–Tentori confirmation. |
   | `abs_ko` | \|Δ/(p + q − 2pq)\| | Kemeny–Oppenheim confirmation (P(E\|H) − P(E\|¬H))/(P(E\|H) + P(E\|¬H)), rewritten in p and q with Bayes' rule. |

7. For each of the 6 × 2 (measure, improvement) pairs, report the **Pearson**
   and **Spearman** correlations with 95% **bootstrap confidence intervals**,
   plus bootstrap CIs for the mean Brier and log-loss improvements. A
   bootstrap CI resamples the questions with replacement 10,000 times,
   recomputes the statistic each time, and keeps the middle 95% of those
   values. Pearson tracks how the *mean* improvement moves with a measure,
   which is what a scoring rule averages; Spearman uses only ranks, so it
   follows the typical question rather than the mean. Both p-values are also
   reported, but the Pearson p-value assumes normally distributed data, and a
   per-question improvement is far from normal, so read the bootstrap CI.

## Results

**The current run does not support the original hypothesis** that |Z| is
positively associated with the Brier improvement: their Spearman correlation
is essentially zero (rho = 0.05, p = 0.64). Retrieval still
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

### Exploratory: six measures × two scores

These come from the same 100-question run and are **exploratory**. The extra
measures, log loss and Pearson were added after the |Z| test above came out
null; the grid holds 24 correlations with no correction for multiple
comparisons; and several measures nearly duplicate each other (on this run,
Δ² and KL rank-correlate at 0.95, and UR_Brier and UR_log at 0.99).

Retrieval lowered the mean log loss from 0.537 to 0.477 (improvement +0.059,
95% CI −0.015 to +0.146). As with Brier, the mean improved, but the CI
includes zero.

Each cell is the correlation with its 95% bootstrap CI (n = 100):

| measure | Pearson r, Brier | Pearson r, log loss | Spearman rho, Brier | Spearman rho, log loss |
| --- | --- | --- | --- | --- |
| Δ² | 0.82 (0.51 to 0.92) | 0.86 (0.55 to 0.94) | −0.07 (−0.33 to 0.19) | −0.08 (−0.35 to 0.19) |
| KL(q‖p) | 0.82 (0.52 to 0.92) | 0.86 (0.56 to 0.95) | −0.05 (−0.30 to 0.20) | −0.07 (−0.33 to 0.19) |
| UR_Brier | 0.40 (0.16 to 0.62) | 0.42 (0.18 to 0.67) | 0.43 (0.21 to 0.62) | 0.49 (0.28 to 0.68) |
| UR_log | 0.39 (0.16 to 0.60) | 0.41 (0.18 to 0.66) | 0.42 (0.20 to 0.60) | 0.48 (0.27 to 0.66) |
| \|Z\| | 0.54 (0.26 to 0.72) | 0.58 (0.34 to 0.74) | 0.05 (−0.22 to 0.28) | 0.05 (−0.22 to 0.30) |
| \|KO\| | 0.48 (0.20 to 0.65) | 0.50 (0.24 to 0.66) | 0.04 (−0.19 to 0.25) | 0.01 (−0.22 to 0.24) |

- **Pearson and Spearman disagree for the size-of-move measures** (Δ², KL,
  |Z|, |KO|). Pearson is clearly positive, Spearman is about zero. The Pearson
  values rest on a few questions: the five largest moves all went toward the
  outcome and together add up to 135% of the net Brier improvement. Dropping
  those five lowers Pearson r for Δ² vs Brier from 0.82 to 0.17, and dropping
  the ten largest gives −0.14 (a one-off check, not in the summary JSON).
- **The uncertainty reductions are the only measures where both correlations
  are positive** with CIs above zero. Algebraically, the realized Brier
  improvement equals Δ·(2y − 1) − UR_Brier, so this says that moving away from
  ½ tended to go with moving toward the outcome. That pattern comes almost
  entirely from the 69 questions that resolved NO (Spearman 0.72 there,
  against 0.05 among the 31 that resolved YES), where most forecasts were
  below ½ and becoming more certain meant moving toward 0.

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
compute them, to `run_<timestamp>_summary.json`. It computes log loss and the
six measures from the CSV's `p_h`, `p_he` and `outcome` columns, so it works on
any existing run CSV. The correlation grid is under
`correlations[<improvement>][<measure>][pearson|spearman]`, each with
`estimate`, `p_value` and `ci`.

## Project layout

```
src/rag_forecast/
  config.py        — Config dataclass (model, paths, dates, rate limits)
  data.py          — ForecastBench fetch, join, binary filter, template fill
  retrieval.py     — date-bounded, cached AskNews wrapper
  forecasting.py   — rate-limited Anthropic client, strict-JSON parse, cached
  rate_limiter.py  — async sliding-window RPM/ITPM/OTPM limiter
  prompts.py       — prior/posterior elicitation prompts
  metrics.py       — brier, log_loss, shift_measures, z_crupi_tentori,
                     pearson, spearman, bootstrap_ci
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

Covers the Brier, log-loss and Crupi–Tentori Z formulas, each belief-shift
measure against its definition, Pearson and Spearman edge cases, bootstrap
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
