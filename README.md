# rag-support-forecast

Retrieval-augmented forecasting can improve LLM forecasts, but it is unclear
when and why retrieved evidence helps. On binary questions from
[ForecastBench](https://www.forecastbench.org/), this repo asks:

> **Can measures of an LLM's belief shift, computed from its forecast before
> (p) and after (q) reading retrieved evidence, tell us when to trust the
> updated forecast?**

| sub-question | asks |
| --- | --- |
| **SQ1 Prediction** | How strongly is each measure associated with the realized Brier and log-loss improvement? |
| **SQ2 Warrant** | Within one source, are shifts with higher measure values better justified: (A) does q beat p, and (B) was the move the right size? |
| **SQ3 Decision** | On a source it has never seen, does "keep p in the measure groups where q did worse on the other sources" beat always using q? |

Why SQ2 and SQ3: with Δ = q − p and outcome y, a question's improvement is
(size of the move) × (λᵢ − break-even), where λᵢ = (y − p)/Δ is how justified
the move was (1 = right size, 0 = unsupported, < 0 = wrong way). The size is
2Δ² for Brier and Δ·Δlogit for log loss, so any measure that grows with move
size correlates with improvement (SQ1) even when big moves are no better
justified. SQ2 and SQ3 take the size out.

## Method

1. **Questions:** ForecastBench question and resolution sets dated
   **2025-10-26**, binary outcomes, one row per `(id, source)`: **348 questions**.
2. **Prior p:** `claude-haiku-4-5-20251001` at temperature 0, from the question,
   resolution criteria and background, with `freeze_datetime` as the
   forecast-as-of date.
3. **Evidence:** top 10 **AskNews** results from
   `[freeze_datetime − 60 days, freeze_datetime]`, so nothing after the freeze leaks in.
4. **Posterior q:** same model and date, with the evidence added.
5. **Scores:** Brier `(r − y)²` and log loss `−[y·log r + (1 − y)·log(1 − r)]`,
   with r clipped to `[1e-6, 1 − 1e-6]`. Improvement = score(p) − score(q).
6. **Measures** from p and q:

   | key | formula | meaning |
   | --- | --- | --- |
   | `delta_sq` | Δ² | expected Brier gain is (2λ − 1)·Δ² if the truth is p + λΔ |
   | `kl` | KL(q‖p) | expected log-loss gain if the truth is q |
   | `ur_brier` | p(1 − p) − q(1 − q) | drop in each forecast's own expected Brier score (signed) |
   | `ur_log` | H(p) − H(q) | drop in entropy (signed) |
   | `abs_z` | \|Z\|, Z = Δ/(1 − p) if q ≥ p, else Δ/p | Crupi–Tentori confirmation |
   | `abs_ko` | \|Δ/(p + q − 2pq)\| | Kemeny–Oppenheim confirmation |

7. **SQ1:** Pearson and Spearman correlation of each measure with each
   improvement. All CIs are 95% percentile bootstrap intervals (10,000
   resamples of the questions, seed 0).
8. **SQ2:** use the questions whose forecast moved (Δ ≠ 0). For each measure,
   rank questions within their own source, cut each source into 4 groups, and
   pool group g across sources, so every group has the same source mix. Per
   group: *achieved* = mean improvement (A); **λ̂** = ΣΔ(y − p)/ΣΔ², the single
   scale c that makes p + cΔ score best under Brier, and **c\***, the same
   under log loss (B: 1 = right size, < 1 too large, > 1 too small); *share* =
   achieved ÷ the gain at that best scale (shown when achieved > 0). λ̂ is also
   given per source. CIs resample within each source and regroup each time.
9. **SQ3:** hold out one source at a time. Using only the other sources, mark
   group g "keep p" if its mean improvement is below 0, and apply the marks to
   the held-out source. **D** = mean over tested questions of score(always q)
   − score(rule), so D > 0 means the rule wins. The CI reruns the whole
   procedure on each within-source resample.

## Pilot results

100 of the 348 questions (random, seed 0, 8 sources): `data/results/run_20260914T104832Z.csv`
and its `_summary.json`. 81 forecasts moved. **Exploratory:** five of the
measures, log loss, Pearson, SQ2 and SQ3 were all designed after the original
test (Spearman of |Z| vs Brier improvement) came out null. Mean Brier went from
0.187 to 0.165 (improvement +0.022 [−0.008, +0.057]) and log loss from 0.537
to 0.477 (+0.059 [−0.015, +0.146]); q beat p on 31 of the 100 questions.
Cells are estimate [95% CI].

**SQ1: correlation of each measure with the improvement**

| measure | Brier: Pearson | Brier: Spearman | log loss: Pearson | log loss: Spearman |
| --- | --- | --- | --- | --- |
| Δ² | +0.82 [+0.51, +0.92] | −0.07 [−0.33, +0.19] | +0.86 [+0.55, +0.94] | −0.08 [−0.35, +0.19] |
| KL | +0.82 [+0.52, +0.92] | −0.05 [−0.30, +0.20] | +0.86 [+0.56, +0.95] | −0.07 [−0.33, +0.19] |
| UR_B | +0.40 [+0.16, +0.62] | +0.43 [+0.21, +0.62] | +0.42 [+0.18, +0.67] | +0.49 [+0.28, +0.68] |
| UR_L | +0.39 [+0.16, +0.60] | +0.42 [+0.20, +0.60] | +0.41 [+0.18, +0.66] | +0.48 [+0.27, +0.66] |
| \|Z\| | +0.54 [+0.26, +0.72] | +0.05 [−0.22, +0.28] | +0.58 [+0.34, +0.74] | +0.05 [−0.22, +0.30] |
| \|KO\| | +0.48 [+0.20, +0.65] | +0.04 [−0.19, +0.25] | +0.50 [+0.24, +0.66] | +0.01 [−0.22, +0.24] |

The size measures' high Pearson rests on about five large moves, and their
Spearman is near 0. The uncertainty reductions are positive on both, almost
entirely through questions that resolved NO.

**SQ2: warrant in each measure's lowest and top within-source group** (of 4)

| measure | group | n | Brier achieved | λ̂ | log-loss achieved | c\* | share (Brier / log) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Δ² | lowest | 20 | −0.002 [−0.013, +0.003] | −1.02 [−7.19, +2.20] | −0.017 [−0.045, −0.001] | −0.67 [−1.00, −0.00] | — / — |
| Δ² | top | 23 | +0.102 [−0.024, +0.211] | +0.85 [+0.34, +1.08] | +0.283 [−0.029, +0.561] | +1.02 [+0.33, +1.10] | 97% / 100% |
| KL | lowest | 15 | −0.002 [−0.014, +0.006] | −0.99 [−4.60, +4.45] | −0.012 [−0.042, +0.007] | −0.67 [−1.14, +2.00] | — / — |
| KL | top | 23 | +0.109 [−0.005, +0.220] | +0.87 [+0.47, +1.13] | +0.298 [+0.016, +0.592] | +1.02 [+0.49, +1.10] | 98% / 100% |
| UR_B | lowest | 17 | −0.033 [−0.095, +0.032] | −0.36 [−1.37, +1.47] | −0.083 [−0.220, +0.093] | −0.20 [−0.68, +1.20] | — / — |
| UR_B | top | 25 | +0.085 [+0.002, +0.196] | +0.96 [+0.53, +1.18] | +0.245 [+0.036, +0.536] | +1.01 [+0.77, +1.03] | 100% / 99% |
| UR_L | lowest | 16 | +0.006 [−0.065, +0.054] | +0.89 [−1.58, +2.89] | −0.005 [−0.162, +0.131] | +0.35 [−0.36, +2.68] | 98% / — |
| UR_L | top | 25 | +0.084 [+0.001, +0.191] | +0.96 [+0.52, +1.17] | +0.243 [+0.035, +0.530] | +1.01 [+0.78, +1.03] | 100% / 99% |
| \|Z\| | lowest | 18 | −0.005 [−0.014, +0.013] | −1.69 [−4.36, +2.73] | −0.025 [−0.050, +0.026] | −0.67 [−1.00, +1.60] | — / — |
| \|Z\| | top | 24 | +0.094 [−0.013, +0.195] | +0.87 [+0.39, +1.08] | +0.277 [+0.006, +0.535] | +1.01 [+0.47, +1.03] | 98% / 100% |
| \|KO\| | lowest | 17 | −0.012 [−0.040, +0.008] | −1.27 [−3.03, +1.72] | −0.032 [−0.091, +0.014] | −1.50 [−2.00, +1.75] | — / — |
| \|KO\| | top | 24 | +0.131 [+0.001, +0.214] | +1.02 [+0.51, +1.18] | +0.340 [+0.021, +0.575] | +1.01 [+0.56, +1.03] | 100% / 99% |

Every measure's top group was about the right size (λ̂ 0.85–1.02, c\* 1.01–1.02)
and captured 97–100% of the available improvement. The lowest groups'
intervals are too wide to tell whether smaller moves were less justified.
Groups 2 and 3 are in the summary JSON.

**SQ2: λ̂ by source**

| source | n moved | λ̂ |
| --- | --- | --- |
| acled | 10 | −1.33 [−2.55, −0.31] |
| dbnomics | 9 | −3.20 [−8.65, +3.10] |
| fred | 13 | −0.34 [−3.08, +2.08] |
| manifold | 6 | +1.07 [+0.77, +1.26] |
| metaculus | 3 | +0.94 [−9.71, +1.67] |
| polymarket | 17 | +1.04 [+0.09, +1.71] |
| wikipedia | 16 | +0.68 [−1.47, +1.06] |
| yfinance | 7 | +5.50 [−8.27, +12.14] |

**SQ3: keep-p rule vs always q, one source held out at a time** (D > 0 = rule wins)

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | +0.000 [−0.035, +0.014] | +0.004 [−0.077, +0.036] | 1, 2 / 1, 2 |
| KL | +0.001 [−0.032, +0.018] | +0.006 [−0.067, +0.046] | 1, 2 / 1, 2 |
| UR_B | +0.007 [−0.035, +0.025] | +0.030 [−0.080, +0.062] | 1, 2 / 1, 2 |
| UR_L | +0.010 [−0.037, +0.024] | +0.022 [−0.083, +0.060] | 2 / 1, 2 |
| \|Z\| | −0.001 [−0.036, +0.020] | +0.003 [−0.080, +0.052] | 1, 2 / 1, 2 |
| \|KO\| | +0.011 [−0.032, +0.025] | +0.021 [−0.076, +0.058] | 1, 2, 3 / 1, 2, 3 |

No rule is distinguishable from always using q.

**Limits:** questions come in families resolved by one shared cause (48
yfinance stock questions for the same week, 49 dbnomics temperatures for the
same day, 50 fred rates), and all resolve within one week, so the CIs are too
narrow, and a result can only claim to carry over to another source in the
same week. Changing only the prompts moved the original test's Spearman rho
from 0.21 to 0.05.

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
python scripts/run_experiment.py --question-sets 2025-10-26 --max-questions 5  # smoke test; --help lists all flags
python scripts/analyze_results.py data/results/run_<timestamp>.csv  # writes run_<timestamp>_summary.json (~5 min)
python scripts/audit_leakage.py  # offline: flag cached evidence dated after each freeze
```

`run_experiment.py --random --seed N` samples questions, and `--resume-from
<csv>` adds questions to an earlier run; pass the latest CSV to the analysis.
LLM and AskNews calls are cached under `data/cache/`, so reruns are free. To
keep the pilot out of the SQ3 test when analyzing pilot + new questions, add
`--train-only data/results/run_20260914T104832Z.csv` to `analyze_results.py`.

## Outputs

- `run_<timestamp>.csv`: one row per question, including `id`, `source`,
  `outcome`, `p_h`, `p_he` and both forecasts' reasoning.
- `run_<timestamp>.meta.json`: seed, sampling flags, model and retrieval
  settings, the selected questions and any that failed.
- `run_<timestamp>_summary.json`: all results, under `correlations` (SQ1),
  `warrant` (SQ2), `decision` (SQ3) and `ci_method`.
- `data/archive/`: the July 2026 runs made with the earlier prompts.

## Project layout

```
src/rag_forecast/  data, retrieval, prompts, forecasting, pipeline, metrics, audit, cache, rate_limiter, config
scripts/           run_experiment.py, analyze_results.py, audit_leakage.py
tests/             run with `pytest -q`
```

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

Full citations for the scoring rules, confirmation measures, statistics and
related work are in [REFERENCES.md](REFERENCES.md).

- ForecastBench: <https://www.forecastbench.org/>
- ForecastBench datasets: <https://github.com/forecastingresearch/forecastbench-datasets>
- AskNews Python SDK: <https://github.com/emergentmethods/asknews-python-sdk>
