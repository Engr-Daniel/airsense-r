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

How reliable are machine-learning and deep-learning air-quality forecasting models when sensor observations are incomplete/noisy or originate from an unseen monitoring site?

## Planned dataset

UCI Beijing Multi-Site Air Quality dataset: hourly pollutant and meteorological observations across 12 stations (2013–2017). Keep raw data immutable once downloaded.

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
- Do not claim novelty until literature stress-testing is complete.
- Do not claim Edge-ML deployment in v1.

## Dashboard concept

Static GitHub Pages "Environmental ML Reliability Explorer" with precomputed results. Planned controls: model, station/site, operating condition, corruption severity. Planned outputs: actual vs predicted PM2.5, MAE/RMSE/R², RPD, and model comparison views.

## Two-day constraint

The project is intentionally narrow. Prioritize complete, reproducible evidence over additional models/features. Anomaly detection is out of v1 scope unless the core study is fully complete.
