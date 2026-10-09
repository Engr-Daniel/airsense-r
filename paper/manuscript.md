# AirSense-R: Do Air-Quality Forecasters Keep Their Rank Under Sensor Degradation and Site Shift?

## Abstract

_TBD after results._

## 1. Introduction

The study asks whether a forecaster chosen using clean validation data remains a good choice when input observations are degraded or the monitoring station was excluded from fitting. The intended contribution is a controlled evaluation of selection regret and ranking stability, not a new forecasting architecture. Evidence, prior-art limits, and conditions for a useful contribution are documented in [the pre-results research rationale](../research/RESEARCH_RATIONALE.md). No empirical conclusion is asserted before P5-P8.

The planned contribution is to evaluate whether a model family selected under clean validation remains a practically defensible choice under predefined observation degradation and unseen-station conditions, using paired comparisons, selection regret, practical near-ties, and dependence-aware uncertainty. Clean means no added synthetic degradation, not complete observations. Selection is repeated within each station-holdout fold.

The canonical title is maintained in CITATION.cff; manuscript findings remain pending.

## 2. Related Work

Recent air-quality forecasting research already covers several elements that motivate, but also constrain, AirSense-R. Alvarado-Alcon et al. (2026) study citywide cross-location forecasting under sparse and missing sensor streams with held-out stations, while Chowdhury et al. (2026) compare machine- and deep-learning PM2.5 forecasters under varying data availability and imputation strategies. Wang et al. (2025) likewise develop a missing-data-tolerant spatiotemporal forecasting architecture, demonstrating that robustness to missing observations is itself an established research problem.

Spatial and distributional generalization are also not new. Liu et al. (2024) benchmark PM2.5 forecasting under distribution shift and show that model families can differ substantially in shift sensitivity. Yao et al. (2024) use transfer learning across the 12 Beijing monitoring sites to improve forecasting at data-limited stations. More recently, Chisilev and Pelican (2026) report that model rankings vary across forecast horizons, countries and station contexts, and explicitly evaluate spatial transfer. Adong and Bainomugisha (2026), although focused on sensor calibration rather than forecasting, show that model transfer across heterogeneous African cities can degrade sharply when environmental conditions differ.

These studies rule out an over-broad novelty claim based on missing data, unseen sites, distribution shift, or ML-versus-DL comparison alone. AirSense-R therefore focuses on a narrower deployment question: **whether the model selected as best under clean, in-distribution evaluation remains the preferred model when the same frozen candidates are subjected to multiple pre-specified sensor/deployment stresses.** The analysis emphasizes clean-to-stress changes in absolute error, relative degradation and model ordering. This positioning is consistent with broader calls to move beyond single aggregate forecasting leaderboards toward context-sensitive evaluation (Feng et al., 2026), while remaining specific to controlled environmental-sensor stress tests.

The literature reconnaissance supporting this positioning is documented in `research/LITERATURE_NOTES.md`.

## 3. Data

_TBD after dataset audit._

## 4. Methods

_TBD from frozen protocol._

## 5. Experimental Protocol

_TBD from frozen protocol._

## 6. Results

_TBD only after experiments are complete._

## 7. Discussion

_TBD after results; distinguish evidence from interpretation._

## 8. Limitations

- Public Beijing monitoring data may not represent all deployment contexts.
- Synthetic corruptions approximate, but do not fully reproduce, physical sensor failure modes.
- No embedded/Edge deployment is claimed in v1.
- Cross-site shift is not equivalent to cross-city/cross-country shift.

## 9. Future Work

Potential model compression, quantization, and eventual on-device evaluation on resource-constrained environmental sensing hardware.

## 10. Conclusion

_TBD._
