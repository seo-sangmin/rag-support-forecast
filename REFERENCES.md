# References

Works behind the methods and motivation in the [README](README.md) and
[DETAILS.md](DETAILS.md). Step numbers refer to the README's
[Method](README.md#method) section, and names in backticks are its measure
keys (step 6).

## Forecasting and scoring rules

- Karger, E., Bastani, H., Yueh-Han, C., Jacobs, Z., Halawi, D., Zhang, F., &
  Tetlock, P. E. (2025). ForecastBench: A dynamic benchmark of AI forecasting
  capabilities. *International Conference on Learning Representations
  (ICLR)*. <https://arxiv.org/abs/2409.19839>. The question sets (Method
  step 1).
- Brier, G. W. (1950). Verification of forecasts expressed in terms of
  probability. *Monthly Weather Review*, 78(1), 1–3.
  <https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2>. The
  Brier score.
- Good, I. J. (1952). Rational decisions. *Journal of the Royal Statistical
  Society: Series B*, 14(1), 107–114.
  <https://doi.org/10.1111/j.2517-6161.1952.tb00104.x>. The logarithmic
  score (log loss).
- Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules,
  prediction, and estimation. *Journal of the American Statistical
  Association*, 102(477), 359–378.
  <https://doi.org/10.1198/016214506000001437>. Expected score = entropy +
  divergence (Section 2.2). The four expected-improvement measures in Method
  step 6 follow from it.
- Shannon, C. E. (1948). A mathematical theory of communication. *Bell System
  Technical Journal*, 27(3), 379–423.
  <https://doi.org/10.1002/j.1538-7305.1948.tb01338.x>. Entropy H, behind
  `ur_log`.
- Kullback, S., & Leibler, R. A. (1951). On information and sufficiency.
  *Annals of Mathematical Statistics*, 22(1), 79–86.
  <https://doi.org/10.1214/aoms/1177729694>. KL divergence (`kl`).
- Jeffreys, H. (1946). An invariant form for the prior probability in
  estimation problems. *Proceedings of the Royal Society of London. Series
  A*, 186(1007), 453–461. <https://doi.org/10.1098/rspa.1946.0056>. The
  symmetric divergence KL(p‖q) + KL(q‖p). For a binary forecast it equals
  Δ·Δlogit, the size of a move under log loss in the README's key terms.

## Confirmation measures

- Kemeny, J. G., & Oppenheim, P. (1952). Degree of factual support.
  *Philosophy of Science*, 19(4), 307–324. <https://doi.org/10.1086/287214>.
  The Kemeny–Oppenheim measure (`abs_ko`).
- Crupi, V., Tentori, K., & Gonzalez, M. (2007). On Bayesian measures of
  evidential support: Theoretical and empirical issues. *Philosophy of
  Science*, 74(2), 229–252. <https://doi.org/10.1086/520779>. The
  Crupi–Tentori measure Z (`abs_z`).
