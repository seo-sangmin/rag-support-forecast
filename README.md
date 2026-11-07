# rag-support-forecast

Retrieval-augmented forecasting can improve LLM forecasts, but it is unclear
when and why retrieved evidence helps. On binary questions from
[ForecastBench](https://www.forecastbench.org/), this repo asks:

> **Can measures of an LLM's belief shift, computed from its forecast before
> (p) and after (q) reading retrieved evidence, tell us when to trust the
> updated forecast?**

Here "when to trust" means which moves (p to q) are justified, so SQ2 carries
the main question. SQ3 asks whether acting on the answer improves scores on a
source the rule has not seen.

| sub-question | asks | answered by |
| --- | --- | --- |
| **SQ1 Prediction** | How strongly is each measure associated with the realized Brier and log-loss improvement? | estimates only |
| **SQ2 Warrant** | Within one source, are shifts with higher measure values better justified: (A) does q beat p, and (B) was the move the right size? | H1 (A), H2 (B), H4 |
| **SQ3 Decision** | On a source it has never seen, does "keep p in the measure groups where q did worse on the other sources" beat always using q? | estimate only |

Why SQ2 and SQ3: with Δ = q − p and outcome y, a question's improvement is
(size of the move) × (λᵢ − break-even), where λᵢ = (y − p)/Δ is how justified
the move was (1 = right size, 0 = unsupported, < 0 = wrong way). The size is
2Δ² for Brier and Δ·Δlogit for log loss, so any measure that grows with move
size correlates with improvement (SQ1) even when big moves are no better
justified. SQ2 and SQ3 take the size out.

## Hypotheses (draft)

Drafted after the pilot and before the exploration run, and not preregistered
yet (see [Stages](#stages)). A measure's *top group* is its highest of the 4
groups formed within each source (Method step 8), and *the rest* is its other
three groups pooled. H1, H2 and H4 are tested for each of the six measures.
Each test checks one direction at the 5% level, except H2, which is an
equivalence test.

| | claim | answers | pass rule | test dates (rough) |
| --- | --- | --- | --- | --- |
| **H1** | In each top group, q beats p. | SQ2 (A) | *achieved* > 0 under Brier and under log loss | 1 |
| **H2** | Top group moves are about the right size. | SQ2 (B) | λ̂ and c\* inside a band around 1, for example 0.7 to 1.3 | 2 or more |
| **H3** | Over all questions, q beats p. | baseline | mean improvement > 0 under Brier and under log loss | 2 |
| **H4** | Top group moves are better justified than the rest. | main question (SQ2) | λ̂(top) − λ̂(rest) > 0 | 2 or more |

H4 compares λ̂ itself, not its distance to 1, which is H2's question. λ̂ is the
average of λᵢ weighted by Δ², and a group's total Brier improvement is
ΣΔ² × (2λ̂ − 1), so a higher λ̂ means more improvement for the same total move
size. If q were right on average (the chance that y = 1 equals q, whatever p
and q are), every group would have λ = 1, so with enough data H1 to H3 would
pass and H4's gap would be 0. A passing H4 therefore shows what H1 to H3
cannot: the measures separate more justified moves from less justified ones.

Reported as estimates with intervals, without a pass rule:
- **SQ1 correlations**, because they mix move size with how justified the move
  was (see above).
- **SQ3 D**, because even the best single set of "keep p" marks, chosen knowing
  the outcomes, would gain only 0.003 to 0.013 Brier per moved question on the
  pilot (depending on the measure). That is at or below the smallest D two test
  dates could detect (0.011 to 0.015).
- **|Z| and |KO| vs Δ²** (do the confirmation measures pick better moves than
  move size?), because their top groups share most questions with Δ²'s (19 and
  16 of 24 on the pilot), so the comparison rests on the few questions where
  they differ.

The test dates come from a rough pilot check (family bootstrap, standard errors
scaled to about 380 questions per date, 80% power) and are redone after the
exploration run. Still open: H2's band, how to correct for testing six measures
under two scores, and H4 under log loss (c\* in place of λ̂, not yet checked).
`analyze_results.py` does not compute H4 yet.

## Stages

1. **Pilot** (done): 100 of the 348 questions, exploratory. Its results shaped
   the hypotheses, so it cannot test them.
2. **Exploration run**: questions from another ForecastBench date, with their
   outcomes looked at. It checks whether the pilot patterns hold and supplies
   the numbers for the power check.
3. **Preregistration**: fixes the hypotheses, pass rules and number of test
   dates before any test outcome is seen.
4. **Test run**: as many new dates as the power check calls for, analyzed once
   as preregistered.

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
   scale c that makes p + cΔ score best under Brier, and **c\***, the single
   scale c of each move in log odds, logit p + c·(logit q − logit p), that
   scores best under log loss (B: 1 = right size, < 1 too large, > 1 too
   small). Scaling in log odds keeps every scaled forecast a probability, so
   c\* is never stopped at 0 or 1, but it measures size on a different scale
   than λ̂. c\* is searched in [−50, 50]. > 50 means the best scale lies beyond
   that, as when every move in the group pointed toward its outcome (< −50:
   every move away). *share* = achieved ÷ the gain at that best scale (shown
   when achieved > 0). λ̂ and c\* are also
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
| Δ² | lowest | 20 | −0.002 [−0.015, +0.005] | −1.02 [−8.91, +5.14] | −0.017 [−0.046, +0.007] | −2.00 [< −50, +1.24] | — / — |
| Δ² | top | 23 | +0.102 [−0.016, +0.255] | +0.85 [+0.41, +1.14] | +0.283 [−0.002, +0.635] | +0.81 [+0.46, +1.47] | 97% / 97% |
| KL | lowest | 15 | −0.002 [−0.023, +0.009] | −0.99 [−9.51, +8.90] | −0.012 [−0.062, +0.014] | −1.53 [< −50, +2.38] | — / — |
| KL | top | 23 | +0.109 [−0.001, +0.272] | +0.87 [+0.50, +1.17] | +0.298 [+0.036, +0.685] | +0.84 [+0.53, +1.64] | 98% / 98% |
| UR_B | lowest | 17 | −0.033 [−0.095, +0.056] | −0.36 [−1.28, +2.38] | −0.083 [−0.223, +0.148] | −0.49 [< −50, +1.63] | — / — |
| UR_B | top | 25 | +0.085 [−0.000, +0.217] | +0.96 [+0.49, +1.16] | +0.245 [+0.034, +0.566] | +1.01 [+0.54, +1.97] | 100% / 100% |
| UR_L | lowest | 16 | +0.006 [−0.062, +0.072] | +0.89 [−1.58, +3.13] | −0.005 [−0.157, +0.185] | +0.45 [< −50, +1.81] | 98% / — |
| UR_L | top | 25 | +0.084 [−0.000, +0.209] | +0.96 [+0.50, +1.14] | +0.243 [+0.033, +0.549] | +1.01 [+0.53, +1.97] | 100% / 100% |
| \|Z\| | lowest | 18 | −0.005 [−0.022, +0.014] | −1.69 [−7.34, +3.97] | −0.025 [−0.068, +0.028] | −4.88 [< −50, +1.39] | — / — |
| \|Z\| | top | 24 | +0.094 [−0.006, +0.220] | +0.87 [+0.43, +1.11] | +0.277 [+0.026, +0.569] | +0.85 [+0.49, +1.58] | 98% / 99% |
| \|KO\| | lowest | 17 | −0.012 [−0.038, +0.004] | −1.27 [−6.02, +1.41] | −0.032 [−0.090, +0.006] | −1.50 [< −50, +0.82] | — / — |
| \|KO\| | top | 24 | +0.131 [+0.008, +0.241] | +1.02 [+0.57, +1.17] | +0.340 [+0.042, +0.608] | +1.05 [+0.53, +1.59] | 100% / 100% |

Every measure's top group was about the right size (λ̂ 0.85 to 1.02, c\* 0.81
to 1.05) and captured 97 to 100% of the available improvement under both
scores. The lowest groups' intervals are too wide to tell whether smaller moves
were less justified. Each lowest group's c\* interval reaches the −50 cap,
because some resamples keep only moves that pointed away from their outcome.
Groups 2 and 3 are in the summary JSON. λ̂ and c\* also differ by source, for
example −1.33 and −1.05 for acled but +1.04 and +1.04 for polymarket (all
sources are in the summary JSON), which is why groups are formed within
sources.

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
