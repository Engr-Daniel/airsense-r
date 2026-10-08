# Research Protocol

**Status: FROZEN — final evaluation may proceed only under this protocol**

**Frozen:** 2026-10-08

## 1. Study objective

Evaluate whether the model selected from clean validation data remains a reliable deployment choice when air-quality observations are degraded or originate from a monitoring site excluded from model fitting.

The study is explicitly about **model-selection reliability under deployment stress**, not simply about which model attains the lowest clean-test error.

## 2. Primary research question

Does clean-validation model selection remain practically reliable when sensor observations are incomplete/noisy or when inference occurs at an unseen monitoring site?

## 3. Research questions

- **RQ1:** Which candidate model is selected using clean validation MAE?
- **RQ2:** How do candidate models' absolute errors and rankings change under predefined observation-degradation conditions?
- **RQ3:** What selection regret is incurred by retaining the clean-validation-selected model under each stress condition?
- **RQ4:** How consistent are those conclusions across monitoring stations and repeated corruption/training realizations?

## 4. Frozen hypotheses

- **H1:** At least one learned model will outperform persistence under clean evaluation.
- **H2:** Forecast error will increase as observation corruption becomes more severe.
- **H3:** Clean-validation model ranking will not necessarily remain stable under all deployment stresses.
- **H4:** Some apparent rank changes will be practically negligible; selection regret, the predefined near-tie rule, and paired uncertainty will distinguish meaningful reversals from numerical near-ties.
- **H5:** Cross-site results will vary by station, so station-specific and aggregate results are both required.

## 5. Dataset

UCI Beijing Multi-Site Air Quality dataset (UCI ID 501; DOI `10.24432/C5RK5G`). Raw bytes are acquired remotely into temporary storage and are not retained by the repository workflow.

P2 authoritative verification closed on 2026-10-08. The frozen archive SHA-256 is `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`. The verified dataset contains 420,768 rows across all 12 expected stations, 35,064 hourly rows per station, with no duplicate timestamps, backward/zero steps, or hourly gaps.

The v1 study uses regulatory/reference monitoring data. It does **not** establish performance on low-cost embedded sensors, microcontrollers, field power constraints, or device-level calibration.

## 6. Forecasting outcome and temporal context

- **Primary outcome:** PM2.5 concentration one hour ahead.
- **Forecast horizon:** 1 hour.
- **History window:** 24 hours.
- **Window definition:** for target time `t+1`, the model may use observations available through time `t`; no value at or after the target time may enter the input window.
- **Target handling:** future targets are never imputed or corrupted. A sample whose target PM2.5 is missing is not scored.

The 24-hour lookback is retained because P2 verified 28,900–31,172 PM2.5-complete candidate history windows per station and because it captures the principal diurnal context without expanding the study into long-horizon architecture search.

## 7. Frozen feature set

### 7.1 Historical numeric sensor channels

- PM2.5
- PM10
- SO2
- NO2
- CO
- O3
- TEMP
- PRES
- DEWP
- RAIN
- WSPM

### 7.2 Wind direction

`wd` is retained as a categorical meteorological input. After the causal missing-data step, categories are one-hot encoded using categories learned from the fitting/training data only. Missing values use a dedicated `MISSING` category and any unseen category at inference uses `OTHER`.

### 7.3 Deterministic temporal features

The pipeline includes:

- hour-of-day sine/cosine;
- day-of-year sine/cosine.

These are deterministic calendar features and may be computed for the forecast target timestamp because they contain no future measured quantity.

### 7.4 Explicit exclusions

- Station identity is used for grouping, splitting, and reporting, **not as a predictive feature**. This avoids giving seen-station models a categorical identity unavailable for a genuinely unseen held-out station.
- `No` and raw timestamp component columns are identifiers/construction fields, not model inputs after feature construction.

## 8. Frozen temporal split

All splits are defined by **target timestamp**, not by random rows or row-count fractions.

### Training period

