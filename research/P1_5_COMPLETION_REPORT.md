# P1.5 Completion Report — Methodology Hardening

**Status: COMPLETE**

## Purpose

P1.5 converts the P1 novelty direction into a stricter experimental design before dataset audit and protocol freeze. It responds to methodological review without adding model families or changing the core research question.

## Changes adopted

1. **Validation-based deployment selection**
   - One model will be selected using clean validation MAE.
   - Final test results never determine the selected model.
   - Test-best performance is treated only as a retrospective oracle reference.

2. **Selection regret added as a central outcome**
   - Measures the additional stressed-test MAE paid by retaining the clean-validation-selected model.
   - Prevents trivial rank swaps from being overstated.

3. **Uncertainty made mandatory**
   - Paired temporal-block bootstrap planned for model differences.
   - Shared target rows and shared corruption realizations required.
   - Multiple training/corruption seeds planned where feasible.

4. **Cross-site evaluation strengthened**
   - Primary plan changed from a single held-out station to repeated leave-one-station-out evaluation across all feasible stations.
   - Held-out station data are prohibited from fitting/preprocessing/selection.
   - Recent held-out-station sensor history remains allowable at inference and will be stated explicitly.

5. **Observation corruption made stream-consistent**
   - Corruption is applied to chronological station streams before overlapping windows are built.
   - Future targets stay clean.
   - A small contiguous-outage sensitivity analysis is added.

6. **Noise leakage fixed at design/code level**
   - Noise severity is now based on frozen training-derived scales, never test-set standard deviations.

7. **Pipeline fairness clarified**
   - Models must be evaluated on identical station-timestamp targets.
   - Preprocessing/imputation is part of the evaluated pipeline.
   - A small imputation sensitivity check may be frozen in P3.

8. **Repository hygiene improved**
   - Broad `models/` ignore rule replaced with `/artifacts/models/*` so source model code remains trackable.
   - Additional tests added for corruption, noise scales, temporal splits, station isolation, and selection regret.

## Scope deliberately NOT added

- No new model families.
- No anomaly-detection task.
- No transformers.
- No embedded/Edge deployment claim.
- No claim that public reference-station data represent low-cost embedded sensors.

## Remaining decisions for P2/P3

- exact timestamp split boundaries;
- usable stations and sample coverage;
- final imputation policy;
- practical near-tie threshold;
- block-bootstrap length;
- exact training/corruption seed counts;
- whether all 12 stations are feasible for repeated holdout within the compute budget;
- whether a matched same-station comparator is warranted before using the phrase "site-shift penalty."

## Gate

P2 may begin. The protocol remains **DRAFT** until the dataset audit informs these remaining choices.
