# MEMORY.md — AirSense-R Project Memory

This file stores durable project context so future contributors/agents can resume work without reconstructing prior decisions.

## Project identity

- Name: **AirSense-R**
- Working paper title: **Beyond Clean Accuracy: Evaluating Air-Quality Forecasting Models Under Sensor Degradation and Monitoring-Site Shift**
- Domain: environmental intelligence / air-quality forecasting / reliable ML
- Primary target: PM2.5 one-hour-ahead forecasting
- Intended public artifact: research repository + technical paper + GitHub Pages reliability explorer
- Edge deployment is **future work**, not a claimed contribution in v1.

## Core research question

Does the model selected as best under clean one-hour-ahead PM2.5 forecasting remain the best deployment choice when the same frozen candidates face sensor degradation or monitoring-site shift?

## Planned dataset

UCI Beijing Multi-Site Air Quality dataset: hourly pollutant and meteorological observations across 12 stations (2013–2017). Default access is **remote-only**: stream the authoritative UCI archive into temporary storage, compute a runtime SHA-256, audit it, retain only compact reports, and delete raw bytes automatically.

## P1 novelty decision

P1 literature reconnaissance (completed 2026-10-07) found strong direct prior art for missing-data forecasting, cross-location generalization, distribution shift, and ML/DL PM2.5 benchmarking. AirSense-R must **not** claim those elements individually as novel.

The v1 contribution is now frozen at the P1 level as a **model-selection reliability under deployment stress** study: quantify whether the clean-data winner remains the winner under random feature dropout, complete channel loss, controlled measurement noise, and unseen-site evaluation. Explicit outcomes should include clean/stress ranks, rank changes, winner retention, and relative performance degradation. Novelty is moderate/conditional; avoid "first study" claims without a later systematic review.

See `research/LITERATURE_NOTES.md` and `research/P1_COMPLETION_REPORT.md`.

## Planned reliability conditions

1. Clean / in-distribution evaluation
2. Random sensor-feature dropout
3. Whole-variable / sensor-channel dropout
4. Controlled measurement noise
5. Monitoring-site shift / unseen-station evaluation

## Planned model families

- Persistence baseline
- Tree-based ML baseline (default candidate: XGBoost; fallback: HistGradientBoostingRegressor)
- MLP
- Compact GRU

Avoid expanding model count unless a scientific reason is documented.

## Metrics

Primary: MAE
Secondary: RMSE, R²
Robustness: Relative Performance Degradation (RPD)
Required for central comparisons: paired dependence-aware uncertainty / temporal-block bootstrap

## Scientific guardrails

- Freeze protocol before final experiments.
- Never tune hyperparameters on final test outcomes.
- Preserve time order in temporal splits.
- Prevent future information leakage in feature construction/scaling.
- For site-shift tests, keep held-out station data out of training.
- Record all protocol deviations.
- P1 novelty stress-test is complete; keep claims limited to the frozen P1 contribution statement and avoid absolute first-of-kind language.
- Do not claim Edge-ML deployment in v1.

## Dashboard concept

Static GitHub Pages "Environmental ML Reliability Explorer" with precomputed results. Planned controls: model, station/site, operating condition, corruption severity. Planned outputs: actual vs predicted PM2.5, MAE/RMSE/R², RPD, and model comparison views.

## Two-day constraint

The project is intentionally narrow. Prioritize complete, reproducible evidence over additional models/features. Anomaly detection is out of v1 scope unless the core study is fully complete.

## P1.5 methodology decisions

- The deployable model is selected **only from clean validation MAE**; final test outcomes cannot choose the model.
- A test-best model is a retrospective oracle reference, not an implementable selection rule.
- **Selection regret** is a central outcome: stressed MAE of the validation-selected model minus the best stressed MAE among candidates.
- Ranking changes must be interpreted with paired uncertainty and a predefined practical near-tie rule.
- Observation corruptions act on the chronological sensor stream **before** overlapping windows are built; future targets remain uncorrupted.
- Noise severity uses **training-derived frozen scales**, never test statistics.
- Prefer repeated leave-one-station-out evaluation across all feasible stations; the held-out station is excluded from fitting/preprocessing/selection. Recent local observations may still be used as inference inputs.
- Avoid calling cross-site error a causal "site-shift penalty" unless a matched same-station comparator is implemented.
- Preprocessing/imputation is part of the evaluated forecasting pipeline.
- Uncertainty for central model comparisons is mandatory, with paired temporal-block bootstrap planned.


## P2 dataset decisions

- P2 **closed 2026-10-08** after authoritative UCI acquisition and structural verification under Python 3.11.
- Frozen authoritative archive SHA-256: `b04da438b2f331ac0ffd45aebdfec0d20d2367feb5f6948c4b1f7ce1191e33c4`; archive size 8,192,212 bytes.
- Verified 420,768 rows, 12/12 expected stations, 35,064 rows per station, 2013-03-01 00:00 through 2017-02-28 23:00, with no duplicates, backward/zero steps, or hourly gaps.
- Aggregate PM2.5 missingness is 8,739 rows (2.077%); CO has the highest aggregate missingness among numeric channels at 4.920%.
- PM2.5-complete 24-hour-history/1-hour-ahead windows range from 28,900 to 31,172 per station, supporting retention of the 24-hour lookback as a viable P3 candidate.
- Raw data remain remote-only/temporary; only compact audit evidence is retained.
- The first successful authoritative receipt is immutable. Both acquisition entry points must compare later downloads to the frozen SHA-256 and station inventory and fail on mismatch.
- Full-data P2 analysis was restricted to structural checks. Modeling-relevant exploratory analysis remains development-only under the frozen P3 temporal boundaries.

## P3 protocol decisions

- P3 is marked FROZEN on 2026-10-08; the completion report records that final-test performance was not inspected. `research/PROTOCOL.md` is authoritative and `configs/experiment.yaml` records the settings.
- Training targets: 2013-03-02 through 2015-02-28; validation: 2015-03-01 through 2016-02-29; final test: 2016-03-01 through 2017-02-28. Horizon: 1 hour; lookback: 24 hours.
- Features: six pollutants, TEMP/PRES/DEWP/RAIN/WSPM, categorical wind direction, and hour/day-of-year cyclical features. Station identity is excluded as a predictor.
- Primary imputation: missingness indicators, causal station-wise forward fill capped at 6 hours, then training-only median/category fallback. Sensitivity: fallback without forward fill. Future targets are never imputed.
- Models: persistence, XGBoost, MLP, compact GRU. Training-only expanding-window tuning precedes clean-validation family selection with equal station weighting.
- Practical near-tie: 1.0 microgram per cubic metre in aggregate MAE; simplicity tiebreak: persistence, XGBoost, MLP, GRU.
- LOSO covers all 12 stations; held-out station data are excluded from fitting, preprocessing fitting, tuning, and selection.
- Corruptions: random dropout at 10/30/50%; whole-variable loss of NO2/CO/TEMP; contiguous outages of 6/12 hours; noise at 5/10/20% of training-derived IQR/1.349, with training-standard-deviation fallback. See the protocol for eligible channels and clipping rules.
- Training seeds: 42, 31415, 27182. Corruption seeds: 101, 202, 303, 404, 505. Bootstrap seed: 424242.
- Uncertainty: paired moving-block bootstrap with 24-hour blocks, 2,000 replicates, and 95% confidence intervals.
- P4 data-pipeline implementation is next. Starter utilities must be brought into agreement with the frozen protocol before experiments.
- Material post-freeze methodological changes must be recorded in `research/PROTOCOL_DEVIATIONS.md`.