Targets from:

`2013-03-02 00:00` through `2015-02-28 23:00`

The one-day offset at the beginning ensures the first scored target has a complete 24-hour chronological history available from the dataset start.

### Clean validation period

Targets from:

`2015-03-01 00:00` through `2016-02-29 23:00`

### Final untouched test period

Targets from:

`2016-03-01 00:00` through `2017-02-28 23:00`

The final test period is a complete calendar year and must not be used to choose features, imputers, hyperparameters, corruption magnitudes, near-tie thresholds, bootstrap settings, or model family.

A validation/test target may use its immediately preceding 24-hour observed history even when that history lies in the previous split. This is allowed because those observations occur strictly before the forecast target and mirrors deployment. Learned preprocessing remains fitted only on the permitted fitting data.

## 9. Model families and tuning

The frozen candidate families are deliberately limited to:

1. Persistence baseline.
2. XGBoost regressor.
3. MLP.
4. Compact GRU.

No additional model family may be added after protocol freeze without recording a protocol deviation.

### 9.1 Hyperparameter tuning

Hyperparameters for each learned family must be tuned **inside the training period only** using expanding-window temporal validation. The default internal folds are:

- Fold 1: fit through `2014-02-28 23:00`, validate `2014-03-01 00:00`–`2014-06-30 23:00`;
- Fold 2: fit through `2014-06-30 23:00`, validate `2014-07-01 00:00`–`2014-10-31 23:00`;
- Fold 3: fit through `2014-10-31 23:00`, validate `2014-11-01 00:00`–`2015-02-28 23:00`.

The hyperparameter search spaces must be declared in configuration/code before their scores are inspected. The chosen hyperparameters minimize mean internal-fold MAE. The family is then refit on the full training period before clean validation scoring.

Persistence has no tuned parameters.

## 10. Clean-validation model-selection rule

1. Tune each learned family using training data only as defined above.
2. Refit each tuned family on the full training period.
3. Evaluate all candidate pipelines on the same clean validation station-target rows.
4. Aggregate clean validation MAE by first computing station-specific MAE and then taking the **unweighted mean across eligible stations** so a station is the unit of aggregation rather than an individual hourly row.
5. Select exactly one model family with the lowest aggregate clean validation MAE.
6. If two or more families satisfy the frozen near-tie rule in Section 18, choose the simpler model by this fixed order: **persistence → XGBoost → MLP → GRU**.
7. Freeze the selected family before inspecting final clean or stressed test outcomes.

The model with the lowest final test MAE is a **retrospective oracle reference only** and never determines the deployed choice.

## 11. Primary missing-data policy

Preprocessing is part of the evaluated forecasting pipeline and must be applied identically during clean and stressed evaluation.

### 11.1 Numeric channels

For each station's chronological input stream:

1. Add a binary missingness indicator for every raw sensor channel before imputation. Synthetic corruptions also activate the corresponding indicator.
2. Apply causal forward-fill for at most **6 consecutive hours** using only earlier observations from the same station.
3. Any remaining missing numeric value is replaced with the feature median estimated from the current fitting/training stations and fitting period only.

Forward fill is intentionally capped. P2 identified some pollutant gaps far longer than six hours, so unlimited carry-forward would create implausibly stale measurements.

Historical PM2.5 inputs follow the same raw-data imputation policy, although the primary synthetic random-dropout and noise experiments do not corrupt historical PM2.5.

### 11.2 Wind direction

For `wd`:

1. preserve a missingness indicator;
2. causal forward-fill for at most 6 hours;
3. map any remaining missing value to `MISSING`;
4. map unseen inference categories to `OTHER` after fitting the training-only encoder.

### 11.3 Sensitivity imputation policy

One predefined sensitivity policy is allowed:

- no forward fill;
- training-only feature median for numeric channels;
- `MISSING`/`OTHER` handling for wind direction;
- the same missingness indicators.

