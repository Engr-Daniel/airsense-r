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

UCI Beijing Multi-Site Air Quality dataset: hourly pollutant and meteorological observations across 12 stations (2013–2017). Keep raw data immutable once downloaded.

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
Optional: bootstrap confidence intervals and paired error comparisons

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
