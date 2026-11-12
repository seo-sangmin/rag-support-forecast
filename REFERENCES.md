# References

Step numbers refer to the [README method](README.md#method). The project’s
warrant estimates, hypothesis H and power calculation are defined in
[DETAILS.md](DETAILS.md).

## Forecasting and scoring rules

- Karger, E., Bastani, H., Yueh-Han, C., Jacobs, Z., Halawi, D., Zhang, F., &
  Tetlock, P. E. (2025). ForecastBench: A dynamic benchmark of AI forecasting
  capabilities. *International Conference on Learning Representations
  (ICLR)*. The benchmark releases dated question and resolution sets
  (step 1). When a question recurs, this project keys its forecast and
  retrieved evidence by `(id, source, freeze_datetime)`.
  [Paper](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea74e45a229dac70b5b63b28d8934db6-Abstract-Conference.html)
  · [ForecastBench datasets](https://github.com/forecastingresearch/forecastbench-datasets)
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
  <https://doi.org/10.1198/016214506000001437> — expected score = entropy +
  divergence (Section 2.2); the four expected-improvement measures in Method
  step 6 follow from it.
- Shannon, C. E. (1948). A mathematical theory of communication. *Bell System
  Technical Journal*, 27(3), 379–423.
  <https://doi.org/10.1002/j.1538-7305.1948.tb01338.x> — entropy H, behind
  `ur_log`.
- Kullback, S., & Leibler, R. A. (1951). On information and sufficiency.
  *Annals of Mathematical Statistics*, 22(1), 79–86.
  <https://doi.org/10.1214/aoms/1177729694> — KL divergence (`kl`).
- Jeffreys, H. (1946). An invariant form for the prior probability in
  estimation problems. *Proceedings of the Royal Society of London, Series A*,
  186(1007), 453–461. For binary forecasts, the symmetric divergence
  KL(q‖p) + KL(p‖q) equals Δ·(logit q − logit p), the move-size factor in
  the README’s log-loss decomposition. <https://doi.org/10.1098/rspa.1946.0056>

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
  (pp. 650–665). Oxford University Press. The survey describes the probability
  difference and likelihood ratio measures. Step 6 shows why their magnitudes
  (using the log likelihood ratio) rank moves like `delta_sq` and `abs_ko`,
  respectively. [Matching measures](DETAILS.md#step-6-measures)
  <https://doi.org/10.1093/oxfordhb/9780199607617.013.33>
  ([PDF](https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf))
- Fitelson, B. (2021). A problem for confirmation measure Z. *Philosophy of
  Science*, 88(4), 726–730. <https://doi.org/10.1086/713920> — a critique of Z.

## Belief updating and forecast revisions

- Augenblick, N., & Rabin, M. (2021). Belief movement, uncertainty reduction,
  and rational updating. *Quarterly Journal of Economics*, 136(2), 933–985.
  For a Bayesian update, squared movement and the drop in p(1 − p) are equal
  in expectation (Proposition 1). These are `delta_sq` and `ur_brier` for one
  update. The authors also discuss the KL and entropy pair.
  <https://doi.org/10.1093/qje/qjaa043>
- Coibion, O., & Gorodnichenko, Y. (2015). Information rigidity and the
  expectations formation process: A simple framework and new facts.
  *American Economic Review*, 105(8), 2644–2678. They regress forecast errors
  on revisions. In SQ2’s notation, the slope of y − q on Δ = q − p, fitted
  without an intercept, is exactly λ̂ − 1. <https://doi.org/10.1257/aer.20110306>
- Bordalo, P., Gennaioli, N., Ma, Y., & Shleifer, A. (2020). Overreaction in
  macroeconomic expectations. *American Economic Review*, 110(9), 2748–2782.
  Using forecast errors and revisions, they find that individual forecasters
  typically overreact to news and consensus forecasts underreact.
  <https://doi.org/10.1257/aer.20181219>
- Hahn, U., Merdes, C., & von Sydow, M. (2018). How good is your evidence
  and how would you know? *Topics in Cognitive Science*, 10(4), 660–678.
  Their simulations use Brier scores to measure what happens to posterior
  accuracy when an agent misjudges how diagnostic its evidence is.
  <https://doi.org/10.1111/tops.12374>
- Augenblick, N., Lazarus, E., & Thaler, M. (2025). Overinference from weak
  signals and underinference from strong signals. *Quarterly Journal of
  Economics*, 140(1), 335–401. They study how overreaction and underreaction
  vary with signal strength. SQ2 groups forecasts by the model’s observed
  belief shift. <https://doi.org/10.1093/qje/qjae032>
- Cox, D. R. (1958). Two further applications of a model for binary
  regression. *Biometrika*, 45(3–4), 562–565. Cox’s calibration slope fits
  forecast log odds to outcomes. SQ2 fixes logit p as an offset and fits c\*
  only to the change in log odds, logit q − logit p (step 8).
  <https://doi.org/10.1093/biomet/45.3-4.562>
- Albert, A., & Anderson, J. A. (1984). On the existence of maximum
  likelihood estimates in logistic regression models. *Biometrika*, 71(1),
  1–10. Complete separation explains why c\* has no finite optimum when
  every move points toward its outcome or every move points away. SQ2 caps
  the search at ±50. <https://doi.org/10.1093/biomet/71.1.1>

## Statistics

- Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *Annals
  of Statistics*, 7(1), 1–26. <https://doi.org/10.1214/aos/1176344552> — the
  bootstrap.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*.
  Chapman & Hall. <https://doi.org/10.1201/9780429246593> — Ch. 13, the
  percentile interval used for the CIs (Method step 7).
- Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data.
  *Journal of the Royal Statistical Society: Series B*, 69(3), 369–390.
  Resampling intact clusters preserves dependence within them. The project
  draws whole question families for its intervals (steps 7–10).
  <https://doi.org/10.1111/j.1467-9868.2007.00593.x>
- Cameron, A. C., & Miller, D. L. (2015). A practitioner’s guide to
  cluster-robust inference. *Journal of Human Resources*, 50(2), 317–372.
  Few independent clusters limit inference. In the pilot, five shared
  events decided all 67 dataset questions. <https://doi.org/10.3368/jhr.50.2.317>
- Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J.,
  Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B.,
  Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F.
  (2017). Cross-validation strategies for data with temporal, spatial,
  hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.
  They describe choosing validation blocks to match where a prediction
  will be used. SQ3 learns the “keep p” rule on the other sources and tests
  it on the held-out source (step 10). <https://doi.org/10.1111/ecog.02881>

## Hypothesis and power

- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018).
  The preregistration revolution. *Proceedings of the National Academy of
  Sciences*, 115(11), 2600–2606. They distinguish using observations to form
  a hypothesis from testing it on fresh data. The pilot informed H and its
  within-source median split. The project plans to preregister the test
  before examining its outcomes.
  [Study stages](README.md#stages) · <https://doi.org/10.1073/pnas.1708274114>
- Berger, R. L., & Hsu, J. C. (1996). Bioequivalence trials,
  intersection–union tests and equivalence confidence sets. *Statistical
  Science*, 11(4), 283–319. Theorem 1 gives the intersection–union rule used
  for H. For one measure, the Brier and log-loss gaps must each have a
  positive lower 95% interval bound (a nominal one-sided 2.5% test, step 9).
  <https://doi.org/10.1214/ss/1032280304>
- Rubin, M. (2021). When to adjust alpha during multiple testing: A
  consideration of disjunction, conjunction, and individual testing.
  *Synthese*, 199, 10969–11000. The distinction between individual and joint
  claims matters here because H yields a separate conclusion for each of
  the six measures. <https://doi.org/10.1007/s11229-021-03276-4>
- Lakens, D. (2022). Sample size justification. *Collabra: Psychology*,
  8(1), 33267. Planning around a meaningful effect motivates stating the
  target gap before estimating how many test dates it would take to detect
  it. This project chose a gap of 1.0 for both scores.
  [Power and test dates](DETAILS.md#power-and-test-dates) · <https://doi.org/10.1525/collabra.33267>
- Sozu, T., Sugimoto, T., & Hamasaki, T. (2011). Sample size determination
  in superiority clinical trials with multiple co-primary correlated
  endpoints. *Journal of Biopharmaceutical Statistics*, 21(4), 650–668.
  Joint power is the probability that all required tests pass. The project
  uses a bivariate normal approximation for its two gaps and estimates their
  dependence from the family bootstrap. <https://doi.org/10.1080/10543406.2011.551329>
- Kruskal, W. H. (1958). Ordinal measures of association. *Journal of the
  American Statistical Association*, 53(284), 814–861. Under bivariate
  normality, Pearson’s ρ equals 2 sin(πρₛ/6), where ρₛ is Spearman’s
  correlation. The power script applies this conversion to the bootstrap
  gap pairs. [Power script](scripts/h_power.py) · <https://doi.org/10.1080/01621459.1958.10501481>

## Related work

- Halawi, D., Zhang, F., Yueh-Han, C., & Steinhardt, J. (2024). Approaching
  human-level forecasting with language models. *Advances in Neural
  Information Processing Systems*, 37, 50426–50468.
  <https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a5acfd0876c940d81619c1dc60e7748-Abstract-Conference.html>
  — retrieval improves average Brier score; the source for the README's
  opening claim.
- Tabet, A. N., & Luštrek, M. (2026). When does evidence help prompted LLM
  forecasting? Evidence access and prompt structure across 12 models.
  *ICML 2026 Workshop: Forecasting as a New Frontier of Intelligence*.
  <https://openreview.net/forum?id=YnNHhcgORk> — closed-book vs.
  AskNews-evidence forecasts on ForecastBench across 12 models.
- Yuan, Z., Ding, Z., & Vlachos, A. (2026). Do language models update their
  forecasts with new information? *arXiv:2509.23936*, version 3. EvolveCast
  compares revisions after news with human forecast revisions. Models often
  move in the same direction as the human forecasters but by less. SQ2 uses
  resolved outcomes to judge the size of a move. <https://arxiv.org/abs/2509.23936v3>
- He, Z., Qiu, T., Shirado, H., & Sap, M. (2025). Martingale Score: An
  unsupervised metric for Bayesian rationality in LLM reasoning. *Advances
  in Neural Information Processing Systems*, 38. Their score tests whether
  an LLM’s current belief predicts its next revision. It can be computed
  before the outcome is known. <https://doi.org/10.52202/085713-4592>
- Paleka, D., Goel, S., Geiping, J., & Tramèr, F. (2026). Pitfalls in
  evaluating language model forecasters. *International Conference on
  Learning Representations (ICLR)*. They document how future information
  can enter a forecasting evaluation. Here each forecast’s freeze time
  determines which articles it can use (step 3).
  <https://proceedings.iclr.cc/paper_files/paper/2026/hash/b9d69c72e4587ddf3fa6352890aefc4f-Abstract-Conference.html>
- Mostafa, H., Shastri, O., & Lee, D. (2026). TimeSeek: Temporal reliability
  of agentic forecasters. *arXiv:2604.04220*. Web search improved pooled
  Brier skill for every model but lowered it in 12% of model–checkpoint
  pairs. SQ3 asks when to keep the forecast made without retrieved evidence.
  <https://arxiv.org/abs/2604.04220>