This sensitivity is used to test whether central ranking conclusions are mainly driven by the primary causal carry-forward choice.

Future targets are never imputed.

## 12. Unseen-site evaluation

Cross-site generalization uses repeated **leave-one-station-out (LOSO)** evaluation across all 12 verified stations.

For each held-out station:

- all rows from that station are excluded from preprocessing fitting, hyperparameter tuning, model fitting, and clean-validation model selection;
- training and validation time boundaries remain exactly those in Section 8 for the remaining 11 stations;
- model-family selection is repeated inside the fold using only the 11 fitting stations' clean validation data;
- the held-out station is evaluated only on its final test targets;
- its recent local observations may be used as forecast inputs because the task is local short-horizon forecasting, not prediction at a station with no current measurements;
- no station-ID predictor is used;
- results are retained per station before aggregation.

The primary cross-site aggregate is the unweighted mean of station-level metrics across the 12 LOSO folds. Results are described as **cross-site generalization performance**, not a causal site-shift penalty.

## 13. Frozen corruption intervention rules

All observation corruptions act on the **underlying chronological station stream before overlapping windows are constructed**. The same corrupted physical observation must therefore be seen consistently by every window containing it.

Future PM2.5 targets remain uncorrupted.

For a fixed station, condition, severity, and corruption seed, all candidate models receive the same corruption realization and are scored on identical eligible target timestamps.

### 13.1 Random feature dropout

Severities are frozen at:

- 10%
- 30%
- 50%

Dropout is independent Bernoulli masking at the station-timestamp-channel level across non-target input channels:

`PM10, SO2, NO2, CO, O3, TEMP, PRES, DEWP, RAIN, WSPM, wd`.

Historical PM2.5 is excluded from the primary random-dropout intervention so the persistence baseline remains interpretable.

### 13.2 Whole-variable dropout

Primary channels are frozen as:

- NO2
- CO
- TEMP

Each channel is evaluated separately as completely unavailable over the evaluation stream. The pipeline must recover through the frozen missing-data policy; no retraining on corrupted data is performed.

### 13.3 Contiguous outage sensitivity

Durations are frozen at:

- 6 hours
- 12 hours

The same representative channels `NO2`, `CO`, and `TEMP` are evaluated separately. For each station, channel, duration, and corruption seed, one outage start is sampled within each calendar month of the final test year, subject to staying within that month. Outages are applied before window construction.

Report both:

- full-period metrics; and
- metrics restricted to target windows whose 24-hour input history intersects an outage.

The outage analysis is a focused sensitivity analysis, not a new model-selection stage.

### 13.4 Measurement noise

Normalized severities are frozen at:

- 5%
- 10%
- 20%

For each numeric non-target channel, independent zero-mean Gaussian noise is added with standard deviation:

`severity × robust_training_scale(feature)`

where:

`robust_training_scale = IQR / 1.349`

estimated from fitting/training data only. If the IQR is zero, training standard deviation is used as the fallback scale.

Historical PM2.5 and categorical `wd` are excluded from the primary noise intervention. After noise injection, naturally non-negative variables (`PM10`, `SO2`, `NO2`, `CO`, `O3`, `RAIN`, `WSPM`) are clipped at zero.

### 13.5 No stress retraining

For observation-degradation experiments, models and learned preprocessing parameters remain those fitted under the clean protocol. Corruption is an evaluation-time deployment stress, not a retraining condition.

## 14. Frozen random seeds

### Hyperparameter search / deterministic setup

- base seed: `42`

### Training seeds for stochastic learned models

- `42`
- `31415`
- `27182`

The MLP and GRU must be trained under all three seeds. XGBoost uses the same seed set where stochastic settings make the seed relevant. Persistence is deterministic and is not artificially replicated.

### Corruption seeds

- `101`
- `202`
- `303`
- `404`
- `505`

### Bootstrap seed

- `424242`

All seeds used in an output must be recorded with that output.

## 15. Metrics

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

