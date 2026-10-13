# References

Works behind the methods in the [README](README.md). Step numbers refer to
its [Method](README.md#method) section, and names in backticks are its
belief-shift measure keys.

## Forecasting and scoring rules

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

## Confirmation measures

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

## Statistics

- Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *Annals
  of Statistics*, 7(1), 1–26. <https://doi.org/10.1214/aos/1176344552> — the
  bootstrap.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*.
  Chapman & Hall. <https://doi.org/10.1201/9780429246593> — Ch. 13, the
  percentile interval used for the CIs (Method step 7).

## Related work

- Halawi, D., Zhang, F., Yueh-Han, C., & Steinhardt, J. (2024). Approaching
  human-level forecasting with language models. *Advances in Neural
  Information Processing Systems*, 37, 50426–50468.
  <https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a5acfd0876c940d81619c1dc60e7748-Abstract-Conference.html>
  — a retrieval-augmented LLM forecasting system that nears the human crowd
  aggregate.
- Tabet, A. N., & Luštrek, M. (2026). When does evidence help prompted LLM
  forecasting? Evidence access and prompt structure across 12 models.
  *ICML 2026 Workshop: Forecasting as a New Frontier of Intelligence*.
  <https://openreview.net/forum?id=YnNHhcgORk> — closed-book vs.
  AskNews-evidence forecasts on ForecastBench across 12 models.
