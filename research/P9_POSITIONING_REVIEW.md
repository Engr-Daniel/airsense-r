# Focused positioning review — 29 October 2026

This audit supports cautious positioning, not a claim of exhaustive novelty.
The accepted primary study is unchanged. The target-history checkpoint is
post-results and has no accepted real-data outcomes yet.

## Closest decision-support study

Semper, Curado, Vicent and Tortosa, *A practical decision-support system for
robust post-training model selection in spatiotemporal forecasting*,
Knowledge-Based Systems 351, 116673 (2026), DOI
[10.1016/j.knosys.2026.116673](https://doi.org/10.1016/j.knosys.2026.116673).
The publisher abstract describes fixed predictions evaluated against perturbed
references, seed-calibrated regret, validation-based rule comparison and
budget-dependent deployment decisions. Its datasets include PM2.5. Neither
selection regret nor an air-quality application differentiates AirSense-R alone.

The [author overview](https://marcsemperlloret.com/publications/robust-post-training-model-selection/)
reports online publication on 23 July; the publisher issue record is dated
9 October. Do not imply this work first became available after our protocol.

The linked [public minimal implementation](https://github.com/MarcSemperLloret/Decision-Support-Protocol-for-Spatiotemporal-Forecasting)
was inspected at method level. In `src/paper1_minimal/experiment.py`,
`build_prediction_bundles` predicts from clean context once;
`evaluate_condition_rows` compares those predictions with different reference
windows. The README identifies this as a synthetic demonstration. It is not
evidence that the complete journal experiment has been reproduced or inspected.
The journal full text could not be retrieved in this review; obtain and check it
before making a stronger distinction about its complete experimental coverage.

| Dimension | Semper et al.: verified abstract / minimal code | AirSense-R |
|---|---|---|
| Perturbed object | Evaluation reference; predictions reused | Chronological input observations; predictions recomputed |
| Model-choice question | Diagnose uncertainty and compare robust rules | Consequences of retaining a frozen validation choice |
| Spatial evaluation | Do not infer full paper design from minimal code | Twelve chronological LOSO folds; local history available |
| Practical interpretation | Seed-calibrated regret and performance budget | Original 1 µg/m³ near-tie/simplicity rule, paired calendar intervals |

These are supported differences in the inspected material, not proof of a
unique method or superiority. AirSense-R does not validate an adaptive policy.

## Closest air-quality work

- [Alvarado-Alcon et al. (2026)](https://doi.org/10.3390/jsan15040052)
  explicitly covers sparse networks, cross-location forecasting and missing
  data. These are overlapping problems, not unoccupied research territory.
  The publisher metadata/abstract and earlier repository review support that
  statement; full HTML/XML access was rate-limited during this follow-up.
- [Liu et al. (2024)](https://experts.illinois.edu/en/publications/pm25-forecasting-under-distribution-shift-a-graph-learning-approa/)
  compares graph and non-graph forecasters under temporal distribution shift.
  AirSense-R instead emphasizes a fixed selection decision across input stress
  and station exclusion. This comparison is supported by the institutional
  journal abstract; it does not establish absence of regret elsewhere in the paper.
- The [2021 precursor](https://graph-learning-benchmarks.github.io/assets/papers/glb2021/A_New_Benchmark_of_Graph_Learning_for_PM2.5.pdf)
  explicitly contrasts chronological and randomized timestamp splits. We do
  not adopt random splitting as a deployment evaluation or add new architectures.

## Defensible contribution wording

AirSense-R evaluates the cost of retaining an accuracy-and-simplicity choice
under declared input-observation interventions and within-city station
exclusion, with matched targets, paired uncertainty and preserved evidence.
The post-results checkpoint probes the protected target-history assumption and
tolerance dependence. Its results must be reported regardless of direction.

Do not claim the first use of selection regret, the first air-quality robustness
study, a novel forecasting architecture, or an operational fallback strategy.
Complete the journal full-text and forward/backward citation checks before
submission. A reproducible empirical contribution is the intended positioning.
