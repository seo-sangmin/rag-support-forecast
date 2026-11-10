# Analysis plan and pilot detail

The [README](README.md) gives the question, the draft hypothesis H and a
summary of the pilot. This file keeps the detail behind them: why H has its
form, the power checks, finer method points and the full pilot tables. Terms
are defined in the README, and step numbers refer to its
[Method](README.md#method).

## Hypothesis H

H was drafted after the pilot and before the exploration run, and is not
preregistered yet (see [Stages](README.md#stages)).

**Halves.** A measure's *top half* is its two highest of the 4 groups formed
within each source (Method step 8), and its *low half* is its two lowest. Each
half is pooled: λ̂ and c\* are computed over all its moves at once, so a half's
λ̂ is the average of its two groups' λ̂ weighted by their ΣΔ².

**Pass rule.** Each gap is checked in one direction at the 2.5% level, the
same bar the usual two sided 5% test sets for a positive result. So a gap
passes when its 95% bootstrap interval lies above 0. If either gap is really 0
or below, its check passes by luck at most 2.5% of the time, and H needs both
checks to pass. So the two scores need no correction.

**Six measures.** There is no correction for testing six measures, because
each measure's result answers its own question, so every conclusion is about
one measure. Each conclusion has a 2.5% chance of a lucky pass, and across the
six, the chance that at least one does is about 8 to 12% on the pilot. No test
compares the measures with each other (for example, whether |Z| picks better
moves than plain move size Δ²), so H's six results are not a ranking: one
measure passing and another failing does not show that the first is better.

**Why the gaps compare λ̂ and c\* themselves.** λ̂ is the average of λᵢ
weighted by Δ², and a group's total Brier improvement is ΣΔ² × (2λ̂ − 1), so a
higher λ̂ means more improvement for the same total move size. c\* plays the
same role for log loss. Whether the moves were the right size (λ̂ and c\* near
1) is reported as an estimate.

**Why halves.** A measure tells justified updates apart if the updates it
rates high are better justified than those it rates low, and the median is the
default line between high and low. On the pilot, λ̂ and c\* also drop between
groups 2 and 3 for five measures, while groups 3 and 4 look alike (see the
[SQ2 table](#sq2-warrant-by-group)). An earlier draft compared the top group
with the other three. If the pilot gaps were true, halves would raise H's
power on two test dates (earlier draft → halves) for Δ² (65% → 94%), UR_B
(50% → 98%) and UR_L (53% → 99%), keep KL (83% → 86%) and |Z| (39% → 40%)
about the same, and lower it for |KO| (100% → 48%), whose drop comes between
groups 3 and 4. The exploration run checks this choice again.

**Why only one hypothesis.** If q were right on average (the chance that
y = 1 equals q, whatever p and q are), every group would have λ = 1 and
c\* = 1. Then q would beat p in every group and overall, and every group's
moves would be the right size, yet both gaps would be 0. So only the gaps can
tell measures that pick out justified moves from measures that do not.

## Estimates without a pass rule

- **Baseline:** does q beat p over all questions?
- **SQ2 for each group:** *achieved*, λ̂ and c\* (does q beat p, and was the
  move the right size?).
- **SQ1 correlations**, because they mix move size with how justified the
  move was (see the README's key terms).
- **SQ3 D**, because even the best single set of "keep p" marks, chosen
  knowing the outcomes, would gain only 0.003 to 0.013 Brier per moved
  question on the pilot (depending on the measure). That is at or below the
  smallest D two test dates could detect (0.012 to 0.017).

## Test dates and power

Test dates (rough): 2 or more. On the pilot the λ̂ gaps are +1.21 to +2.43
and the c\* gaps +0.96 to +1.80, but every λ̂ gap's 95% interval includes 0, so
H would pass for no measure. The smallest gap that two test dates could detect
is about 0.7 to 1.5 for λ̂ and 0.5 to 2.3 for c\* (family bootstrap, standard
errors scaled to about 380 questions per date, one direction at 2.5%, 80%
power). For c\*, the standard error is taken from the middle half of the
bootstrap values, because the few resamples where a half's c\* reaches the
±50 cap (about 3% at most) inflate the usual one. All of this is redone after
the exploration run. `analyze_results.py` reports H under `hypothesis` in the
summary JSON: each half's λ̂ and c\*, both gaps, and each gap's 95% interval,
whose low end is the one direction check.

## Method detail

- **Matching measures (step 6).** Δ² ranks questions exactly like |q − p|,
  the size of the difference measure, and |KO| exactly like
  |logit q − logit p|, the size of the log likelihood ratio that p and q
  imply, since KO = tanh((logit q − logit p)/2). So each pair gives the same
  groups and the same SQ1 Spearman, SQ2, SQ3 and H results. Only SQ1's
  Pearson differs.
- **Families (step 7).** One event, such as one week's stock market or one
  day's weather, decides a dataset family together. The bootstrap uses seed 0.
- **λ̂ and c\* (step 8).** λ̂ = ΣΔ(y − p)/ΣΔ² is the single scale c that makes
  p + cΔ score best under Brier. c\* is the single scale c of each move in
  log odds, logit p + c·(logit q − logit p), that scores best under log loss.
  Scaling in log odds keeps every scaled forecast a probability, so c\* is
  never stopped at 0 or 1, but it measures size on a different scale than λ̂.
- **The c\* cap.** c\* is searched in [−50, 50]. > 50 means the best scale
  lies beyond that, as when every move in the group pointed toward its outcome
  (< −50: every move away). In the H check for |Z|, the low half reaches −50
  in about 3% of resamples, so the top end of its c\* gap interval (+50.67) is
  shown as > +50.
- **share** = achieved ÷ the gain at the best scale (shown when achieved > 0).
- **Per source.** λ̂ and c\* are also given per source, without a CI (a
  dataset source on one date is a single family).
- **Resampling.** The groups are rebuilt in each resample, and SQ3's CI reruns
  the whole procedure on each resample. SQ3's D is a mean over the tested
  questions.

## Design choices

- **Evidence cutoff:** the AskNews search window ends at each question's
  `freeze_datetime` (not the resolution date), so retrieval can't surface news
  that reveals the outcome. `scripts/audit_leakage.py` verifies this held for
  the cached evidence, offline, and fails closed on articles whose
  `published_date` can't be verified as pre-freeze. Rerun on 2026-10-18 over
  the 927 cached articles for the pilot's 100 questions (the other 248 have no
  cached evidence yet), it found none published after freeze and none with
  unverifiable dates (`data/results/leakage_20261018T135507Z.json`).
- **Model cutoff:** `claude-haiku-4-5-20251001`'s Jul 2025 training cutoff
  precedes every question's `freeze_datetime` and AskNews search window, so
  neither the outcomes nor the retrieved evidence were in training.
- **Lookback:** 60 days before `freeze_datetime`, for recent reporting without
  flooding the LLM with stale context.
- **Temperature 0:** maximizes reproducibility, and relies on decode time
  reasoning rather than ensembling samples.

## Pilot tables

100 of the 348 questions (random, seed 0, 8 sources):
`data/results/run_20260914T104832Z.csv` and its `_summary.json`. 81 forecasts
moved. Cells are estimate [95% CI].

### SQ1: correlation with the improvement

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

### SQ2: warrant by group

Each measure's 4 within source groups (1 = lowest, 4 = top).

| measure | group | n | Brier achieved | λ̂ | log-loss achieved | c\* | share (Brier / log) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Δ² | 1 | 20 | −0.002 [−0.015, +0.005] | −1.02 [−8.91, +5.14] | −0.017 [−0.046, +0.007] | −2.00 [< −50, +1.24] | — / — |
| Δ² | 2 | 19 | −0.010 [−0.027, +0.037] | −0.98 [−3.40, +2.08] | −0.039 [−0.078, +0.094] | −0.07 [−9.89, +1.42] | — / — |
| Δ² | 3 | 19 | +0.005 [−0.040, +0.137] | +0.70 [−0.98, +2.31] | +0.028 [−0.086, +0.345] | +0.82 [−0.54, +2.58] | 81% / 96% |
| Δ² | 4 | 23 | +0.102 [−0.016, +0.255] | +0.85 [+0.41, +1.14] | +0.283 [−0.002, +0.635] | +0.81 [+0.46, +1.47] | 97% / 97% |
| KL | 1 | 15 | −0.002 [−0.023, +0.009] | −0.99 [−9.51, +8.90] | −0.012 [−0.062, +0.014] | −1.53 [< −50, +2.38] | — / — |
| KL | 2 | 23 | −0.021 [−0.046, +0.019] | −1.61 [−3.47, +1.19] | −0.059 [−0.110, +0.048] | −0.25 [−10.84, +0.96] | — / — |
| KL | 3 | 20 | +0.012 [−0.045, +0.135] | +1.05 [−1.36, +2.38] | +0.031 [−0.106, +0.333] | +0.86 [−1.18, +2.69] | 100% / 97% |
| KL | 4 | 23 | +0.109 [−0.001, +0.272] | +0.87 [+0.50, +1.17] | +0.298 [+0.036, +0.685] | +0.84 [+0.53, +1.64] | 98% / 98% |
| UR_B | 1 | 17 | −0.033 [−0.095, +0.056] | −0.36 [−1.28, +2.38] | −0.083 [−0.223, +0.148] | −0.49 [< −50, +1.63] | — / — |
| UR_B | 2 | 22 | −0.015 [−0.063, +0.077] | −0.48 [−2.21, +1.91] | −0.046 [−0.148, +0.182] | −0.89 [−7.88, +1.35] | — / — |
| UR_B | 3 | 17 | +0.058 [−0.037, +0.220] | +1.04 [−3.68, +1.75] | +0.131 [−0.085, +0.520] | +1.00 [−10.23, +2.62] | 100% / 100% |
| UR_B | 4 | 25 | +0.085 [−0.000, +0.217] | +0.96 [+0.49, +1.16] | +0.245 [+0.034, +0.566] | +1.01 [+0.54, +1.97] | 100% / 100% |
| UR_L | 1 | 16 | +0.006 [−0.062, +0.072] | +0.89 [−1.58, +3.13] | −0.005 [−0.157, +0.185] | +0.45 [< −50, +1.81] | 98% / — |
| UR_L | 2 | 22 | −0.047 [−0.102, +0.062] | −0.93 [−1.76, +1.18] | −0.112 [−0.230, +0.153] | −3.07 [−9.98, +1.17] | — / — |
| UR_L | 3 | 18 | +0.058 [−0.029, +0.217] | +1.07 [−2.75, +1.72] | +0.133 [−0.069, +0.513] | +1.06 [−4.90, +2.68] | 100% / 100% |
| UR_L | 4 | 25 | +0.084 [−0.000, +0.209] | +0.96 [+0.50, +1.14] | +0.243 [+0.033, +0.549] | +1.01 [+0.53, +1.97] | 100% / 100% |
| \|Z\| | 1 | 18 | −0.005 [−0.022, +0.014] | −1.69 [−7.34, +3.97] | −0.025 [−0.068, +0.028] | −4.88 [< −50, +1.39] | — / — |
| \|Z\| | 2 | 20 | −0.009 [−0.069, +0.059] | −0.17 [−3.04, +2.63] | −0.031 [−0.159, +0.146] | −0.20 [< −50, +1.71] | — / — |
| \|Z\| | 3 | 19 | +0.012 [−0.064, +0.187] | +0.71 [−1.11, +1.76] | +0.019 [−0.142, +0.434] | +0.65 [−2.06, +2.64] | 84% / 71% |
| \|Z\| | 4 | 24 | +0.094 [−0.006, +0.220] | +0.87 [+0.43, +1.11] | +0.277 [+0.026, +0.569] | +0.85 [+0.49, +1.58] | 98% / 99% |
| \|KO\| | 1 | 17 | −0.012 [−0.038, +0.004] | −1.27 [−6.02, +1.41] | −0.032 [−0.090, +0.006] | −1.50 [< −50, +0.82] | — / — |
| \|KO\| | 2 | 19 | −0.013 [−0.061, +0.065] | −0.14 [−3.19, +2.34] | −0.026 [−0.143, +0.168] | +0.02 [−14.22, +2.15] | — / — |
| \|KO\| | 3 | 21 | −0.022 [−0.065, +0.164] | −0.00 [−0.97, +1.97] | −0.057 [−0.149, +0.391] | −0.01 [−1.96, +2.25] | — / — |
| \|KO\| | 4 | 24 | +0.131 [+0.008, +0.241] | +1.02 [+0.57, +1.17] | +0.340 [+0.042, +0.608] | +1.05 [+0.53, +1.59] | 100% / 100% |

Every measure's top group (4) was about the right size (λ̂ 0.85 to 1.02, c\*
0.81 to 1.05) and captured 97 to 100% of the available improvement under both
scores. For five measures, group 3 looks like group 4 (λ̂ 0.70 to 1.07, c\*
0.65 to 1.06), and λ̂ and c\* drop between groups 2 and 3. |KO| is the
exception: its group 3 has λ̂ and c\* near 0. Groups 1 and 2 hold only 2 to
13% of the movement (ΣΔ²), so their intervals are too wide to tell how
justified those moves were. Every group 1 c\* interval reaches the −50 cap,
and so does |Z|'s group 2, because some resamples keep only moves that pointed
away from their outcome. λ̂ and c\* also differ by source, for example −1.33
and −1.05 for acled but +1.04 and +1.04 for polymarket (all sources are in the
summary JSON), which is why groups are formed within sources.

### SQ3: keep-p rule vs always q

One source held out at a time (D > 0 = rule wins).

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | +0.000 [−0.033, +0.011] | +0.004 [−0.073, +0.031] | 1, 2 / 1, 2 |
| KL | +0.001 [−0.030, +0.016] | +0.006 [−0.065, +0.042] | 1, 2 / 1, 2 |
| UR_B | +0.007 [−0.042, +0.024] | +0.030 [−0.094, +0.064] | 1, 2 / 1, 2 |
| UR_L | +0.010 [−0.041, +0.025] | +0.022 [−0.093, +0.063] | 2 / 1, 2 |
| \|Z\| | −0.001 [−0.039, +0.019] | +0.003 [−0.082, +0.052] | 1, 2 / 1, 2 |
| \|KO\| | +0.011 [−0.036, +0.023] | +0.021 [−0.085, +0.056] | 1, 2, 3 / 1, 2, 3 |

No rule is distinguishable from always using q.

## Limits

- **One forecast date.** Every forecast was made as of 2025-10-16, and the 67
  questions from the five dataset sources all resolved on 2025-11-02, each
  source decided by one shared event (in the pilot, 12 of 13 dbnomics stations
  warmed against a forecast near 0.37, and only 2 of 11 yfinance stocks rose
  against about 0.51). This has two consequences. The CIs, which resample
  families, see only 5 such shared events (5 dataset families among 38), so
  how much they vary is estimated from very few draws. And holding out a
  source (SQ3) tests whether a rule carries over to a new source, not to
  another period with different shared events. More forecast dates would
  address both.
- **Same-event market questions** (e.g. three Spotify top-artist questions)
  are still treated as separate families. There are only a few such groups.
