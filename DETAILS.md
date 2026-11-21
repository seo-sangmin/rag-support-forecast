# Reasons for H, method detail and result tables

The [README](README.md) gives the question, the draft hypothesis H and a
summary of the pilot and the exploration run. This file gives the detail
behind them, in four parts:

1. [Hypothesis H](#hypothesis-h): what H tests, why it has this form, how the
   six measures are handled, power, and what is only estimated.
2. [Method detail](#method-detail-by-readme-step): finer points of the
   README's [Method](README.md#method) steps, in step order.
3. [Pilot results](#pilot-results): the full tables and the limits.
4. [Exploration results](#exploration-results): the full tables for both
   models, H without the questions that may have been settled, and notes on
   two odd answers.

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
- The table treats every question as independent, so each test date in it
  stands for 380 questions. A date that uses all its usable questions adds
  less than that. Its dataset questions share one event per family (up to
  about 50 per family, against about 13 in the pilot), and the market
  questions it repeats from nearby dates add almost nothing new. So for such
  dates the table is optimistic. A test spread over more dates, with each
  market question used once, comes closer to the assumption.

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

- **Model cutoff.** Anthropic reports a July 2025 training-data cutoff for
  `claude-haiku-4-5-20251001` and released the snapshot on October 15, 2025,
  before every question's freeze. Outcomes that first became knowable after
  release could not have been in its training data. A market can resolve
  months after the underlying event. If the result was public before
  release, the freeze and market resolution dates alone cannot tell us
  whether the model saw it during training.
  [Anthropic's model specifications](https://platform.claude.com/docs/en/models/haiku-4-5/overview#specifications).
  The exploration's second model, `claude-opus-4-5-20251101`, has an August
  2025 training-data cutoff and was released on November 24, 2025, before
  both exploration freezes (2026-03-06 and 2026-10-09)
  ([its specifications](https://platform.claude.com/docs/en/models/opus-4-5/overview#specifications)).
- **Temperature 0** maximizes reproducibility, and relies on decode time
  reasoning rather than ensembling samples.

### Step 3: evidence

- **Evidence cutoff.** The AskNews search window ends at each question's
  `freeze_datetime` (not the resolution date), so no article dated after
  the freeze is retrieved.
- **Leakage audit.** `scripts/audit_leakage.py` checks offline that this held
  for the cached evidence. It fails closed: an article whose `published_date`
  is missing or unreadable makes the audit fail instead of being skipped.
  Rerun on 2026-10-18 over the 927 cached articles for the pilot's 100
  questions (the other 248 have no cached evidence yet), it found none
  published after the freeze and none with unverifiable dates
  (`data/results/leakage_20261018T135507Z.json`). The exploration's audits
  found none either: `leakage_20261120T033022Z.json` for the 2026-03-15 set
  (232 questions) and `leakage_20261120T033043Z.json` for the 2026-10-11 set
  (65 questions).
- **What a date check can't catch.** An article published before the freeze
  can report an event that has already happened. The San Diego FC question
  in the [pilot](#pilot-results) is one example. Even when the outcome is
  still uncertain at the freeze, the audit has three limits.
  1. An article with a wrong `published_date`, or edited after that date,
     still passes.
  2. The model reads AskNews's summary of each article, and the cache does
     not record when AskNews wrote it.
  3. The search runs long after the freeze (July 2026 for the pilot), so
     the ranking in use then picks the top 10 articles. It may favor
     articles that later turned out to matter.
- **Why a leak matters for H.** Leaked news would mostly cause large moves
  toward the outcome. For the size measures, such moves land in the top
  half and never count as too large or the wrong way. So a leak could
  produce the very pattern H tests.
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

San Diego FC clinched a playoff berth on August 23, 2025. The question
froze on October 16, and ForecastBench records the YES resolution on
January 1, 2026. The retrieved articles reported the clinch, and the
forecast went from 0.35 to 0.99. The reported pilot includes this question.
As a sensitivity check, the mean Brier improvement was +0.0222 across all
100 questions and +0.0182 across the other 99.
[Club match report](https://www.sandiegofc.com/news/match-recap-san-diego-fc-clinches-playoff-berth-with-scoreless-draw-against-portland-timbers-at-snapdragon-stadium) ·
[Pilot forecasts](data/results/run_20260914T104832Z.csv).

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
- **Question mix.** Results describe ForecastBench's mix of questions and
  may not carry over to other kinds. Ranking within each source (Method
  step 8) gives every group the same source mix, which protects comparisons
  inside the sample but says nothing about other questions. Two features
  stand out:
  1. 245 of the 348 questions (70%) come from the five dataset sources,
     whose questions follow a few fixed templates, such as whether a
     weather station will be warmer on one date than on another.
  2. Only questions resolved to 0 or 1 are kept. In the resolution set used
     here, that dropped 143 of the 246 market questions, mostly long ones
     (median close date 2030). The kept ones had a median market forecast
     of 0.036 at the freeze and the dropped ones 0.35, so the kept market
     questions are mostly short ones the crowd already saw as near certain
     NO. Just 3 of them (1 in the pilot) resolved early while their market
     was still open, so whether they were kept depended on how they
     resolved.

## Exploration results

297 questions, 232 from the 2026-03-15 set and 65 from the 2026-10-11 set
(see [the exploration README](data/exploration/README.md)), forecast by
Haiku 4.5 (`data/results/run_20261120T025349Z.csv`) and Opus 4.5
(`data/results/run_20261120T030940Z.csv`) from the same evidence. Each has
its two summary files (`_summary.json` and `_drop_maybe_settled_summary.json`).
Haiku moved 243 forecasts and Opus 224. The README gives the baseline and H
on all questions. Cells are estimate [95% CI].

### H without the questions that may have been settled

The second value of H leaves out 74 questions: every ACLED question, and
every market priced 0.05 or less or 0.95 or more at the freeze (see
[Answers already public at the freeze](data/exploration/README.md#answers-already-public-at-the-freeze)).
That leaves 223 questions, of which Haiku moved 193 and Opus 165.

| measure | Haiku λ̂ gap | Haiku c\* gap | Opus λ̂ gap | Opus c\* gap |
| --- | --- | --- | --- | --- |
| Δ² | −0.30 [−1.45, +0.64] | −0.12 [−1.33, +0.66] | −0.72 [−2.43, +0.31] | −0.54 [−2.13, +0.47] |
| KL | −0.73 [−1.74, +0.38] | −0.56 [−1.83, +0.45] | −0.95 [−2.36, +0.44] | −0.77 [−2.28, +0.58] |
| UR_B | +0.13 [−0.45, +0.77] | −0.46 [−0.90, +0.52] | −0.31 [−1.05, +0.61] | −0.49 [−1.05, +0.46] |
| UR_L | +0.20 [−0.44, +0.79] | −0.43 [−0.90, +0.54] | −0.31 [−1.05, +0.60] | −0.49 [−1.05, +0.46] |
| \|Z\| | −0.36 [−1.30, +0.85] | −0.07 [−0.97, +1.00] | −0.45 [−1.69, +0.55] | −0.39 [−1.36, +0.43] |
| \|KO\| | +0.12 [−1.27, +0.90] | +0.25 [−1.31, +0.98] | −1.18 [−2.21, +0.07] | −1.41 [−2.78, +0.20] |

H passes for no measure here either. Opus's Δ² and KL λ̂ gaps, whose
intervals lie below 0 on all questions, now include 0.

### SQ1 on the exploration

**Haiku 4.5**

| measure | Brier: Pearson | Brier: Spearman | log loss: Pearson | log loss: Spearman |
| --- | --- | --- | --- | --- |
| Δ² | +0.04 [−0.31, +0.39] | +0.14 [−0.01, +0.28] | +0.21 [−0.30, +0.50] | +0.14 [−0.01, +0.29] |
| KL | +0.20 [−0.34, +0.45] | +0.11 [−0.03, +0.26] | +0.71 [−0.34, +0.91] | +0.11 [−0.04, +0.26] |
| UR_B | −0.02 [−0.23, +0.21] | +0.35 [+0.20, +0.50] | −0.22 [−0.40, +0.14] | +0.39 [+0.23, +0.53] |
| UR_L | −0.04 [−0.25, +0.20] | +0.35 [+0.21, +0.49] | −0.25 [−0.45, +0.13] | +0.39 [+0.24, +0.53] |
| \|Z\| | +0.03 [−0.16, +0.22] | +0.21 [+0.09, +0.34] | +0.03 [−0.25, +0.19] | +0.23 [+0.10, +0.36] |
| \|KO\| | +0.01 [−0.19, +0.22] | +0.10 [−0.04, +0.24] | +0.05 [−0.25, +0.23] | +0.10 [−0.05, +0.25] |

**Opus 4.5**

| measure | Brier: Pearson | Brier: Spearman | log loss: Pearson | log loss: Spearman |
| --- | --- | --- | --- | --- |
| Δ² | −0.05 [−0.46, +0.45] | +0.16 [+0.02, +0.30] | −0.12 [−0.53, +0.45] | +0.17 [+0.03, +0.31] |
| KL | −0.06 [−0.46, +0.42] | +0.14 [−0.00, +0.28] | −0.10 [−0.52, +0.44] | +0.15 [+0.01, +0.29] |
| UR_B | +0.01 [−0.20, +0.24] | +0.32 [+0.17, +0.46] | −0.04 [−0.26, +0.26] | +0.35 [+0.20, +0.49] |
| UR_L | +0.00 [−0.21, +0.23] | +0.32 [+0.17, +0.46] | −0.04 [−0.28, +0.25] | +0.35 [+0.20, +0.49] |
| \|Z\| | +0.05 [−0.17, +0.27] | +0.24 [+0.12, +0.36] | +0.02 [−0.21, +0.28] | +0.27 [+0.14, +0.38] |
| \|KO\| | +0.04 [−0.18, +0.28] | +0.12 [−0.01, +0.26] | +0.02 [−0.21, +0.29] | +0.14 [−0.00, +0.28] |

- **Size measures.** Their Pearson is near 0, because the largest moves
  pointed away from the outcome about as often as toward it (10 of Haiku's
  and 9 of Opus's 20 largest moves by Δ² pointed away). Haiku's KL under log
  loss (+0.71) is the exception, and one question carries it (see the
  [notes](#notes-on-the-exploration)). Their Spearman is small and positive
  (+0.10 to +0.27), and the intervals of |Z| lie above 0 in both models.
- **Uncertainty reductions.** UR_B and UR_L keep the pilot's positive
  Spearman (+0.32 to +0.39, every interval above 0), but their Pearson is
  −0.25 to +0.01.

### SQ2 on the exploration

Each measure's 4 within source groups (1 = lowest, 4 = top), as in the
[pilot table](#sq2-warrant-by-group).

**Haiku 4.5**

| measure | group | n | Brier achieved | λ̂ | log-loss achieved | c\* | share (Brier / log) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Δ² | 1 | 60 | +0.002 [−0.006, +0.010] | +1.09 [−1.32, +2.94] | +0.003 [−0.017, +0.036] | +0.68 [−0.36, +1.68] | 99% / 77% |
| Δ² | 2 | 61 | +0.004 [−0.007, +0.036] | +0.68 [+0.16, +1.88] | +0.013 [−0.021, +0.098] | +0.69 [+0.24, +1.63] | 78% / 76% |
| Δ² | 3 | 60 | +0.061 [−0.008, +0.100] | +1.19 [+0.40, +1.59] | +0.120 [−0.116, +0.220] | +1.06 [+0.06, +1.81] | 97% / 100% |
| Δ² | 4 | 62 | −0.029 [−0.114, +0.076] | +0.40 [+0.10, +0.77] | +0.033 [−0.355, +0.641] | +0.57 [+0.03, +0.95] | — / 28% |
| KL | 1 | 56 | −0.002 [−0.010, +0.015] | +0.13 [−1.69, +2.88] | −0.003 [−0.022, +0.045] | +0.27 [−0.87, +2.51] | — / — |
| KL | 2 | 62 | +0.018 [−0.004, +0.047] | +1.34 [+0.35, +2.22] | +0.052 [−0.005, +0.121] | +1.31 [+0.42, +2.26] | 94% / 95% |
| KL | 3 | 59 | +0.056 [−0.005, +0.097] | +1.18 [+0.44, +1.56] | +0.129 [−0.047, +0.218] | +1.16 [+0.28, +1.62] | 98% / 98% |
| KL | 4 | 66 | −0.033 [−0.122, +0.067] | +0.38 [+0.07, +0.73] | −0.006 [−0.411, +0.601] | +0.52 [−0.05, +0.94] | — / — |
| UR_B | 1 | 56 | −0.020 [−0.086, +0.061] | +0.37 [−0.08, +0.85] | +0.159 [−0.189, +0.801] | +0.82 [−0.14, +1.02] | — / 89% |
| UR_B | 2 | 62 | +0.019 [−0.034, +0.066] | +0.81 [−0.07, +1.38] | +0.041 [−0.080, +0.143] | +0.78 [−0.11, +1.36] | 95% / 92% |
| UR_B | 3 | 62 | +0.007 [−0.041, +0.074] | +0.57 [+0.05, +1.47] | +0.004 [−0.108, +0.163] | +0.51 [+0.07, +1.84] | 44% / 14% |
| UR_B | 4 | 63 | +0.027 [−0.038, +0.070] | +0.80 [+0.16, +1.24] | −0.023 [−0.295, +0.148] | +0.38 [−0.09, +1.25] | 94% / — |
| UR_L | 1 | 56 | −0.018 [−0.086, +0.059] | +0.39 [−0.09, +0.85] | +0.165 [−0.191, +0.792] | +0.83 [−0.17, +1.02] | — / 90% |
| UR_L | 2 | 62 | +0.010 [−0.041, +0.067] | +0.65 [−0.10, +1.31] | +0.016 [−0.095, +0.148] | +0.60 [−0.15, +1.32] | 70% / 57% |
| UR_L | 3 | 60 | +0.030 [−0.029, +0.078] | +0.90 [+0.15, +1.57] | +0.068 [−0.076, +0.174] | +0.92 [+0.16, +2.04] | 99% / 99% |
| UR_L | 4 | 65 | +0.012 [−0.043, +0.065] | +0.61 [+0.14, +1.21] | −0.063 [−0.305, +0.138] | +0.30 [−0.09, +1.18] | 60% / — |
| \|Z\| | 1 | 56 | −0.004 [−0.018, +0.009] | −0.09 [−1.90, +1.65] | −0.017 [−0.058, +0.024] | −0.18 [−4.92, +1.07] | — / — |
| \|Z\| | 2 | 63 | +0.007 [−0.024, +0.058] | +0.69 [−0.07, +1.85] | +0.014 [−0.060, +0.131] | +0.65 [−0.06, +1.62] | 79% / 69% |
| \|Z\| | 3 | 58 | +0.027 [−0.036, +0.104] | +0.69 [+0.24, +1.26] | +0.061 [−0.072, +0.686] | +0.68 [+0.27, +1.34] | 80% / 79% |
| \|Z\| | 4 | 66 | +0.006 [−0.092, +0.080] | +0.53 [+0.08, +0.87] | +0.102 [−0.372, +0.596] | +0.69 [−0.03, +0.98] | 20% / 71% |
| \|KO\| | 1 | 55 | +0.006 [−0.012, +0.022] | +1.26 [−0.84, +2.74] | +0.021 [−0.027, +0.062] | +1.49 [−0.75, +2.92] | 96% / 89% |
| \|KO\| | 2 | 66 | +0.006 [−0.027, +0.049] | +0.72 [−0.18, +1.74] | +0.017 [−0.060, +0.115] | +0.72 [−0.10, +1.79] | 85% / 85% |
| \|KO\| | 3 | 57 | +0.056 [−0.013, +0.100] | +1.12 [+0.36, +1.54] | +0.125 [−0.026, +0.223] | +1.11 [+0.38, +1.66] | 99% / 99% |
| \|KO\| | 4 | 65 | −0.027 [−0.111, +0.071] | +0.39 [+0.08, +0.77] | +0.013 [−0.386, +0.605] | +0.54 [−0.01, +0.95] | — / 12% |

**Opus 4.5**

| measure | group | n | Brier achieved | λ̂ | log-loss achieved | c\* | share (Brier / log) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Δ² | 1 | 53 | +0.001 [−0.005, +0.020] | +0.95 [−1.23, +5.34] | −0.004 [−0.040, +0.060] | +0.25 [−1.66, +2.84] | 100% / — |
| Δ² | 2 | 59 | +0.024 [+0.001, +0.045] | +2.27 [+0.59, +3.73] | +0.067 [+0.005, +0.122] | +2.06 [+0.60, +3.81] | 69% / 74% |
| Δ² | 3 | 54 | +0.036 [−0.019, +0.065] | +1.28 [+0.08, +1.82] | +0.089 [−0.044, +0.160] | +1.24 [+0.15, +1.96] | 95% / 96% |
| Δ² | 4 | 58 | +0.001 [−0.071, +0.093] | +0.50 [+0.19, +0.95] | −0.013 [−0.214, +0.236] | +0.48 [+0.18, +0.93] | 2% / — |
| KL | 1 | 58 | +0.011 [−0.003, +0.027] | +3.54 [−0.30, +6.22] | +0.022 [−0.030, +0.066] | +2.35 [−1.65, +4.60] | 48% / 66% |
| KL | 2 | 51 | +0.016 [−0.006, +0.043] | +1.53 [+0.08, +3.24] | +0.045 [−0.010, +0.117] | +1.44 [+0.26, +3.17] | 88% / 91% |
| KL | 3 | 57 | +0.022 [−0.021, +0.061] | +0.99 [+0.02, +1.70] | +0.054 [−0.048, +0.147] | +0.96 [+0.12, +1.83] | 100% / 100% |
| KL | 4 | 58 | +0.012 [−0.069, +0.094] | +0.56 [+0.20, +0.96] | +0.020 [−0.206, +0.245] | +0.53 [+0.20, +0.94] | 37% / 23% |
| UR_B | 1 | 55 | +0.015 [−0.053, +0.069] | +0.64 [−0.03, +1.14] | +0.058 [−0.120, +0.218] | +0.70 [+0.02, +1.09] | 68% / 76% |
| UR_B | 2 | 55 | +0.018 [−0.020, +0.085] | +1.01 [+0.05, +2.22] | +0.042 [−0.048, +0.192] | +1.00 [+0.02, +2.82] | 100% / 100% |
| UR_B | 3 | 56 | +0.009 [−0.035, +0.056] | +0.67 [−0.04, +1.98] | +0.008 [−0.101, +0.120] | +0.54 [−0.11, +2.60] | 75% / 39% |
| UR_B | 4 | 58 | +0.019 [−0.038, +0.061] | +0.72 [+0.16, +1.31] | +0.032 [−0.151, +0.158] | +0.57 [+0.15, +1.74] | 84% / 63% |
| UR_L | 1 | 55 | +0.012 [−0.051, +0.069] | +0.61 [−0.03, +1.15] | +0.047 [−0.118, +0.215] | +0.67 [+0.01, +1.10] | 58% / 68% |
| UR_L | 2 | 55 | +0.028 [−0.020, +0.091] | +1.18 [+0.09, +2.07] | +0.065 [−0.045, +0.209] | +1.22 [+0.12, +2.98] | 98% / 97% |
| UR_L | 3 | 56 | +0.010 [−0.035, +0.058] | +0.69 [−0.04, +2.07] | +0.009 [−0.103, +0.122] | +0.55 [−0.18, +2.74] | 79% / 43% |
| UR_L | 4 | 58 | +0.013 [−0.041, +0.057] | +0.65 [+0.11, +1.26] | +0.020 [−0.160, +0.149] | +0.52 [+0.13, +1.63] | 71% / 46% |
| \|Z\| | 1 | 56 | +0.014 [−0.006, +0.033] | +2.55 [−0.14, +5.05] | +0.035 [−0.019, +0.095] | +1.45 [−0.13, +2.60] | 63% / 88% |
| \|Z\| | 2 | 54 | +0.018 [−0.021, +0.049] | +0.98 [−0.24, +1.85] | +0.038 [−0.056, +0.118] | +0.84 [−0.36, +1.62] | 100% / 95% |
| \|Z\| | 3 | 56 | +0.002 [−0.028, +0.066] | +0.53 [+0.05, +1.43] | +0.017 [−0.061, +0.179] | +0.61 [+0.10, +1.54] | 20% / 57% |
| \|Z\| | 4 | 58 | +0.027 [−0.058, +0.096] | +0.65 [+0.20, +1.10] | +0.050 [−0.188, +0.242] | +0.58 [+0.19, +1.11] | 72% / 55% |
| \|KO\| | 1 | 49 | +0.016 [−0.002, +0.038] | +2.45 [+0.25, +5.03] | +0.035 [−0.003, +0.090] | +2.36 [+0.33, +5.68] | 65% / 67% |
| \|KO\| | 2 | 60 | +0.025 [−0.007, +0.052] | +1.44 [+0.15, +2.27] | +0.059 [−0.021, +0.131] | +1.52 [+0.07, +2.95] | 91% / 90% |
| \|KO\| | 3 | 57 | +0.006 [−0.036, +0.051] | +0.64 [−0.24, +1.44] | +0.009 [−0.096, +0.118] | +0.56 [−0.25, +1.42] | 69% / 43% |
| \|KO\| | 4 | 58 | +0.014 [−0.064, +0.096] | +0.57 [+0.20, +1.02] | +0.036 [−0.196, +0.261] | +0.56 [+0.21, +1.00] | 44% / 39% |

- **Top groups (4).** Every top group's moves were too large (λ̂ 0.38 to
  0.80, c\* 0.30 to 0.69). For Δ² and KL, the top group's λ̂ interval lies
  below 1 in both models. For Haiku, the top groups of Δ², KL and |KO|
  made the Brier score slightly worse (achieved −0.027 to −0.033, each
  interval including 0).
- **Groups 1 and 2.** Their λ̂ is positive in 23 of the 24 cells, and for
  Opus often above 1 (moves too small), where the pilot's was negative in
  11 of 12. Together with the top groups' smaller λ̂, this is why 20 of the
  24 H gaps are below 0.
- **Movement.** The low half holds 6 to 15% of the movement (ΣΔ²) for the
  size measures (pilot 2 to 7%) and about half for UR_B and UR_L (pilot
  13%). No c\* interval in these tables reaches the ±50 cap.
- **By source.** λ̂ ranges from −0.62 (yfinance) to +1.51 (fred) for Haiku
  and from −0.51 (infer) to +2.92 (fred) for Opus. All sources, with c\*,
  are in the summary JSON files.

### SQ3 on the exploration

One source held out at a time (D > 0 = rule wins).

**Haiku 4.5**

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | +0.004 [−0.033, +0.028] | −0.065 [−0.221, +0.086] | 4 / none |
| KL | +0.009 [−0.031, +0.030] | −0.056 [−0.212, +0.103] | 1, 4 / 1, 4 |
| UR_B | −0.008 [−0.036, +0.019] | −0.104 [−0.217, +0.065] | 1 / 4 |
| UR_L | −0.004 [−0.036, +0.019] | −0.075 [−0.217, +0.070] | 1 / 4 |
| \|Z\| | −0.021 [−0.037, +0.021] | −0.080 [−0.213, +0.086] | 1 / 1 |
| \|KO\| | +0.005 [−0.035, +0.025] | −0.061 [−0.217, +0.089] | 4 / none |

**Opus 4.5**

| measure | Brier: D | log loss: D | keep p in groups (chosen from all data, Brier / log) |
| --- | --- | --- | --- |
| Δ² | −0.009 [−0.023, +0.015] | −0.022 [−0.060, +0.048] | none / 1, 4 |
| KL | −0.007 [−0.024, +0.014] | −0.019 [−0.064, +0.041] | none / none |
| UR_B | −0.010 [−0.028, +0.010] | −0.019 [−0.072, +0.021] | none / none |
| UR_L | −0.010 [−0.028, +0.009] | −0.018 [−0.072, +0.021] | none / none |
| \|Z\| | −0.008 [−0.025, +0.011] | −0.014 [−0.066, +0.036] | none / none |
| \|KO\| | −0.003 [−0.026, +0.012] | −0.033 [−0.067, +0.037] | none / none |

Every D interval includes 0, as in the pilot.

### Notes on the exploration

- **A prior of exactly 0.** Haiku's prior for "Will Cooper Flagg win the
  2025–26 NBA Rookie of the Year award?" was exactly 0. Its reasoning put
  him in the 2024 draft, so it judged him a second year player who could
  not win (he was the first pick of the 2025 draft). With the evidence it
  moved to 0.72, and he won. Log loss clips r to [1e-6, 1 − 1e-6], so this
  prior scores −log(1e-6) ≈ 13.8, and the question's improvement of 13.5
  adds 13.5 / 297 ≈ +0.045 to Haiku's mean log loss improvement of +0.035.
  Without it, that mean is −0.011, and Haiku's SQ1 Pearson for KL under log
  loss is −0.14 instead of +0.71. With a clip of 0.01, the mean is +0.004.
  The clip also enters c\* and the measures KL, UR_L and |KO|. Opus has
  one forecast of exactly 0 too (next note), but it was right, so its
  results barely depend on the clip.
- **An AskNews text with last year's results.** Opus moved its forecast
  that Arizona wins the 2026 NCAA men's tournament from 0.07 to exactly 0.
  Its reasoning cites a snippet saying Arizona lost to Duke in the Sweet 16.
  That snippet is the AskNews text of an NCAA.com bracket page dated
  2026-01-28, which describes the 2025 tournament's results with 2026
  dates. The page is dated before the freeze (2026-03-06), so the leakage
  audit passes it (see [Step 3](#step-3-evidence)). Arizona did not win, so
  the move counts as right. It is small (Δ² ≈ 0.005), so it barely changes
  any result. Haiku, reading the same text, moved from 0.04 to 0.01.
