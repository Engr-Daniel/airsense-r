# Experiment Plan

This file summarizes the frozen experiment families. `research/PROTOCOL.md` is authoritative.

## E0 — Training-only tuning and clean validation selection

Tune XGBoost, MLP, and GRU only within the frozen training period using the three expanding-window folds in `research/PROTOCOL.md`. Refit each tuned family on the full training period, then select exactly one deployable family using unweighted mean station-level clean validation MAE. Persistence is untuned.

Candidates within 1.0 µg/m³ validation MAE are practical near-ties and are resolved by fixed simplicity order: persistence → XGBoost → MLP → GRU.

## E1 — Clean final-test benchmark

Evaluate persistence, XGBoost, MLP, and GRU on identical clean final-test station-target rows from 2016-03-01 through 2017-02-28. Report station-specific metrics, equal-weight station aggregates, model rank, and the retrospective test oracle. The test oracle is descriptive only.

## E2 — Random observation dropout

Apply 10%, 30%, and 50% Bernoulli masking to non-target input channels on the chronological evaluation stream before window construction. Historical PM2.5 and future targets remain uncorrupted. Use the same corruption realization for every model.

## E3 — Whole-channel loss

Evaluate complete loss of NO2, CO, and TEMP separately. The frozen clean-trained pipelines and missing-data policy must absorb the unavailable channel; no stress retraining is allowed.

## E4 — Contiguous outage sensitivity

Evaluate 6-hour and 12-hour outages separately on NO2, CO, and TEMP. For every station/channel/duration/corruption seed, create one seeded outage event per calendar month of the final test year. Report both full-period results and metrics restricted to forecast windows whose input history intersects an outage.

## E5 — Measurement-noise stress

Inject independent zero-mean Gaussian noise at 5%, 10%, and 20% of a training-only robust feature scale (`IQR / 1.349`, falling back to training standard deviation when required). Historical PM2.5 is excluded from the primary noise intervention. Naturally non-negative variables are clipped at zero after injection.

## E6 — Repeated unseen-site evaluation

Run 12 leave-one-station-out folds. The held-out station is excluded from fitting, preprocessing, tuning, and selection. Model-family selection is repeated using only the remaining 11 stations' clean validation data. Evaluate the held-out station on final-test targets while allowing its recent local observations as inputs.

## E7 — Imputation sensitivity

Repeat the central clean/stress comparisons with the predefined sensitivity imputer: training-only median/category fallback, no forward fill, same missingness indicators. This analysis tests whether model-ranking conclusions are dominated by the primary six-hour causal carry-forward policy.

## Core outcomes

For each applicable condition, record:

- MAE, RMSE, and R²;
- RPD relative to the same model's clean performance;
- candidate ranking and rank change;
- winner retention;
- selection regret relative to the retrospective stressed-test oracle;
- 95% paired moving-block bootstrap intervals using 24-hour blocks and 2,000 replicates;
- training/corruption seed metadata;
- station-specific results before equal-weight station aggregation.

The scientific emphasis is whether clean-validation selection incurs **meaningful additional forecasting error under deployment stress**, not merely whether numeric ranks change.