Absolute stressed MAE must always accompany RPD.

## 16. Selection regret

For stress condition `s`:

`SelectionRegret(s) = MAE_s(validation-selected model) - min_m MAE_s(m)`

Selection regret is reported in original PM2.5 units alongside ranking changes and uncertainty. The retrospective best stressed-test model is an oracle reference only.

## 17. Statistical uncertainty

Central model comparisons use paired dependence-aware uncertainty.

### 17.1 Paired temporal block bootstrap

- Method: paired moving-block bootstrap on aligned target timestamps.
- Block length: **24 hours**.
- Bootstrap replicates: **2,000**.
- Confidence level: **95%**.
- Bootstrap seed: `424242`.

The 24-hour block length is frozen a priori to preserve the principal diurnal dependence scale and to match the 24-hour forecasting context. It is not estimated from final-test autocorrelation.

For every comparison, the same sampled temporal blocks are applied to both models' aligned errors.

### 17.2 Reported uncertainty

At minimum, report 95% bootstrap confidence intervals for:

- paired MAE difference between the clean-validation-selected model and each comparator;
- selection regret;
- station-level stressed-minus-clean MAE change where relevant.

Training-seed and corruption-seed variation must be retained in structured outputs. Primary summaries average within station/condition across the predefined seeds, then aggregate stations with equal station weight.

Thousands of correlated hourly rows must not be treated as independent experimental replications.

## 18. Practical significance / near-ties

A practical near-tie is frozen **before final evaluation** as an absolute aggregate MAE difference of no more than:

**1.0 µg/m³ PM2.5**.

Interpretation rules:

- A rank reversal with absolute MAE difference `<= 1.0 µg/m³` is reported as a practical near-tie rather than a meaningful selection failure.
- A difference `> 1.0 µg/m³` is potentially meaningful, but central claims still require the paired 95% bootstrap interval to exclude zero in the corresponding direction.
- If the confidence interval includes zero, the comparison is described as uncertain even when the point difference exceeds the practical threshold.

For clean-validation selection, candidates within 1.0 µg/m³ of the lowest aggregate validation MAE are resolved by the fixed simplicity order in Section 10.

## 19. Reproducibility requirements

- Fixed documented seeds.
- Config snapshot per run.
- Environment captured via requirements/lock information.
- Structured predictions and metrics saved.
- Training and corruption seeds recorded.
- Corruption masks/event schedules recorded where practical.
- Data archive/file checksums recorded from P2.
- Tests must cover target preservation, deterministic corruption, train-derived noise scales, temporal ordering, station isolation, causal imputation, split/window leakage protections, and LOSO exclusion.

## 20. Computational/Edge boundary

Optional CPU resource measurements may include serialized model size, inference latency, and memory under a documented desktop environment. They are **not evidence of microcontroller feasibility, embedded energy use, or field reliability**.

Edge deployment remains future work.

## 21. Freeze checklist

- [x] P1 literature stress-test complete
- [x] P1.5 methodology hardening complete
- [x] P2 authoritative acquisition + structural audit complete and inspected
- [x] timestamp/split logic finalized
- [x] 1-hour horizon and 24-hour lookback finalized
- [x] feature list finalized
- [x] primary and sensitivity imputation policies finalized
- [x] model families finalized
- [x] clean-validation model-selection rule finalized
- [x] corruption implementation and severities finalized
- [x] repeated 12-station LOSO design finalized
- [x] uncertainty/block-bootstrap settings finalized
- [x] practical near-tie rule finalized
- [x] training/corruption/bootstrap seeds finalized
- [x] Status changed from DRAFT to FROZEN

## 22. Deviations

Any change after this freeze that affects data splitting, features, preprocessing, candidate models, model selection, corruption, seeds, evaluation targets, uncertainty, or practical-significance rules must be recorded in `research/PROTOCOL_DEVIATIONS.md` with date, reason, whether final-test results had been inspected, and expected impact.
