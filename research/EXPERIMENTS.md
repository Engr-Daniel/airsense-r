# Experiment Plan

This file summarizes the experiment families. `research/PROTOCOL.md` is authoritative once frozen.

## E0 — Model selection on clean validation data

Train/tune candidate pipelines on development data and select exactly one model using clean validation MAE. The final test set must not influence selection.

## E1 — Clean test benchmark

Evaluate persistence, tree-based ML, MLP, and GRU on identical clean test station-timestamp targets. Report absolute metrics and descriptive test ranking.

## E2 — Random observation dropout

Corrupt the chronological input stream before window construction at frozen severities. Preserve future targets. Use the same corruption realization for every model.

## E3 — Whole-channel loss

Remove predefined sensor channels consistently from the evaluation stream. Evaluate complete pipelines, including imputation.

## E4 — Contiguous outage sensitivity

Apply predefined 6/12-hour continuous outages to selected input channels before windowing. This tests realistic continuity failures without expanding the core model set.

## E5 — Measurement-noise stress

Inject noise using scales estimated from training data only. Test statistics must not set noise severity.

## E6 — Repeated unseen-site evaluation

Prefer leave-one-station-out evaluation across all feasible stations. The held-out station is excluded from fitting and preprocessing, but recent local observations may be used at inference.

## Core decision outcomes

For each stress condition, record:

- absolute MAE/RMSE/R²;
- RPD relative to the same model's clean performance;
- candidate ranking and rank change;
- whether the clean-validation-selected winner is retained;
- **selection regret** relative to the retrospective stressed-test oracle;
- paired uncertainty estimates.

The scientific emphasis is not merely whether rankings change, but whether clean validation selection incurs meaningful additional forecasting error under stress.