- Crupi, V., & Tentori, K. (2016). Confirmation theory. In A. Hájek & C.
  Hitchcock (Eds.), *The Oxford Handbook of Probability and Philosophy*
  (pp. 650–665). Oxford University Press.
  <https://doi.org/10.1093/oxfordhb/9780199607617.013.33>
  ([PDF](https://www.vincenzocrupi.com/website/wp-content/uploads/2017/02/CrupiTentori_OxfordHandbook2016.pdf)).
  Survey of confirmation measures.
- Fitelson, B. (2021). A problem for confirmation measure Z. *Philosophy of
  Science*, 88(4), 726–730. <https://doi.org/10.1086/713920>. A critique of Z.

## Belief updating

- Augenblick, N., & Rabin, M. (2021). Belief movement, uncertainty reduction,
  and rational updating. *Quarterly Journal of Economics*, 136(2), 933–985.
  <https://doi.org/10.1093/qje/qjaa043>. For a Bayesian, expected movement
  (squared belief change, `delta_sq`) equals expected uncertainty reduction
  (drop in π(1 − π), `ur_brier`) (Proposition 1). The paper also names the
  KL and entropy pair (`kl`, `ur_log`).
- Coibion, O., & Gorodnichenko, Y. (2015). Information rigidity and the
  expectations formation process: A simple framework and new facts.
  *American Economic Review*, 105(8), 2644–2678.
  <https://doi.org/10.1257/aer.20110306>. Regresses the forecast error on the
  forecast revision. For y − q on Δ with no intercept, that slope is λ̂ − 1,
  so their underreaction (slope above 0) is λ̂ > 1 (Method step 8).
- Bordalo, P., Gennaioli, N., Ma, Y., & Shleifer, A. (2020). Overreaction in
  macroeconomic expectations. *American Economic Review*, 110(9), 2748–2782.
  <https://doi.org/10.1257/aer.20181219>. The same regression for individual
  forecasters finds overreaction (λ̂ < 1 in the README's terms).
- Augenblick, N., Lazarus, E., & Thaler, M. (2025). Overinference from weak
  signals and underinference from strong signals. *Quarterly Journal of
  Economics*, 140(1), 335–401. <https://doi.org/10.1093/qje/qjae032>. People
  overinfer from weak signals and underinfer from strong ones. H's Δ² gap
  asks the same of an LLM's small and large moves (Method step 9).

## Statistics and study design

- Efron, B. (1979). Bootstrap methods: Another look at the jackknife. *Annals
  of Statistics*, 7(1), 1–26. <https://doi.org/10.1214/aos/1176344552>. The
  bootstrap.
- Efron, B., & Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*.
  Chapman & Hall. <https://doi.org/10.1201/9780429246593>. Ch. 13, the
  percentile interval used for the CIs (Method step 7).
- Field, C. A., & Welsh, A. H. (2007). Bootstrapping clustered data.
  *Journal of the Royal Statistical Society: Series B*, 69(3), 369–390.
  <https://doi.org/10.1111/j.1467-9868.2007.00593.x>. Resampling whole
  clusters, as the CIs do with families (Method step 7).
- Cameron, A. C., & Miller, D. L. (2015). A practitioner's guide to
  cluster-robust inference. *Journal of Human Resources*, 50(2), 317–372.
  <https://doi.org/10.3368/jhr.50.2.317>. Inference with clusters needs many
  clusters, not just many rows. Behind the "one forecast date" limit in
  [DETAILS.md](DETAILS.md#limits), where just 5 shared events decided the 67
  dataset questions.
- Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J.,
  Guillera-Arroita, G., Hauenstein, S., Lahoz-Monfort, J. J., Schröder, B.,
  Thuiller, W., Warton, D. I., Wintle, B. A., Hartig, F., & Dormann, C. F.
  (2017). Cross-validation strategies for data with temporal, spatial,
  hierarchical, or phylogenetic structure. *Ecography*, 40(8), 913–929.
  <https://doi.org/10.1111/ecog.02881>. Hold out whole blocks of related
  data, not single rows. SQ3 holds out one source at a time (Method step 10).
- Rubin, M. (2021). When to adjust alpha during multiple testing: A
  consideration of disjunction, conjunction, and individual testing.
  *Synthese*, 199(3–4), 10969–11000.
  <https://doi.org/10.1007/s11229-021-03276-4>. Alpha needs adjusting only
  when any one passing test would support the claim (disjunction testing).
  It does not when every test must pass (conjunction testing), as H's two
  gaps must, or when each test answers its own question (individual
  testing), as each of the six measures does. See
  [What H tests](DETAILS.md#what-h-tests) and
  [Testing six measures](DETAILS.md#testing-six-measures) in DETAILS.md.
- Lakens, D. (2022). Sample size justification. *Collabra: Psychology*,
  8(1), 33267. <https://doi.org/10.1525/collabra.33267>. Ways to justify a
  sample size, such as a power analysis for the smallest effect that
  matters. Behind the gap that matters (1.0) and the test dates table in
  [DETAILS.md](DETAILS.md#power-and-test-dates).
- Nosek, B. A., Ebersole, C. R., DeHaven, A. C., & Mellor, D. T. (2018). The
  preregistration revolution. *Proceedings of the National Academy of
  Sciences*, 115(11), 2600–2606. <https://doi.org/10.1073/pnas.1708274114>.
  A hypothesis generated from some data is not tested by that same data, so
  preregistration fixes the questions and analysis plan before the outcomes
  are seen. Behind the README's [Stages](README.md#stages): the pilot shaped
  H, so it cannot test H.

## Related work

- Halawi, D., Zhang, F., Yueh-Han, C., & Steinhardt, J. (2024). Approaching
  human-level forecasting with language models. *Advances in Neural
  Information Processing Systems*, 37, 50426–50468.
  <https://proceedings.neurips.cc/paper_files/paper/2024/hash/5a5acfd0876c940d81619c1dc60e7748-Abstract-Conference.html>.
  Retrieval improves average Brier score. The source for the README's
  opening claim.
- Yuan, Z., Ding, Z., & Vlachos, A. (2025). Do language models update their
  forecasts with new information? *arXiv preprint* arXiv:2509.23936.
  <https://arxiv.org/abs/2509.23936>. Introduces EvolveCast: given news from
  after their training cutoff, LLMs often move the right way but much less
  than human forecasters. SQ2 (B) asks whether moves were the right size.
- He, Z., Qiu, T., Shirado, H., & Sap, M. (2025). Martingale Score: An
  unsupervised metric for Bayesian rationality in LLM reasoning. *Advances
  in Neural Information Processing Systems (NeurIPS)*.
  <https://openreview.net/forum?id=BfO6od6JD6>. Regresses an LLM's belief
  update on its prior, which needs no outcomes, and finds the updates often
  predictable. λ̂ instead regresses the realized error y − p on the update
  Δ.
- Paleka, D., Goel, S., Geiping, J., & Tramèr, F. (2026). Pitfalls in
  evaluating language model forecasters. *International Conference on
  Learning Representations (ICLR)*.
  <https://openreview.net/forum?id=z85kARAoyD>. Search filtered by date and
  stated training cutoffs can leak the future, questions from one period
  share outcome drivers, and keeping only resolved questions skews the
  question mix. See Method steps 2 and 3 and the "one forecast date" and
  "question mix" limits in [DETAILS.md](DETAILS.md#limits).
- Mostafa, H., Shastri, O., & Lee, D. (2026). TimeSeek: Temporal reliability
  of agentic forecasters. *arXiv preprint* arXiv:2604.04220 (workshop paper).
  <https://arxiv.org/abs/2604.04220>. Web search improves every model's
  pooled Brier skill score but hurts in 12% of the model and checkpoint
  pairs. This motivates rules that defer selectively, like SQ3's "keep p"
  rule.
- Tabet, A. N., & Luštrek, M. (2026). When does evidence help prompted LLM
  forecasting? Evidence access and prompt structure across 12 models.
  *ICML 2026 Workshop: Forecasting as a New Frontier of Intelligence*.
  <https://openreview.net/forum?id=YnNHhcgORk>. Closed-book vs.
  AskNews-evidence forecasts on ForecastBench across 12 models.
