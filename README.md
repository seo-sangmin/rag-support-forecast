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

## Status

So far one pilot run covers 100 of the 348 questions, sampled at random
(seed 0) across 8 sources: `data/results/run_20260914T104832Z.csv` (the last of
four resume-chained batches, so it holds all 100), with its `_summary.json`
(every statistic from Method step 7) and `.meta.json`. The other 248 questions
have not been run yet. The pilot's numbers are exploratory, because the six
measures, log loss and Pearson were added after the pilot's original test
(Spearman of |Z| vs Brier improvement) came out null. Notes from the pilot:

- Changing only the prompts, with the same questions, evidence and model,
  moved that original test's Spearman rho from 0.21 to 0.05.
- The size-of-move measures (Δ², KL, |Z|, |KO|) have high Pearson but
  near-zero Spearman correlations with improvement. The Pearson values rest on
  about five large moves that all went toward the outcome.
- The uncertainty reductions correlate positively on both statistics, but
  almost entirely through the questions that resolved NO.

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

`analyze_results.py` writes the aggregate statistics, including the
bootstrap CIs and the settings used to compute them, to
`run_<timestamp>_summary.json`. It computes log loss and the
six measures from the CSV's `p_h`, `p_he` and `outcome` columns, so it works on
any existing run CSV. The correlation grid is under
`correlations[<improvement>][<measure>][pearson|spearman]`, each with
`estimate`, `p_value` and `ci`.

`data/archive/` holds the July 2026 runs made with the earlier prompts (result
CSVs, summaries and leakage audits) and their prompt cache.

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
  `published_date` can't be verified as pre-freeze. On the pilot's 927 cached
  articles it found none published after freeze and none with unverifiable
  dates (`data/results/leakage_20260914T110031Z.json`).
- **Model cutoff**: `claude-haiku-4-5-20251001`'s Jul 2025 training cutoff
  precedes every question's `freeze_datetime` and AskNews search window, so
  neither the outcomes nor the retrieved evidence were in training.
- **Lookback**: 60 days before `freeze_datetime` — recent reporting without
  flooding the LLM with stale context.
- **Temperature 0**: maximizes reproducibility; relies on decode-time
  reasoning rather than ensembling samples.

## References

### Forecasting and scoring rules

- Karger, E., Bastani, H., Yueh-Han, C., Jacobs, Z., Halawi, D., Zhang, F., &
  Tetlock, P. E. (2025). ForecastBench: A dynamic benchmark of AI forecasting
  capabilities. *International Conference on Learning Representations
  (ICLR)*. <https://arxiv.org/abs/2409.19839> — the question sets (Method
  step 1).
- Brier, G. W. (1950). Verification of forecasts expressed in terms of
  probability. *Monthly Weather Review*, 78(1), 1–3.
  <https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2> — the
  Brier score.
- Good, I. J. (1952). Rational decisions. *Journal of the Royal Statistical
  Society: Series B*, 14(1), 107–114.
  <https://doi.org/10.1111/j.2517-6161.1952.tb00104.x> — the logarithmic
  score (log loss).
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules,
  prediction, and estimation. *Journal of the American Statistical
  Association*, 102(477), 359–378.
  <https://doi.org/10.1198/016214506000001437> — the entropy and divergence of
  a proper scoring rule, behind the expected-improvement measures (Method
  step 6).
- Kullback, S., & Leibler, R. A. (1951). On information and sufficiency.
  *Annals of Mathematical Statistics*, 22(1), 79–86.
  <https://doi.org/10.1214/aoms/1177729694> — KL divergence (`kl`).

### Confirmation measures

- Kemeny, J. G., & Oppenheim, P. (1952). Degree of factual support.
  *Philosophy of Science*, 19(4), 307–324. <https://doi.org/10.1086/287214> —
  the Kemeny–Oppenheim measure (`abs_ko`).
- Crupi, V., Tentori, K., & Gonzalez, M. (2007). On Bayesian measures of
  evidential support: Theoretical and empirical issues. *Philosophy of
  Science*, 74(2), 229–252. <https://doi.org/10.1086/520779> — the
  Crupi–Tentori measure Z (`abs_z`).
- Crupi, V., & Tentori, K. (2016). Confirmation theory. In A. Hájek & C.
  Hitchcock (Eds.), *The Oxford Handbook of Probability and Philosophy*
  (pp. 650–665). Oxford University Press.
  <https://doi.org/10.1093/oxfordhb/9780199607617.013.33>
  ([PDF](https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf))
  — survey of confirmation measures.
- Fitelson, B. (2021). A problem for confirmation measure Z. *Philosophy of
  Science*, 88(4), 726–730. <https://doi.org/10.1086/713920> — a critique of Z.

### Statistics

- Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *Annals
  of Statistics*, 7(1), 1–26. <https://doi.org/10.1214/aos/1176344552> — the
  bootstrap.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*.
  Chapman & Hall. <https://doi.org/10.1201/9780429246593> — Ch. 13, the
  percentile interval used for the CIs (Method step 7).

### Related work

- Tabet, A. N., & Luštrek, M. (2026). When does evidence help prompted LLM
  forecasting? Evidence access and prompt structure across 12 models.
  *ICML 2026 Workshop: Forecasting as a New Frontier of Intelligence*.
  <https://openreview.net/forum?id=YnNHhcgORk> — closed-book vs.
  AskNews-evidence forecasts on ForecastBench across 12 models.

### Data and software

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- AskNews Python SDK: <https://github.com/emergentmethods/asknews-python-sdk>
