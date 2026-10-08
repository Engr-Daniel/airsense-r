# TASK.md — AirSense-R Execution Plan

## Objective

Complete a scientifically defensible v1 research study, technical manuscript, reproducible repository, and GitHub Pages reliability explorer within a two-day sprint.

## P0 — Repository bootstrap

- [x] Create standard repository structure
- [x] Add `MEMORY.md`
- [x] Add `AGENTS.md`
- [x] Add `TASK.md`
- [x] Add protocol/dataset/experiment documentation templates
- [x] Add GitHub Pages dashboard shell
- [x] Add starter Python package and tests

## P1 — Literature reconnaissance and novelty stress-test

- [x] Search recent air-quality forecasting literature
- [x] Search sensor-missingness / degraded-observation literature
- [x] Search cross-site / spatial-shift generalization literature
- [x] Identify closest prior work
- [x] Freeze precise contribution statement
- [x] Record sources in `research/LITERATURE_NOTES.md`

## P1.5 — Methodology hardening

- [x] Define validation-based model selection
- [x] Add selection regret as a central outcome
- [x] Make paired dependence-aware uncertainty mandatory
- [x] Strengthen site shift to repeated station holdout
- [x] Require stream-level corruption before window construction
- [x] Add contiguous outage sensitivity
- [x] Require training-derived noise scales
- [x] Require shared targets/corruption realizations across models
- [x] Clarify preprocessing as part of evaluated pipeline
- [x] Fix model-artifact `.gitignore` scope
- [x] Add methodology-hardening tests
- [x] Record completion in `research/P1_5_COMPLETION_REPORT.md`

## P2 — Dataset acquisition and audit

- [x] Establish remote-only temporary acquisition from authoritative UCI URL
- [x] Implement strict validation of all 12 unique expected station identities
- [x] Harden timestamp diagnostics to preserve original-order errors before sorting
- [x] Require every internal step in a usable forecast window to be exactly one hour
- [x] Distinguish missing-run rows from verified consecutive missing hours
- [x] Implement reproducible structural audit for missingness, continuity, gaps and provisional usable-window coverage
- [x] Separate full-data structural checks from development-only exploratory/modeling analysis
- [x] Complete independent 12-station structural preflight against a pinned UCI-derived mirror
- [x] Configure Python 3.11 GitHub Actions authoritative audit and checksum-baseline workflow
- [ ] Authoritative UCI Action has produced `acquisition_receipt.json` and structural audit outputs
- [ ] Inspect authoritative outputs and mark P2 dataset verification closed

## P3 — Freeze protocol BEFORE final experiments

- [ ] Finalize hypotheses
- [ ] Finalize forecasting horizon
- [ ] Finalize lookback window
- [ ] Finalize feature set
- [ ] Finalize timestamp-based train/validation/test strategy
- [ ] Finalize clean-validation model-selection rule
- [ ] Finalize practical near-tie threshold
- [ ] Finalize primary imputation policy and one sensitivity policy
- [ ] Finalize repeated held-out-site strategy
- [ ] Finalize corruption levels
- [ ] Finalize model families
- [ ] Finalize metrics/statistical analysis including selection regret and temporal-block bootstrap
- [ ] Set protocol status to `FROZEN` in `research/PROTOCOL.md`

## P4 — Data pipeline

- [ ] Parse and combine station files
- [ ] Construct timestamp
- [ ] Sort and validate time order
- [ ] Implement missing-value policy
- [ ] Build lag/window features without leakage
- [ ] Fit train-only preprocessing
- [ ] Persist processed data metadata

## P5 — Clean benchmark

- [ ] Persistence baseline
- [ ] Tree-based ML model
- [ ] MLP
- [ ] GRU
- [ ] Save predictions and metrics
- [ ] Compare against persistence

## P6 — Sensor degradation

- [ ] Random feature dropout at frozen severities
- [ ] Whole-variable dropout at frozen channels
- [ ] Measurement-noise injection at frozen severities
- [ ] Re-evaluate frozen models without retraining unless protocol specifies otherwise
- [ ] Compute RPD

## P7 — Site shift

- [ ] Train without held-out site(s)
- [ ] Evaluate on unseen site(s)
- [ ] Quantify cross-site generalization performance (do not call it a penalty without matched comparator)
- [ ] Compare model ranking stability

## P8 — Statistical and failure analysis

- [ ] Compute required paired dependence-aware uncertainty / temporal-block bootstrap intervals
- [ ] Analyze worst-error cases
- [ ] Check error by pollution regime
- [ ] Check whether clean ranking persists under degradation
- [ ] Create publication figures/tables

## P9 — Paper

- [ ] Abstract
- [ ] Introduction
- [ ] Related work
- [ ] Dataset
- [ ] Methods
- [ ] Experimental protocol
- [ ] Results
- [ ] Discussion
- [ ] Limitations
- [ ] Future work / Edge-ML path
- [ ] Conclusion

## P10 — GitHub Pages explorer

- [ ] Export dashboard-ready result JSON/CSV
- [ ] Model selector
- [ ] Condition selector
- [ ] Severity selector
- [ ] Station/site selector
- [ ] Actual vs predicted plot
- [ ] Metrics + RPD cards
- [ ] Model comparison chart
- [ ] Methodology/about panel
- [ ] Validate static deployment from `/docs`

## P11 — Release

- [ ] Run tests
- [ ] Re-run core experiment from clean environment
- [ ] Check README commands
- [ ] Add final figures
- [ ] Complete citation metadata
- [ ] Tag `v1.0.0`

## Out of v1 scope

- Real embedded/Edge deployment
- Anomaly detection as a second major task
- Transformers or large architecture search
- Real-time backend hosting
- Claims based on private/proprietary sensor data
