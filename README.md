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
   resamples, seed 0) that resample **families**, not single questions: the
   dataset questions (acled, dbnomics, fred, wikipedia, yfinance) that share a
   source and resolution day form one family, because one event, such as one
   week's stock market or one day's weather, decides them together; each market
   question is its own family.
8. **SQ2:** use the questions whose forecast moved (Δ ≠ 0). For each measure,
   rank questions within their own source, cut each source into 4 groups, and
   pool group g across sources, so every group has the same source mix. Per
   group: *achieved* = mean improvement (A); **λ̂** = ΣΔ(y − p)/ΣΔ², the single
   scale c that makes p + cΔ score best under Brier, and **c\***, the same
   under log loss (B: 1 = right size, < 1 too large, > 1 too small); *share* =
   achieved ÷ the gain at that best scale (shown when achieved > 0). λ̂ is also
   given per source, without a CI (a dataset source on one date is a single
   family). The groups are rebuilt in each resample.
9. **SQ3:** hold out one source at a time. Using only the other sources, mark
   group g "keep p" if its mean improvement is below 0, and apply the marks to
   the held-out source. **D** = mean over tested questions of score(always q)
   − score(rule), so D > 0 means the rule wins. The CI reruns the whole
   procedure on each resample.

## Pilot results

100 of the 348 questions (random, seed 0, 8 sources): `data/results/run_20260914T104832Z.csv`
and its `_summary.json`. 81 forecasts moved. **Exploratory:** the pilot's
original test was the Spearman correlation of |Z| with Brier improvement.
Changing only the prompts (same questions, evidence and model) moved it from
0.21 to 0.05, and the other five measures, log loss, Pearson, SQ2 and SQ3 were
all added after that. Mean Brier went from
0.187 to 0.165 (improvement +0.022 [−0.005, +0.071]) and log loss from 0.537
to 0.477 (+0.059 [−0.006, +0.177]); q beat p on 31 of the 100 questions.
Cells are estimate [95% CI].

**SQ1: correlation of each measure with the improvement**

| measure | Brier: Pearson | Brier: Spearman | log loss: Pearson | log loss: Spearman |
| --- | --- | --- | --- | --- |
| Δ² | +0.82 [+0.56, +0.92] | −0.07 [−0.31, +0.34] | +0.86 [+0.60, +0.93] | −0.08 [−0.33, +0.33] |
| KL | +0.82 [+0.56, +0.91] | −0.05 [−0.28, +0.37] | +0.86 [+0.60, +0.94] | −0.07 [−0.31, +0.37] |
| UR_B | +0.40 [+0.17, +0.61] | +0.43 [+0.07, +0.77] | +0.42 [+0.20, +0.66] | +0.49 [+0.14, +0.80] |
| UR_L | +0.39 [+0.16, +0.60] | +0.42 [+0.07, +0.73] | +0.41 [+0.21, +0.65] | +0.48 [+0.15, +0.77] |
| \|Z\| | +0.54 [+0.29, +0.71] | +0.05 [−0.20, +0.44] | +0.58 [+0.37, +0.74] | +0.05 [−0.20, +0.45] |
| \|KO\| | +0.48 [+0.26, +0.68] | +0.04 [−0.16, +0.42] | +0.50 [+0.30, +0.69] | +0.01 [−0.20, +0.41] |

The size measures' high Pearson rests on about five large moves, and their
Spearman is near 0. The uncertainty reductions are positive on both, almost
entirely through questions that resolved NO.

**SQ2: warrant in each measure's lowest and top within-source group** (of 4)

