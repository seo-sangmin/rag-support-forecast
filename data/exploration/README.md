# Exploration run

The exploration finished on November 20, 2026. Both models forecast the
same 297 questions. Their outcomes were examined to recheck the pilot's
patterns and inform test planning, so these questions are excluded from
the preregistered test. See the [results](#results).

## Setup

- **Models:** `claude-haiku-4-5-20251001` (main) and Opus 4.5 (second
  model), both at temperature 0 with the pilot's prompts.
- **Evidence:** up to 10 AskNews archive articles from the 60 days before
  each question's freeze, as in the pilot.
  Both models read the same saved search results. AskNews's terms do not
  allow sharing them, so they stay out of the repo. Their SHA-256
  fingerprints are in `data/cache/asknews_sha256.txt`. Running
  `shasum -a 256 data/cache/*/retrieval/asknews/*.json > data/cache/asknews_sha256.txt`
  and then `git diff` shows any changed, added or missing search.
- **Questions:** ForecastBench files from commit `fe2a073` (nightly update
  of 2026-11-15), saved in `data/raw/` so that later updates cannot change
  them.

## Questions (`questions.csv`)

Drawn once by `scripts/draw_questions.py` with Python's `random.Random(0)`,
in this order:

1. 2026-03-15, dataset questions: 15 per source (acled, dbnomics, fred,
   wikipedia, yfinance), each drawn with `sample` from the source's usable
   ids sorted as text.
2. 2026-03-15, market questions: all 157, sorted by (source, id) and then
   shuffled. The first 20 go to batch 1 and the rest to batch 2.
3. 2026-10-11, dataset questions: 15 per source from acled, dbnomics, fred
   and yfinance. Serpapi is skipped because the analysis does not treat it
   as a dataset source yet.
4. 2026-10-11, market questions: 5 of the 44 Kalshi questions that appear on
   no test date.

| batch | question set | questions | distinct saved searches |
| --- | --- | --- | --- |
| 1 | 2026-03-15 | 75 dataset + 20 market | 94 |
| 2 | 2026-03-15 | 137 market | 137 |
| 3 | 2026-10-11 | 60 dataset + 5 Kalshi market | 65 |

Two March FRED series (`WALCL` and `RESPPANWW`) used the same question text
and freeze time, so they shared a saved search. The 297 questions used 296
distinct saved searches. The date audits checked 2,267 article entries in
March and 640 in October, counting each article each time a question used
it. All 2,907 had readable publication dates on or before the corresponding
freeze. [March audit](../results/leakage_20261120T033022Z.json) ·
[October audit](../results/leakage_20261120T033043Z.json).

Batch 3 lies outside the planned test window. Its four dataset sources add
five families because the October FRED questions have two resolution dates.

## How to check

The files in `data/raw/` come from ForecastBench's data repository at commit
[`fe2a073`](https://github.com/forecastingresearch/forecastbench-datasets/commit/fe2a07344bf835fc44356c8f497a7542e8a58f94)
(its nightly update of 2026-11-15). One command checks both these files and
the list:

```bash
python scripts/draw_questions.py exploration
git status --short data/exploration/questions.csv
```

The script downloads every ForecastBench file it needs from that commit (46
files, under 40 MB) into a temporary folder. It stops with a message if a copy
in `data/raw/` differs from the downloaded file. Otherwise it redraws the
list, and if `git status` then prints nothing, the redrawn list is identical
to the saved one. Both checks passed on 2026-11-17.

## Running

```bash
python scripts/run_experiment.py --question-sets 2026-03-15 --questions data/exploration/questions.csv --batch 1
python scripts/run_experiment.py --question-sets 2026-03-15 --questions data/exploration/questions.csv --batch 2 --resume-from data/results/run_<batch 1 timestamp>.csv
python scripts/run_experiment.py --question-sets 2026-10-11 --questions data/exploration/questions.csv --batch 3 --resume-from data/results/run_<batch 2 timestamp>.csv
```

Each batch resumes from the previous batch's file, so the batch 3 file holds
all 297 questions.
Keep the code, prompts and settings the same across batches. A later run on
the same questions, such as Opus 4.5 or a rerun after a bug fix, reuses the
saved search results without new searches.

For Opus 4.5, add `--model claude-opus-4-5-20251101` to each command above
and run it in the same folder as the Haiku batches, where the saved search
results are. Its batches 2 and 3 must resume from its own batch 1 and batch 2
files, because `--resume-from` matches finished questions by id, source and
freeze date, not by model.

The final files are `data/results/run_20261120T025349Z.csv` (Haiku 4.5) and
`data/results/run_20261120T030940Z.csv` (Opus 4.5), each with its two summary
files (`_summary.json` and `_drop_maybe_settled_summary.json`).

## Answers already public at the freeze

A question can be settled before its freeze. In the pilot, San Diego FC had
clinched its playoff berth before the freeze (see
[DETAILS.md](../../DETAILS.md#pilot-results)). No test question is checked
by hand. Instead, `scripts/analyze_results.py` is run twice on each results
file, once as usual and once with `--drop-maybe-settled`. The second run
writes its own summary file ending in `_drop_maybe_settled_summary.json`
and leaves out two kinds of questions:

1. Every market question whose crowd price at the freeze was 0.05 or less or
   0.95 or more.
2. Every ACLED question. ACLED questions count events in the 30 days before
   the resolution date, and that window starts before the freeze (13 of its
   30 days in the pilot, 14 in the 2026-03-15 set and 21 in the 2026-10-11
   set). So events before the freeze can already decide a YES. Finding out
   which ones were decided would need ACLED's daily event counts, so all of
   them are left out.

Both values of H are reported.

The cutoff 0.05 was chosen on 2026-11-18 by checking the 42 markets in the
pilot and in this list whose price was more than 0.03 and at most 0.10 from
0 or 1 ([`settled_check.csv`](settled_check.csv)). The check was done by an
AI model (Claude Opus 5.5 with web search), not by a person. It compared
each market with news and data dated before its freeze, without opening any
forecast or looking at H. One was settled: China's rebar failure rate
(Manifold), whose answer was in a government report of 2026-02-13 while its
price sat 0.0426 from 1. Two more had strong news before the freeze but were
decided by numbers published after it, so they count as open. The 3 settled
pilot markets sat 0.001, 0.01 and 0.0201 from 0 or 1. So 0.05 is the
smallest round cutoff that catches all 4 settled markets.

## Results

A positive gain means the forecast with evidence scored better on average.
Brackets give 95% family bootstrap intervals. Mean gains use every question
in the row. The H and SQ3 analyses use only forecasts that changed.
The screen removed 30 ACLED questions and 44 markets with an extreme crowd
price. Each sample link opens its saved analysis.

| Model | Sample | Questions | Forecasts changed | Mean Brier gain [95% CI] | Mean log loss gain [95% CI] |
| --- | --- | ---: | ---: | --- | --- |
| Haiku 4.5 | [Full](../results/run_20261120T025349Z_summary.json) | 297 | 243 | +0.007 [−0.015, +0.032] | +0.035 [−0.060, +0.162] |
| Haiku 4.5 | [Screened](../results/run_20261120T025349Z_drop_maybe_settled_summary.json) | 223 | 193 | +0.005 [−0.023, +0.035] | +0.039 [−0.082, +0.208] |
| Opus 4.5 | [Full](../results/run_20261120T030940Z_summary.json) | 297 | 224 | +0.012 [−0.006, +0.030] | +0.026 [−0.023, +0.075] |
| Opus 4.5 | [Screened](../results/run_20261120T030940Z_drop_maybe_settled_summary.json) | 223 | 165 | +0.008 [−0.016, +0.032] | +0.015 [−0.052, +0.078] |

**H.** The pilot estimated positive gaps for all six measures on both
scores. That pattern did not repeat. Each cell below gives the top half
minus low half gap for Brier (λ̂) and log loss (c\*), in that order.
H requires both intervals for a measure to lie above zero. No measure met
that rule in any column.

| Measure | Haiku full | Haiku screened | Opus full | Opus screened |
| --- | ---: | ---: | ---: | ---: |
| Δ² | −0.15 / −0.02 | −0.30 / −0.12 | −1.45 / −0.93 | −0.72 / −0.54 |
| KL | −0.60 / −0.48 | −0.73 / −0.56 | −1.33 / −1.05 | −0.95 / −0.77 |
| UR_B | +0.18 / −0.39 | +0.13 / −0.46 | −0.03 / −0.19 | −0.31 / −0.49 |
| UR_L | +0.25 / −0.33 | +0.20 / −0.43 | −0.10 / −0.24 | −0.31 / −0.49 |
| \|Z\| | +0.01 / +0.17 | −0.36 / −0.07 | −0.61 / −0.39 | −0.45 / −0.39 |
| \|KO\| | −0.26 / −0.22 | +0.12 / +0.25 | −1.06 / −1.17 | −1.18 / −1.41 |

For Opus, the full sample's Brier gaps for Δ² and KL were below zero even
at the upper ends of their intervals, [−2.86, −0.18] and [−2.71, −0.01].
After screening, both intervals included zero.

* **SQ1, score improvement.** On all questions, the two uncertainty
  reduction measures (UR_B and UR_L) had positive Spearman rank correlations
  with both score gains for both models, from 0.32 to 0.39. After screening,
  they ranged from 0.20 to 0.29. Each of these intervals lay above zero.
* **SQ2, move size.** In the highest ranked quarter for each measure on the
  full sample, both fitted scales were below 1 for both models. A smaller
  move would have scored better for those groups on these outcomes. In the
  pilot, the corresponding estimates had been close to 1.
* **SQ3, choosing when to keep the prior.** When each source was held out
  in turn, every interval for the rule's gain over always using the
  forecast with evidence included zero, for both models and both samples.

The bootstrap grouped the 135 dataset questions into 10 families by source
and resolution day. It treated each of the 162 market questions as its own
family. Some markets depend on the same event, so the intervals may
understate uncertainty.

## What remains before preregistration

- Dataset questions per source in the test, 15 or 20, from the family
  correlation and the spread, not from whether H passes here.
- The power for each model, by rerunning `scripts/h_power.py` once it counts
  test questions instead of whole dates.
- Which of the two values of H (see the previous section) decides whether H
  passes.
- How to treat linked markets. Kalshi often lists several contracts that one
  number decides (one per threshold), and some Polymarket questions come in
  pairs about one event. The analysis counts each market as its own event,
  which would make its intervals too narrow, so the choice is one family per
  event in the analysis or one contract per event in the test draw.

**Planned test (for reference):** every ForecastBench question set from
2025-12-07 to 2026-09-27 except 2026-03-15, each market question once on its
first date (none from the pilot or this exploration), and 15 or 20 dataset
questions per source per date. The test forecasts should be made by early
January 2027, while both models are still available.
