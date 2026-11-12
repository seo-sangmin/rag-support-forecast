# Reasons for H, method detail and pilot tables

The [README](README.md) gives the question, the draft hypothesis H and a
summary of the pilot. This file gives the detail behind them, in three parts:

1. [Hypothesis H](#hypothesis-h): what H tests, why it has this form, how the
   six measures are handled, power, and what is only estimated.
2. [Method detail](#method-detail-by-readme-step): finer points of the
   README's [Method](README.md#method) steps, in step order.
3. [Pilot results](#pilot-results): the full tables and the limits.

Terms such as λᵢ, λ̂ and c\* are defined in the README's key terms.

## Hypothesis H

H was drafted after the pilot and before the exploration run, and is not
preregistered yet (see [Stages](README.md#stages)).

### What H tests

**Halves.** For each measure, the moved questions are cut into 4 groups
within each source ([Method](README.md#method) step 8). The *top half* is
groups 3 and 4, and the *low half* is groups 1 and 2. Each half is pooled:
λ̂ and c\* are computed over all its moves at once. So a half's λ̂ is the
average of its two groups' λ̂, weighted by their ΣΔ².

**Gaps and pass rule.** H takes two gaps, each the top half minus the low
half: one for λ̂ (Brier) and one for c\* (log loss). Each gap is checked like
this:

1. The family bootstrap gives a 95% interval for the gap. Only 2.5% of the
   bootstrap gaps fall below the interval's low end.
2. The gap passes when that low end is above 0. This is a check in one
   direction at the 2.5% level, the same bar the usual two sided 5% test sets
   for a positive result.
3. H passes for a measure only when both of its gaps pass.

**Why the two scores need no correction.** Suppose one of the two true gaps
is 0 or below. Then its check passes by luck at most 2.5% of the time. H
needs that check to pass, so H also passes by luck at most 2.5% of the time.
Asking for both scores never raises the chance of a lucky pass.

### Why H has this form

**Why the hypothesis is about gaps.**

1. Suppose q were right on average: the chance that y = 1 equals q, whatever
   p and q are.
2. Then every group would have λ = 1 and c\* = 1.
3. So q would beat p in every group and overall, and every group's moves
   would be the right size.
4. Yet both gaps would be 0, since the two halves would not differ.

So "q beats p" and "the moves were the right size" can hold even for a
measure that picks out nothing. Only the gaps tell measures that pick out
justified moves from measures that do not. That is why H is the only
hypothesis, and everything else is an
[estimate](#estimates-without-a-pass-rule).

**Why the gaps compare λ̂ and c\* themselves**, not their distance from 1.

1. λ̂ is the average of λᵢ weighted by Δ², since Δ(y − p) = Δ²·λᵢ.
2. Each question's Brier improvement is 2Δ² × (λᵢ − ½) = Δ²·(2λᵢ − 1).
   Adding these over a group and using step 1 gives a total of
   ΣΔ² × (2λ̂ − 1).
3. So for the same total move size ΣΔ², a higher λ̂ means more improvement.
4. c\* plays the same role for log loss.

Whether the moves were the right size (λ̂ and c\* near 1) is reported as an
estimate.

**Why halves.** A measure tells justified updates apart if the updates it
rates high are better justified than those it rates low. The median is the
default line between high and low, so the halves split each source at its
median. The split is the same for every measure and is fixed now, so the
exploration run does not change it.

The choice was not blind. It was made after seeing the pilot, where λ̂ and
c\* drop between groups 2 and 3 for five measures while groups 3 and 4 look
alike (|KO| drops between groups 3 and 4 instead). See the
[SQ2 table](#sq2-warrant-by-group).

### Testing six measures

- **No correction.** H is tested once for each of the six measures, and each
  result answers its own question: does this measure tell justified updates
  apart? So every conclusion is about one measure, and each has at most a
  2.5% chance of a lucky pass (passing although the measure's true gaps are 0
  or below).
- **The cost.** Across the six, the chance that at least one passes by luck is
  about 8 to 12% on the pilot. That is below the 14% that six independent
  checks would give, because some measures' gaps move together (for example
  Δ² and KL).
- **Not a ranking.** No test compares the measures with each other (for
  example, whether |Z| picks better moves than plain move size Δ²). So one
  measure passing and another failing does not show that the first is better.

### Power and test dates

**The gap that matters is 1.0**, for both the λ̂ gap and the c\* gap. It was
fixed after the pilot and before the exploration run, so no exploration
outcome can shape it. What it means:

1. A half's Brier improvement is ΣΔ² × (2λ̂ − 1) (see
   [Why H has this form](#why-h-has-this-form)). So each unit of movement
   earns 2λ̂ − 1.
2. Suppose the top half's moves are the right size: λ̂ = 1, which earns +1
   per unit.
3. A gap of 1.0 then puts the low half at λ̂ = 0. Its moves carry no
   information, since keeping none of them would score best. Taking them
   still loses 1 per unit, because the Brier score punishes a step away from
   the outcome more than it rewards an equal step toward it.
4. So a measure with this gap separates informative moves from moves that
   carry no information. A c\* gap of 1.0 means about the same under log
   loss.

With the top half at λ̂ = 1, a gap g puts the low half at λ̂ = 1 − g, which
earns 2λ̂ − 1 = 1 − 2g per unit. So the gaps in the table below mean:

- **0.25:** low half λ̂ = 0.75. Its moves still help, earning +0.5 per unit.
- **0.5:** λ̂ = 0.5. They break even (0).
- **0.75:** λ̂ = 0.25. They hurt a little (−0.5).
- **1.0:** λ̂ = 0. They carry no information (−1).
- **1.5:** λ̂ = −0.5. They point the wrong way (−2).

Gaps below 1.0 would matter too. But no realistic number of test dates could
detect a gap of 0.5 (see the table below). A gap of 1.0 is about the
smallest gap with a plain meaning that a realistic number of test dates can
detect.

**Test dates needed.** `scripts/h_power.py` computes them in these steps:

1. On the pilot, the λ̂ gaps are +1.21 to +2.43 and the c\* gaps +0.96 to
   +1.80. But every λ̂ gap's 95% interval includes 0, so H passes for no
   measure on the pilot. These gaps are likely too big to plan with, because
   the pilot shaped H.
2. More questions give narrower intervals. A standard error shrinks in
   proportion to 1/√(number of questions), so the pilot's family bootstrap
   standard errors are scaled from its 100 questions to about 380 questions
   per test date.
3. For c\*, the standard error is taken from the middle half of the bootstrap
   values. The few resamples where a half's c\* reaches the ±50 cap (about 3%
   at most) would inflate the usual one.
4. *Power* is the chance that a check passes when the true gap has a given
   size. With a normal approximation, a gap's check passes when the estimated
   gap is more than 1.96 standard errors above 0. A true gap of 2.8 standard
   errors clears that bar 80% of the time, so its power is 80%.
5. H passes only when both of its gaps pass. The two gaps rise and fall
   together across resamples (correlation 0.73 to 0.98), so H's power is the
   chance that both checks pass under that correlation.
6. The table gives the fewest test dates for 80% power, if both true gaps
   equal the gap in the first column.

| gap | Δ² | KL | UR_B | UR_L | \|Z\| | \|KO\| |
| --- | --- | --- | --- | --- | --- | --- |
| 0.25 | 70 | 57 | 42 | 42 | 190 | 91 |
| 0.5 | 18 | 15 | 11 | 11 | 48 | 23 |
| 0.75 | 8 | 7 | 5 | 5 | 22 | 11 |
| **1.0** | **5** | **4** | **3** | **3** | **12** | **6** |
| 1.5 | 2 | 2 | 2 | 2 | 6 | 3 |

- At the gap of 1.0, five measures need 3 to 6 test dates. |Z| needs 12,
  because its c\* gap is the noisiest.
- Two test dates reach 80% power only at a gap of 1.5, and not even there for
  |Z| and |KO|.
- Besides the pilot's date and one exploration date, about 24 ForecastBench
  dates have resolved questions so far. But dates two weeks apart share 40 to
  70 market questions, so counts far above 10 are not realistic, even before
  cost.

**Not fixed yet: the number of test dates.** The pilot's spread rests on only
5 shared events (see [Limits](#limits)), and the exploration run gives a
better one. Before the preregistration, the script is rerun on the
exploration data, and the preregistration then fixes the number of test
dates for the gap of 1.0:

```bash
python scripts/h_power.py data/results/run_<timestamp>.csv  # about 1 min
```

### Estimates without a pass rule

Everything else is reported as an estimate with its 95% interval:

- **Baseline:** does q beat p over all questions?
- **SQ2 for each group:** *achieved*, λ̂ and c\* (does q beat p, and was the
  move the right size?).
- **SQ1 correlations**, because they mix move size with how justified the
  move was (see the README's key terms).
- **SQ3 D**, because even the best rule's gain is too small to detect:
  1. The best single set of "keep p" marks, chosen knowing the outcomes,
     would gain only 0.003 to 0.013 Brier per moved question on the pilot
     (depending on the measure).
  2. The smallest D two test dates could detect is 0.012 to 0.017.
  3. So even that best gain is at or below what a test could detect.

The baseline and SQ2 per group can hold even for a measure that picks out
nothing (see [Why H has this form](#why-h-has-this-form)), so they describe
the moves rather than test the measures.

## Method detail, by README step

### Step 2: prior p

- **Model cutoff.** `claude-haiku-4-5-20251001`'s Jul 2025 training cutoff
  precedes every question's `freeze_datetime` and AskNews search window, so
  neither the outcomes nor the retrieved evidence were in training.
- **Temperature 0** maximizes reproducibility, and relies on decode time
  reasoning rather than ensembling samples.

### Step 3: evidence

- **Evidence cutoff.** The AskNews search window ends at each question's
  `freeze_datetime` (not the resolution date), so retrieval can't surface
  news that reveals the outcome.
- **Leakage audit.** `scripts/audit_leakage.py` checks offline that this held
  for the cached evidence. It fails closed: an article whose `published_date`
  is missing or unreadable makes the audit fail instead of being skipped.
  Rerun on 2026-10-18 over the 927 cached articles for the pilot's 100
  questions (the other 248 have no cached evidence yet), it found none
  published after the freeze and none with unverifiable dates
  (`data/results/leakage_20261018T135507Z.json`).
- **Lookback:** 60 days before `freeze_datetime`, for recent reporting
  without flooding the LLM with stale context.

### Step 6: measures

**Matching measures.** Two pairs of measures rank questions the same way:

1. Δ² ranks questions exactly like |q − p|, the size of the difference
   measure, because squaring keeps the order of sizes.
2. |KO| ranks questions exactly like |logit q − logit p|, the size of the log
   likelihood ratio that p and q imply, because
   KO = tanh((logit q − logit p)/2) and tanh keeps order.
3. The groups, SQ1's Spearman, SQ2, SQ3 and H use only these ranks, so each
   pair gives the same results there. Only SQ1's Pearson, which uses the
   values themselves, differs.

### Step 7: SQ1 and intervals

**Families.** One event, such as one week's stock market or one day's
weather, decides a dataset family together. So its questions are not
independent, and the bootstrap resamples the whole family at once. The
bootstrap uses seed 0.

### Step 8: SQ2

- **λ̂** = ΣΔ(y − p)/ΣΔ² is the single scale c that makes p + cΔ score best
  under Brier. Since Brier is a squared error, this is the least squares slope
  of y − p on Δ, with no intercept.
- **c\*** is the single scale c of each move in log odds,
  logit p + c·(logit q − logit p), that scores best under log loss. Scaling in
  log odds keeps every scaled forecast strictly between 0 and 1, so log loss
  stays finite and the search never stops at the edge of the probability
  range. The cost is that c\* measures size on a different scale than λ̂.
- **The c\* cap.** c\* is searched in [−50, 50]. A result at the cap is
  shown as > 50 (or < −50): the best scale lies beyond it. This happens, for
  example, when every move in the group pointed toward its outcome. Making
  the moves larger then always lowers log loss, so no finite scale is best.
  The other end works the same way (< −50: every move pointed away).
- **share** = *achieved* ÷ the gain at the best scale, that is, the gain the
  group would have had with every move scaled by λ̂ (Brier) or c\* (log loss).
  For Brier this works out to (2λ̂ − 1)/λ̂², which is 100% at λ̂ = 1. It is
  shown only when achieved > 0, since otherwise it is negative or undefined.
- **Per source.** λ̂ and c\* are also given per source, without a CI. A
  dataset source on one date is a single family, so every resample that
  includes it gives the same value.
- **Groups rebuilt in each resample.** Each resample ranks and groups its
  questions again, so the intervals include the uncertainty in which question
  lands in which group.

### Step 9: H

- **Output.** `analyze_results.py` reports H under `hypothesis` in the
  summary JSON: each half's λ̂ and c\*, both gaps, and each gap's 95%
  interval, whose low end is the one direction check.
- **The c\* cap in H.** For |Z|, the low half's c\* sits at the −50 cap in
  about 3% of resamples. In those resamples the gap is the top half's c\*
  plus 50, the largest gaps of all. They make up more than the top 2.5%, so
  the interval's top end (+50.67) is one of them, and it is shown as > +50.

### Step 10: SQ3

**Intervals.** SQ3's CI reruns the whole procedure on each resample: it
chooses the "keep p" marks on the other sources and applies them to the held
out one. D is a mean over the tested questions.

## Pilot results

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

- Pearson uses the values, so a few large moves can carry it. Spearman uses
  only ranks, so every question counts the same.
- The size measures (Δ², KL, |Z|, |KO|) have a high Pearson that rests on
  about five large moves, and a Spearman near 0.
- The uncertainty reductions (UR_B, UR_L) are positive on both, almost
  entirely through questions that resolved NO.

### SQ2: warrant by group

Each measure's 4 within source groups (1 = lowest, 4 = top). *achieved* is
the mean improvement, and *share* is defined under [Step 8](#step-8-sq2).

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

- **Top groups (4).** Every measure's top group was about the right size
  (λ̂ 0.85 to 1.02, c\* 0.81 to 1.05) and captured 97 to 100% of the
  available improvement under both scores.
- **Group 3.** For five measures, group 3 looks like group 4 (λ̂ 0.70 to
  1.07, c\* 0.65 to 1.06), and λ̂ and c\* drop between groups 2 and 3. |KO|
  is the exception: its group 3 has λ̂ and c\* near 0.
- **Groups 1 and 2.** They hold only 2 to 13% of the movement (ΣΔ²), so their
  intervals are too wide to tell how justified those moves were. Every
  group 1 c\* interval reaches the −50 cap, and so does |Z|'s group 2,
  because some resamples keep only moves that pointed away from their
  outcome.
- **By source.** λ̂ and c\* also differ by source, for example −1.33 and
  −1.05 for acled but +1.04 and +1.04 for polymarket (all sources are in the
  summary JSON). This is why groups are formed within sources.

### SQ3: "keep p" rule vs always q

One source held out at a time (D > 0 = rule wins).

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | +0.000 [−0.033, +0.011] | +0.004 [−0.073, +0.031] | 1, 2 / 1, 2 |
| KL | +0.001 [−0.030, +0.016] | +0.006 [−0.065, +0.042] | 1, 2 / 1, 2 |
| UR_B | +0.007 [−0.042, +0.024] | +0.030 [−0.094, +0.064] | 1, 2 / 1, 2 |
| UR_L | +0.010 [−0.041, +0.025] | +0.022 [−0.093, +0.063] | 2 / 1, 2 |
| \|Z\| | −0.001 [−0.039, +0.019] | +0.003 [−0.082, +0.052] | 1, 2 / 1, 2 |
| \|KO\| | +0.011 [−0.036, +0.023] | +0.021 [−0.085, +0.056] | 1, 2, 3 / 1, 2, 3 |

Every D interval includes 0, so no rule is distinguishable from always using
q.

### Limits

- **One forecast date.** Every forecast was made as of 2025-10-16. The 67
  questions from the five dataset sources all resolved on 2025-11-02, and
  each source was decided by one shared event. In the pilot, 12 of 13
  dbnomics stations warmed against a forecast near 0.37, and only 2 of 11
  yfinance stocks rose against about 0.51. This has two consequences, and
  more forecast dates would address both:
  1. The CIs resample families, and there are only 5 such shared events (5
     dataset families among 38). So how much the CIs vary is estimated from
     very few draws.
  2. Holding out a source (SQ3) tests whether a rule carries over to a new
     source, not to another period with different shared events.
- **Market questions about one event** (for example three Spotify top artist
  questions) are still treated as separate families, which makes the
  intervals slightly too narrow. There are only a few such groups.
