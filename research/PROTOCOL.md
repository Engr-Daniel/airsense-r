# Research Protocol

**Status: DRAFT — DO NOT RUN FINAL EVALUATION UNTIL FROZEN**

## 1. Study objective

Evaluate whether the model selected from clean validation data remains a reliable deployment choice when air-quality observations are degraded or originate from a monitoring site excluded from model fitting.

The study is explicitly about **model-selection reliability under deployment stress**, not simply about which model attains the lowest clean-test error.

## 2. Primary research question

Does clean-validation model selection remain practically reliable when sensor observations are incomplete/noisy or when inference occurs at an unseen monitoring site?

## 3. Research questions

- **RQ1:** Which candidate model would be selected using clean validation MAE?
- **RQ2:** How do candidate models' absolute errors and rankings change under predefined observation-degradation conditions?
- **RQ3:** What selection regret is incurred by retaining the clean-validation-selected model under each stress condition?
- **RQ4:** How consistent are those conclusions across monitoring stations and repeated corruption/training realizations?

## 4. Hypotheses (provisional)

- **H1:** At least one learned model will outperform persistence under clean evaluation.
- **H2:** Forecast error will increase as observation corruption becomes more severe.
- **H3:** Clean-validation model ranking will not necessarily remain stable under all deployment stresses.
- **H4:** Some apparent rank changes will be practically negligible; selection regret and uncertainty will distinguish meaningful reversals from near-ties.
- **H5:** Cross-site results will vary by station, so station-specific and aggregate results are both required.

These hypotheses will be frozen only after P2 establishes dataset structure and usable sample sizes.

## 5. Dataset

Planned: UCI Beijing Multi-Site Air Quality dataset.

The v1 study uses regulatory/reference monitoring data. It does **not** establish performance on low-cost embedded sensors, microcontrollers, field power constraints, or device-level calibration.

## 6. Forecasting outcome

Primary outcome: PM2.5 concentration one hour ahead.

Provisional history window: 24 hours of pollutant and meteorological observations plus cyclical time features.

## 7. Model-selection rule

Candidate families remain deliberately limited:

- Persistence
- Tree-based ML (default candidate: XGBoost; documented fallback if needed)
- MLP
- Compact GRU

### Selection

1. Train/tune candidates using training data only.
2. Select **one model using clean validation MAE**.
3. Freeze that selection before inspecting final clean/stressed test outcomes.
4. Evaluate all frozen candidate pipelines on the same test station-timestamp targets.

The model with the lowest test MAE is a **retrospective oracle reference only** and never determines the deployed choice.

## 8. Selection regret

For stress condition `s`:

`SelectionRegret(s) = MAE_s(validation-selected model) - min_m MAE_s(m)`

Selection regret is reported in the original PM2.5 units alongside ranking changes. Rank reversal alone is insufficient evidence of practical consequence.

## 9. Data splitting

**TO FREEZE AFTER P2 DATA AUDIT.**

Required principles:

- Preserve temporal order.
- Never randomly split individual time-series rows across train/validation/test.
- Use explicit timestamps/cutoffs, not only row-count fractions, in the final pipeline.
- Keep final test periods untouched during tuning/selection.
- Fit scalers, imputers, feature transforms, noise scales, and any learned preprocessing on development/training data only.
- Score competing models on identical station-timestamp targets whenever comparisons are made.
- Construct windows without future information leakage.

## 10. Unseen-site evaluation

Primary plan: repeated leave-one-station-out evaluation over all feasible stations, subject to P2 confirming coverage and computational feasibility.

For each held-out station:

- no rows from that station may be used for parameter fitting, hyperparameter tuning, preprocessing fitting, or model selection;
- recent observations from the held-out station may be used as **forecast inputs at inference**, because the task is local short-horizon forecasting rather than forecasting a station with no current measurements;
- station-specific results must be retained;
- a predefined aggregate across stations must be reported.

The manuscript will avoid calling higher held-out-station error a causal "site-shift penalty" unless a matched same-station reference experiment is explicitly defined. Otherwise, results will be described as **cross-site generalization performance**.

## 11. Corruption intervention rules

