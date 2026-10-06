# Research Protocol

**Status: DRAFT — DO NOT RUN FINAL EVALUATION UNTIL FROZEN**

## 1. Study objective

Evaluate how air-quality forecasting model performance changes when deployment observations are degraded or originate from an unseen monitoring site.

## 2. Primary research question

How reliable are machine-learning and deep-learning air-quality forecasting models when sensor observations are incomplete/noisy or originate from an unseen monitoring site?

## 3. Hypotheses (provisional)

- H1: Learned models outperform persistence under clean evaluation.
- H2: Forecast error increases as observation corruption becomes more severe.
- H3: Model ranking under clean conditions may not remain stable under corrupted observations.
- H4: A held-out monitoring site induces a measurable generalization penalty.

## 4. Dataset

Planned: UCI Beijing Multi-Site Air Quality dataset.

## 5. Outcome

Primary outcome: PM2.5 concentration one hour ahead.

## 6. Inputs

Provisional 24-hour history of pollutant + meteorological observations, with cyclical time features.

## 7. Data splitting

**TO FREEZE AFTER DATA AUDIT.**

Required principles:
- Preserve temporal order.
- Avoid random row splitting of time series.
- Ensure final test period is untouched during tuning.
- For site shift, held-out site must not appear in training.

## 8. Models

Provisional:
- Persistence
- XGBoost (or documented fallback)
- MLP
- Compact GRU

## 9. Corruptions

### Random feature dropout
Provisional severities: 10%, 30%, 50%.

### Whole-variable dropout
Provisional channels: NO2, CO, TEMP.

### Measurement noise
Provisional normalized severities: 5%, 10%, 20%.

Exact implementation must be specified before freeze.

## 10. Metrics

- MAE (primary)
- RMSE
- R²
- Relative Performance Degradation (RPD)

For lower-is-better metric M:

`RPD = (M_degraded - M_clean) / M_clean * 100`

## 11. Statistical analysis

Plan bootstrap confidence intervals over test predictions where computationally feasible. Preserve temporal dependence considerations when interpreting naive resampling.

## 12. Model selection

Hyperparameters may be selected using training/validation data only. Final test outcomes must not inform tuning.

## 13. Reproducibility

- Fixed seeds
- Config snapshot per run
- Environment captured via requirements
- Structured metrics/predictions saved

## 14. Freeze checklist

- [ ] Literature stress-test complete
- [ ] Dataset audit complete
- [ ] Split logic finalized
- [ ] Feature list finalized
- [ ] Model families finalized
- [ ] Corruption implementation finalized
- [ ] Metrics finalized
- [ ] Random seeds finalized
- [ ] Status changed from DRAFT to FROZEN

## 15. Deviations

Any post-freeze changes must be recorded in `PROTOCOL_DEVIATIONS.md` with date, reason, and expected impact.
