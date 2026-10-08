# P3 Completion Report — Protocol Freeze

**Status: COMPLETE**  
**Freeze date: 2026-10-08**

## Objective

Freeze all analysis choices required before AirSense-R proceeds to pipeline construction and final experiments.

## P2 gate

P3 was frozen only after authoritative P2 closure. The verified UCI archive SHA-256 is:

`b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`

P2 verified 420,768 rows, all 12 stations, 35,064 hourly rows per station, no duplicate timestamps, no backward/zero steps, no hourly gaps, aggregate PM2.5 missingness of 2.077%, and 28,900–31,172 PM2.5-complete provisional 24-hour-history windows per station.

## Frozen P3 decisions

### Temporal design

- Forecast horizon: 1 hour.
- Lookback: 24 hours.
- Training targets: 2013-03-02 00:00 through 2015-02-28 23:00.
- Clean validation targets: 2015-03-01 00:00 through 2016-02-29 23:00.
- Final untouched test targets: 2016-03-01 00:00 through 2017-02-28 23:00.
- Splits are by target timestamp; no random row splitting.

### Features

- Historical PM2.5, PM10, SO2, NO2, CO, O3, TEMP, PRES, DEWP, RAIN, WSPM.
- `wd` as training-fitted categorical one-hot input with missing/unknown categories.
- Cyclical hour-of-day and day-of-year.
- Station ID excluded as a predictor.

### Missing-data policy

Primary policy:

- binary missing indicators;
- causal station-wise forward fill capped at 6 hours;
- remaining numeric gaps filled with training-only feature medians;
- analogous 6-hour causal carry-forward for wind direction followed by `MISSING`/`OTHER` categories;
- future targets never imputed.

Sensitivity policy:

- training-only median/category fallback with no forward fill, retaining the same missingness indicators.

### Model selection

Candidate families are persistence, XGBoost, MLP, and compact GRU. Learned-family hyperparameters are tuned only inside the training period with three frozen expanding-window folds. The deployable family is selected only by unweighted mean station-level clean validation MAE.

Candidates within 1.0 µg/m³ MAE are treated as practical near-ties and resolved by fixed simplicity order: persistence, XGBoost, MLP, GRU.

### Site evaluation

- 12-fold leave-one-station-out evaluation.
- Held-out station excluded from fitting, preprocessing, tuning, and selection.
- Recent held-out-station observations may be used at inference.
- Station identity is not an input feature.
- Equal station weighting for aggregate cross-site summaries.

### Corruption protocol

- Random non-target feature dropout: 10%, 30%, 50%.
- Whole-variable dropout: NO2, CO, TEMP.
- Contiguous outages: 6 and 12 hours on NO2, CO, TEMP, with one seeded event per calendar month and outage-affected-window reporting.
- Measurement noise: 5%, 10%, 20% of training-derived robust scale `IQR/1.349` with training-standard-deviation fallback.
- Corruptions occur on the chronological stream before window construction.
- Future target preserved.
- No stress retraining.

### Seeds

- Training: 42, 31415, 27182.
- Corruption: 101, 202, 303, 404, 505.
- Bootstrap: 424242.

### Uncertainty

- Paired moving-block bootstrap.
- 24-hour block length.
- 2,000 replicates.
- 95% confidence intervals.
- Same target timestamps and sampled blocks for paired model comparisons.

### Near-ties

The practical near-tie threshold is fixed at 1.0 µg/m³ aggregate MAE. A rank reversal inside that margin is not interpreted as a meaningful model-selection failure. Central directional claims also require the paired 95% interval to exclude zero.

## Rationale for freezing without final-test inspection

The temporal boundary was defined first. All remaining P3 choices are structural or a priori methodological choices. The final test year remains untouched and cannot be used to revise the frozen protocol.

The P2 structural audit showed long raw pollutant missing runs, which rules out unlimited forward fill. The six-hour causal cap was therefore frozen as a conservative short-gap policy, with training-only fallback. The 24-hour bootstrap block is frozen a priori around the dominant diurnal context and the model lookback rather than selected from final-test autocorrelation.

## Files that must be synchronized in the P3 commit

- `research/PROTOCOL.md` → status `FROZEN` and full frozen rules.
- `configs/experiment.yaml` → executable frozen settings.
- `TASK.md` → all P3 items checked.
- `research/P2_VERIFICATION_STATUS.md` → authoritative verification closed.
- `research/DATASET.md` → horizon/lookback no longer provisional.
- `research/EXPERIMENTS.md` → align with frozen settings.
- `MEMORY.md` → durable P3 decisions.

## Gate to P4

P4 may begin after these synchronized P3 files are committed. Any subsequent material methodological change must be recorded in `research/PROTOCOL_DEVIATIONS.md`.