Observation corruptions must be applied to the **underlying chronological station stream before overlapping forecast windows are constructed**. This prevents one physical observation from being missing in one window but inexplicably available in another.

Future forecast targets remain uncorrupted.

### 11.1 Random feature dropout

Provisional severities: 10%, 30%, 50%.

Primary analysis will initially corrupt non-target sensor channels so persistence remains interpretable. A separate historical-PM2.5 outage sensitivity may be added only if its fallback policy is frozen in advance.

### 11.2 Whole-variable dropout

Provisional channels: NO2, CO, TEMP.

The unavailable channel is removed consistently across the underlying evaluation stream.

### 11.3 Contiguous outage sensitivity

Provisional durations: 6 and 12 hours.

This is a focused sensitivity analysis for realistic continuous sensor/communication outages, not a new major task family.

### 11.4 Measurement noise

Provisional normalized severities: 5%, 10%, 20% of a **training-derived feature scale**.

Noise scales must be estimated from training data only and frozen. Test-set statistics must never determine corruption magnitude.

### 11.5 Shared stress realizations

For a given station, condition, severity, and seed, all candidate models must be evaluated using the same corruption realization and same target rows.

## 12. Missing-data handling

Preprocessing is part of the evaluated forecasting pipeline.

A primary imputation policy will be frozen after P2. A small predefined sensitivity analysis may compare the primary policy with one alternative to determine whether ranking changes are driven mainly by the imputation strategy rather than the forecasting model.

Imputation parameters must be estimated on training data only.

## 13. Metrics

### Primary

- MAE

### Secondary

- RMSE
- R²
- Relative Performance Degradation (RPD)
- model rank / rank change
- winner retention
- selection regret

For lower-is-better metric `M`:

`RPD = (M_degraded - M_clean) / M_clean * 100`

Absolute stressed MAE must always accompany RPD because low relative degradation does not imply good absolute forecasting.

## 14. Statistical uncertainty

Uncertainty is **required**, not optional, for central ranking/selection claims.

Primary plan:

- paired comparisons on identical target rows;
- temporal-block bootstrap rather than IID row bootstrap;
- shared corruption realizations across models;
- multiple corruption seeds and, where stochastic training applies, multiple training seeds as computationally feasible;
- report confidence intervals for paired MAE differences and/or selection regret summaries.

P2/P3 will freeze the temporal block length after inspecting temporal structure. Cross-station results will be retained separately before aggregation; thousands of correlated hourly forecasts will not be treated as independent experimental replications.

## 15. Practical significance / near-ties

P3 must define a practical near-tie rule before final evaluation. This prevents tiny numerical differences from being overinterpreted as meaningful model-selection failures.

The threshold will be chosen after P2 characterizes PM2.5 scale and variability, but before final test evaluation.

## 16. Reproducibility

- Fixed documented seeds.
- Config snapshot per run.
- Environment captured via requirements/lock information.
- Structured predictions and metrics saved.
- Corruption masks/seeds recorded.
- Data archive/file checksums recorded in P2.
- Tests must cover target preservation, deterministic corruption, train-derived noise scales, temporal ordering, station isolation, and split/window leakage protections.

## 17. Computational/Edge boundary

Optional CPU resource measurements may include serialized model size, inference latency, and memory under a documented desktop environment. They are **not evidence of microcontroller feasibility, embedded energy use, or field reliability**.

Edge deployment remains future work.

## 18. Freeze checklist

- [x] P1 literature stress-test complete
- [x] P1.5 methodology hardening complete
- [ ] P2 dataset audit complete
- [ ] timestamp/split logic finalized
- [ ] feature list finalized
- [ ] imputation policy finalized
- [ ] model families finalized
- [ ] model-selection rule finalized
- [ ] corruption implementation and severities finalized
- [ ] repeated site-holdout design finalized
- [ ] uncertainty/block-bootstrap settings finalized
- [ ] practical near-tie rule finalized
- [ ] random/training/corruption seeds finalized
- [ ] Status changed from DRAFT to FROZEN

## 19. Deviations

Any post-freeze change must be recorded in `PROTOCOL_DEVIATIONS.md` with date, reason, and expected impact.
