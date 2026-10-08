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

- P2 implementation + structural preflight completed 2026-10-08 for UCI dataset 501 (DOI `10.24432/C5RK5G`); authoritative UCI archive byte verification remains pending until the GitHub Action commits its receipt.
- Official structure: 420,768 hourly records, 12 stations, 2013-03-01 through 2017-02-28, six pollutants plus meteorological variables, with missing values present.
- Raw data should **not** be permanently downloaded by the default workflow. `scripts/run_data_audit.py` fetches into temporary storage, writes compact `audit/` artifacts, and removes the raw archive automatically.
- The exact archive SHA-256 is computed at runtime rather than hard-coded.
- Full-data P2 work is restricted to structural checks. Distribution/autocorrelation/feature analyses that could influence modeling are development-only after P3 defines temporal boundaries.
- P3 must inspect the generated runtime audit reports before protocol freeze.

## P2 verification hardening

- The first successful authoritative UCI acquisition receipt becomes the frozen SHA-256 baseline; later acquisitions must match it.
- Station inventory must equal the 12 named UCI stations exactly, with no missing, unexpected, or repeated identities.
- Original timestamp order is diagnosed before sorting; sorting must not erase backward/zero-step evidence.
- Forecast-window coverage requires every adjacent step from history through target to be exactly one hour.
- Missing-run rows and consecutive missing hours are reported separately/consistently.
- A pinned public UCI-derived mirror was used only for structural preflight, never as a substitute for authoritative UCI byte identity.
- Latest pre-P2 GitHub Actions run failed because `requests` was omitted from the CI install command; the workflow is corrected in this update.