| measure | group | n | Brier achieved | λ̂ | log-loss achieved | c\* | share (Brier / log) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Δ² | lowest | 20 | −0.002 [−0.015, +0.005] | −1.02 [−8.91, +5.14] | −0.017 [−0.046, +0.007] | −0.67 [−1.14, +2.00] | — / — |
| Δ² | top | 23 | +0.102 [−0.016, +0.255] | +0.85 [+0.41, +1.14] | +0.283 [−0.002, +0.635] | +1.02 [+0.41, +1.10] | 97% / 100% |
| KL | lowest | 15 | −0.002 [−0.023, +0.009] | −0.99 [−9.51, +8.90] | −0.012 [−0.062, +0.014] | −0.67 [−1.50, +2.00] | — / — |
| KL | top | 23 | +0.109 [−0.001, +0.272] | +0.87 [+0.50, +1.17] | +0.298 [+0.036, +0.685] | +1.02 [+0.54, +1.10] | 98% / 100% |
| UR_B | lowest | 17 | −0.033 [−0.095, +0.056] | −0.36 [−1.28, +2.38] | −0.083 [−0.223, +0.148] | −0.20 [−0.68, +1.86] | — / — |
| UR_B | top | 25 | +0.085 [−0.000, +0.217] | +0.96 [+0.49, +1.16] | +0.245 [+0.034, +0.566] | +1.01 [+0.74, +1.03] | 100% / 99% |
| UR_L | lowest | 16 | +0.006 [−0.062, +0.072] | +0.89 [−1.58, +3.13] | −0.005 [−0.157, +0.185] | +0.35 [−0.50, +3.33] | 98% / — |
| UR_L | top | 25 | +0.084 [−0.000, +0.209] | +0.96 [+0.50, +1.14] | +0.243 [+0.033, +0.549] | +1.01 [+0.75, +1.03] | 100% / 99% |
| \|Z\| | lowest | 18 | −0.005 [−0.022, +0.014] | −1.69 [−7.34, +3.97] | −0.025 [−0.068, +0.028] | −0.67 [−1.00, +2.42] | — / — |
| \|Z\| | top | 24 | +0.094 [−0.006, +0.220] | +0.87 [+0.43, +1.11] | +0.277 [+0.026, +0.569] | +1.01 [+0.57, +1.03] | 98% / 100% |
| \|KO\| | lowest | 17 | −0.012 [−0.038, +0.004] | −1.27 [−6.02, +1.41] | −0.032 [−0.090, +0.006] | −1.50 [−2.00, +1.06] | — / — |
| \|KO\| | top | 24 | +0.131 [+0.008, +0.241] | +1.02 [+0.57, +1.17] | +0.340 [+0.042, +0.608] | +1.01 [+0.67, +1.03] | 100% / 99% |

Every measure's top group was about the right size (λ̂ 0.85–1.02, c\* 1.01–1.02)
and captured 97–100% of the available improvement. The lowest groups'
intervals are too wide to tell whether smaller moves were less justified.
Groups 2 and 3 are in the summary JSON. λ̂ also differs by source, from −1.33
for acled to +1.04 for polymarket (all sources are in the summary JSON), which
is why groups are formed within sources.

**SQ3: keep-p rule vs always q, one source held out at a time** (D > 0 = rule wins)

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | +0.000 [−0.033, +0.011] | +0.004 [−0.073, +0.031] | 1, 2 / 1, 2 |
| KL | +0.001 [−0.030, +0.016] | +0.006 [−0.065, +0.042] | 1, 2 / 1, 2 |
| UR_B | +0.007 [−0.042, +0.024] | +0.030 [−0.094, +0.064] | 1, 2 / 1, 2 |
| UR_L | +0.010 [−0.041, +0.025] | +0.022 [−0.093, +0.063] | 2 / 1, 2 |
| \|Z\| | −0.001 [−0.039, +0.019] | +0.003 [−0.082, +0.052] | 1, 2 / 1, 2 |
| \|KO\| | +0.011 [−0.036, +0.023] | +0.021 [−0.085, +0.056] | 1, 2, 3 / 1, 2, 3 |

No rule is distinguishable from always using q.

**Limits:**
- **One forecast date.** Every forecast was made as of 2025-10-16, and the 67
  questions from the five dataset sources all resolved on 2025-11-02, each
  source decided by one shared event (in the pilot, 12 of 13 dbnomics stations
  warmed against a forecast near 0.37, and only 2 of 11 yfinance stocks rose
  against about 0.51). This has two consequences. The CIs, which resample
  families, see only 5 such shared events (5 dataset families among 38), so
  how much they vary is estimated from very few draws. And holding out a source
  (SQ3) tests whether a rule carries over to a new source, not to another
  period with different shared events. More forecast dates would address both.
- **Same-event market questions** (e.g. three Spotify top-artist questions) are
  still treated as separate families; there are only a few such groups.

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
  `published_date` can't be verified as pre-freeze. Rerun on 2026-10-18 over the
  927 cached articles for the pilot's 100 questions (the other 248 have no
  cached evidence yet), it found none published after freeze and none with
  unverifiable dates (`data/results/leakage_20261018T135507Z.json`).
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
