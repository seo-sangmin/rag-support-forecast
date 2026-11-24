# rag-support-forecast

Retrieval-augmented forecasting can improve LLM forecasts, but it is unclear
when and why retrieved evidence helps. On binary questions from
[ForecastBench](https://www.forecastbench.org/), this repo asks:

> **For each of six measures of an LLM's belief shift, computed from its
> forecast before (p) and after (q) reading retrieved evidence, does that
> measure tell which of its updates are justified?**

| sub-question | asks |
| --- | --- |
| **SQ1 Prediction** | How strongly is each measure associated with the realized Brier and log-loss improvement? |
| **SQ2 Warrant** | Within one source, are shifts with higher measure values better justified: (A) does q beat p, and (B) was the move the right size? |
| **SQ3 Decision** | On a source it has never seen, does "keep p in the measure groups where q did worse on the other sources" beat always using q? |

**Key terms.** Let Δ = q − p and let y be the outcome (1 or 0). For one
question, λᵢ = (y − p)/Δ is how justified the move was: 1 = right size,
0 = unsupported, < 0 = wrong way. For a group of moves, λ̂ (Brier) and c\*
(log loss) are the one scale that, applied to all its moves, would have
scored best: 1 = right size, < 1 = too large, > 1 = too small.

A question's improvement is (size of the move) × (λᵢ − break-even), with size
2Δ² for Brier and Δ·Δlogit for log loss. So any measure that grows with move
size correlates with improvement (SQ1) even when big moves are no better
justified. SQ2 and SQ3 take the size out.

## Hypothesis (draft)

**H: in each measure's top half, moves are better justified than in its low
half.** For each measure, the questions whose forecast moved are ranked within
their source and cut into 4 groups. The top half pools groups 3 and 4, the low
half groups 1 and 2. H passes for a measure only if both gaps are above 0:

- Brier: λ̂(top half) − λ̂(low half) > 0
- log loss: c\*(top half) − c\*(low half) > 0

A gap counts as above 0 when its 95% bootstrap interval lies above 0 (one
direction at 2.5%). Each measure's result answers its own question, so there
is no correction for testing six. No test compares the measures, so the six
results are not a ranking. Everything else (q vs p overall, SQ1, SQ2 per
group, SQ3) is an estimate with its interval.
[DETAILS.md](DETAILS.md#hypothesis-h) gives the reasons and the power checks.

## Stages

1. **Pilot** (done): 100 of the 348 questions. It shaped H, so it cannot test H.
2. **Exploration run** (done): 297 questions from two later dates, outcomes
   looked at, to recheck the pilot patterns and the power numbers.
3. **Preregistration**: fixes H, its pass rule and the number of test dates
   before any test outcome is seen. It also specifies how to identify
   questions whose answers were already public at the freeze and whether
   to include them in the test sample.
4. **Test run**: the new dates, analyzed once as preregistered.

## Pilot results (exploratory)

100 of the 348 questions (random, seed 0, 8 sources), of which 81 moved. Mean
Brier fell from 0.187 to 0.165 (improvement +0.022 [−0.005, +0.071]) and log
loss from 0.537 to 0.477 (+0.059 [−0.006, +0.177]). q beat p on 31 of the
100. Cells are estimate [95% CI].

**H on the pilot** (each gap is top half minus low half)

| measure | λ̂ gap (Brier) | c\* gap (log loss) | H passes |
| --- | --- | --- | --- |
| Δ² | +1.83 [−1.11, +4.63] | +0.96 [−0.31, +5.19] | no |
| KL | +2.43 [−0.32, +4.75] | +1.12 [+0.08, +6.34] | no |
| UR_B | +1.39 [−0.31, +2.23] | +1.63 [−0.14, +4.62] | no |
| UR_L | +1.45 [−0.31, +2.22] | +1.80 [−0.11, +6.05] | no |
| \|Z\| | +1.21 [−1.36, +4.01] | +1.43 [−0.53, > +50] | no |
| \|KO\| | +1.29 [−0.74, +3.96] | +1.12 [−0.66, +6.48] | no |

Every gap is above 0, but every λ̂ interval includes 0, so H passes for no
measure (> +50: the interval reaches the cap of the c\* search).

- **SQ1:** the size measures (Δ², KL, |Z|, |KO|) have Pearson +0.48 to +0.86,
  carried by about five large moves, but Spearman near 0. UR_B and UR_L are
  +0.39 to +0.49 on both.
- **SQ2:** every top group was about the right size (λ̂ 0.85 to 1.02, c\*
  0.81 to 1.05), and for five measures group 3 looks like group 4.
- **SQ3:** no "keep p" rule is distinguishable from always using q.

**Caveats.** The pilot's original test (Spearman of |Z| with Brier
improvement) fell from 0.21 to 0.05 when only the prompts changed, and all
other analyses were added after that. All forecasts are as of 2025-10-16, and
the 67 dataset questions were decided by just 5 shared events, so the
intervals have only 5 such events to resample. Full tables and limits are in
[DETAILS.md](DETAILS.md#pilot-results).

## Exploration results (exploratory)

297 questions from the 2026-03-15 set (232) and the 2026-10-11 set (65)
([how they were drawn](data/exploration/README.md)), forecast by Haiku 4.5
and by Opus 4.5 from the same evidence. H was written down before this run,
so unlike the pilot, these questions did not shape it. Cells are estimate
[95% CI].

| | Haiku 4.5 | Opus 4.5 |
| --- | --- | --- |
| forecasts that moved | 243 of 297 | 224 of 297 |
| q beat p | 131 of 297 | 134 of 297 |
| mean Brier of p | 0.194 | 0.189 |
| mean Brier of q | 0.186 | 0.177 |
| Brier improvement | +0.007 [−0.015, +0.032] | +0.012 [−0.006, +0.030] |
| log loss improvement | +0.035 [−0.060, +0.162] | +0.026 [−0.023, +0.075] |

**H on the exploration** (each gap is top half minus low half)

| measure | Haiku λ̂ gap | Haiku c\* gap | Opus λ̂ gap | Opus c\* gap |
| --- | --- | --- | --- | --- |
| Δ² | −0.15 [−1.24, +0.40] | −0.02 [−0.92, +0.45] | −1.45 [−2.86, −0.18] | −0.93 [−1.96, +0.14] |
| KL | −0.60 [−1.48, +0.23] | −0.48 [−1.46, +0.27] | −1.33 [−2.71, −0.01] | −1.05 [−2.29, +0.19] |
| UR_B | +0.18 [−0.34, +0.80] | −0.39 [−0.80, +0.53] | −0.03 [−0.70, +0.72] | −0.19 [−0.73, +0.76] |
| UR_L | +0.25 [−0.31, +0.83] | −0.33 [−0.78, +0.58] | −0.10 [−0.74, +0.68] | −0.24 [−0.76, +0.73] |
| \|Z\| | +0.01 [−1.03, +0.77] | +0.17 [−0.69, +0.91] | −0.61 [−1.39, +0.53] | −0.39 [−1.05, +0.51] |
| \|KO\| | −0.26 [−1.17, +0.62] | −0.22 [−1.20, +0.63] | −1.06 [−1.97, +0.02] | −1.17 [−2.47, +0.07] |

H passes for no measure in either model. Unlike the pilot, most gaps are
below 0. For Opus, the λ̂ gap's interval lies entirely below 0 for Δ² and
KL: its small moves were better justified than its large ones. Leaving out
the 74 questions whose answer may have been public at the freeze, H again
passes for no measure ([DETAILS.md](DETAILS.md#exploration-results)).

- **SQ1:** the size measures' Pearson is near 0 (−0.12 to +0.21, except
  +0.71 for Haiku's KL under log loss, which one question carries), and
  their Spearman is +0.10 to +0.27. UR_B and UR_L keep a positive Spearman
  (+0.32 to +0.39, every interval above 0), but their Pearson is −0.25 to
  +0.01.
- **SQ2:** every top group's moves were too large (λ̂ 0.38 to 0.80, c\* 0.30
  to 0.69), where the pilot's were about the right size.
- **SQ3:** again no "keep p" rule is distinguishable from always using q.

**Caveats.** Two answers stand out. Haiku gave Cooper Flagg winning the NBA
Rookie of the Year award for the 2025 to 2026 season a prior of exactly 0,
because it thought he had been drafted in 2024. He won, and since r is
clipped at 1e-6 (Method step 5), this one question carries Haiku's log loss
result: without it, the mean improvement is −0.011. Opus moved Arizona's
chance of winning the 2026 NCAA tournament from 0.07 to 0 after the AskNews
text of an article dated January 2026 gave the 2025 tournament's results
with 2026 dates. A date check cannot catch that. The forecasts are as of two
dates (2026-03-06 and 2026-10-09), and the 135 dataset questions were
decided by only 10 shared events.

## Method

1. **Questions:** binary questions from ForecastBench's question and
   resolution sets, one row per `(id, source)` on each date. The pilot draws
   from the 348 dated 2025-10-26, and the exploration uses the 297 in
   `data/exploration/questions.csv` (sets dated 2026-03-15 and 2026-10-11).
2. **Prior p:** `claude-haiku-4-5-20251001` at temperature 0, from the
   question, resolution criteria and background, as of `freeze_datetime`.
   Anthropic reports a July 2025 training-data cutoff for this model. The
   exploration also uses `claude-opus-4-5-20251101` (August 2025 cutoff) as
   a second model, for both p and q.
3. **Evidence:** the top 10 AskNews results from the 60 days before
   `freeze_datetime`. The audit verified that all 927 cached pilot articles,
   and all cached exploration articles, were dated on or before the freeze
   for their question.
4. **Posterior q:** the same model and date, with the evidence added.
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

   Δ² ranks questions like the difference |q − p|, and |KO| like the log
   likelihood ratio |logit q − logit p|, so each pair gives the same results
   except SQ1's Pearson.
7. **SQ1:** Pearson and Spearman correlation of each measure with each
   improvement. All CIs are 95% percentile bootstrap intervals (10,000
   resamples) over **families**: dataset questions (acled, dbnomics, fred,
   wikipedia, yfinance) with the same source and resolution day share one
   deciding event, so they form one family. Each market question is its own.
8. **SQ2:** use the questions whose forecast moved (Δ ≠ 0). For each measure,
   rank them within their own source, cut each source into 4 groups
   (1 = lowest), and pool group g across sources, so every group has the same
   source mix. Per group: *achieved* = mean improvement (A), and λ̂ and c\* (B).
9. **H:** pool groups 3 and 4 (top half) and groups 1 and 2 (low half), compute
   λ̂ and c\* over each half's moves, and take top minus low. Each gap gets a
   95% family bootstrap interval, with the groups rebuilt in each resample.
10. **SQ3:** hold out one source at a time. Mark group g "keep p" if its mean
    improvement on the other sources is below 0, and apply the marks to the
    held out source. D = mean score(always q) − score(rule), so D > 0 means
    the rule wins.

## Running the code

```bash
python -m venv .venv  # needs Python 3.11+
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in ANTHROPIC_API_KEY and ASKNEWS_API_KEY
python scripts/run_experiment.py --question-sets 2025-10-26 --max-questions 5  # smoke test; --help lists all flags
python scripts/analyze_results.py data/results/run_<timestamp>.csv  # writes run_<timestamp>_summary.json (~5 min)
python scripts/audit_leakage.py  # offline: flag cached evidence dated after each freeze
pytest -q
```

`run_experiment.py --random --seed N` samples questions, and
`--resume-from <csv>` adds questions to an earlier run. To keep the pilot out
of the SQ3 test, pass `--train-only data/results/run_20260914T104832Z.csv` to
the analysis. LLM and AskNews calls are cached under `data/cache/`, so reruns
are free. The AskNews cache is not in this repo, because AskNews's terms do not
allow sharing its results.

Each run writes `run_<timestamp>.csv` (one row per question, `p_h` = p,
`p_he` = q, with reasoning) and `run_<timestamp>.meta.json` (seed, flags,
model, retrieval settings, selected and failed questions). The analysis writes
`run_<timestamp>_summary.json` (`correlations` SQ1, `all_moved` all moves
pooled, `warrant` SQ2, `hypothesis` H, `decision` SQ3, `ci_method`).
`data/archive/` keeps the July
2026 runs made with earlier prompts. The code is in `src/rag_forecast/` (data,
retrieval, prompts, forecasting, pipeline, metrics, audit, cache, rate_limiter,
config).

## References

Full citations are in [REFERENCES.md](REFERENCES.md). Data and tools:
[ForecastBench](https://www.forecastbench.org/),
[its datasets](https://github.com/forecastingresearch/forecastbench-datasets),
[AskNews Python SDK](https://github.com/emergentmethods/asknews-python-sdk).
