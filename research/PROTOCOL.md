# Research Protocol

**Status: DRAFT — DO NOT RUN FINAL EVALUATION UNTIL FROZEN**

## 1. Study objective

Evaluate whether model selection based on clean, in-distribution PM2.5 forecasting remains reliable when the same frozen candidate models are exposed to deployment-relevant observation degradation or an unseen monitoring site.

## 2. Primary research question

Does the model selected as best under clean one-hour-ahead PM2.5 forecasting remain the best choice under sensor degradation and monitoring-site shift?

## 3. Hypotheses (provisional)

- H1: At least one learned model outperforms persistence under clean evaluation.
- H2: Forecast error increases as observation corruption becomes more severe.
- H3: The ordering of candidate models under clean evaluation is not invariant to all pre-specified deployment stresses.
- H4: A held-out monitoring site induces a measurable generalization penalty relative to clean in-distribution evaluation.
- H5: The model with the best clean MAE is not assumed a priori to have the lowest relative degradation; clean accuracy and robustness are treated as distinct empirical properties.

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
- Clean model rank and stress-condition model rank
- Rank change relative to clean evaluation
- Winner-retention indicator (whether the clean rank-1 model remains rank 1)
- Optional rank-stability summary only if its exact definition is frozen before final evaluation

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

## 14. P1 literature constraint

The literature stress-test is complete. Missing-data forecasting, held-out-station evaluation, distribution-shift analysis, ML/DL comparison and use of the Beijing multi-site dataset are not treated as individually novel. The planned contribution is the controlled analysis of clean-to-stress **model-selection stability** across several pre-specified deployment stresses. See `LITERATURE_NOTES.md`.

## 15. Freeze checklist

- [ ] Literature stress-test complete
- [ ] Dataset audit complete
- [ ] Split logic finalized
- [ ] Feature list finalized
- [ ] Model families finalized
- [ ] Corruption implementation finalized
- [ ] Metrics finalized
- [ ] Random seeds finalized
- [ ] Status changed from DRAFT to FROZEN

## 16. Deviations

Any post-freeze changes must be recorded in `PROTOCOL_DEVIATIONS.md` with date, reason, and expected impact.
