# Exploration run

The exploration run comes before the preregistration (see the README's
[Stages](../../README.md#stages)). It rechecks the pilot's patterns on new
questions and measures the spread that the power calculation needs. Its
outcomes are looked at, so none of its questions can be part of the test.

## Setup

- **Models:** `claude-haiku-4-5-20251001` (main) and Opus 4.5 (second
  model), both at temperature 0 with the pilot's prompts.
- **Evidence:** one AskNews archive search per question, the top 10
  articles from the 60 days before the question's freeze, as in the pilot.
  Both models read the same saved search results. AskNews's terms do not
  allow sharing them, so they stay out of the repo.
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

| batch | question set | questions | searches |
| --- | --- | --- | --- |
| 1 | 2026-03-15 | 75 dataset + 20 market | 95 |
| 2 | 2026-03-15 | 137 market | 137 |
| 3 (optional) | 2026-10-11 | 60 dataset + 5 Kalshi market | 65 |

Batch 3 lies outside the test window, so it costs the test nothing. It adds
4 dataset families and checks the Kalshi questions.

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
python scripts/run_experiment.py --question-sets 2026-10-11 --questions data/exploration/questions.csv --batch 3
```

Keep the code, prompts and settings the same across batches. A later run on
the same questions, such as Opus 4.5 or a rerun after a bug fix, reuses the
saved search results without new searches.

For Opus 4.5, add `--model claude-opus-4-5-20251101` to each command above
and run it in the same folder as the Haiku batches, where the saved search
results are. Its batch 2 must resume from its own batch 1 file, because
`--resume-from` matches finished questions by id, source and freeze date,
not by model.

## What it decides before the preregistration

- Dataset questions per source in the test, 15 or 20, from the family
  correlation and the spread, not from whether H passes here.
- The power for each model, by rerunning `scripts/h_power.py` once it counts
  test questions instead of whole dates.
- What to do with market questions whose answer was already public at the
  freeze.

**Planned test (for reference):** every ForecastBench question set from
2025-12-07 to 2026-09-27 except 2026-03-15, each market question once on its
first date (none from the pilot or this exploration), and 15 or 20 dataset
questions per source per date. The test forecasts should be made by early
January 2027, while both models are still available.
