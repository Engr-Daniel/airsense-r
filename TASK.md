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

## P2 — Dataset acquisition and audit

- [ ] Download UCI Beijing Multi-Site Air Quality dataset
- [ ] Verify file inventory and station coverage
- [ ] Audit missingness, timestamp continuity, distributions, outliers
- [ ] Confirm target and usable features
- [ ] Save audit summary

## P3 — Freeze protocol BEFORE final experiments

- [ ] Finalize hypotheses
- [ ] Finalize forecasting horizon
- [ ] Finalize lookback window
- [ ] Finalize feature set
- [ ] Finalize train/validation/test strategy
- [ ] Finalize held-out site strategy
- [ ] Finalize corruption levels
- [ ] Finalize model families
- [ ] Finalize metrics/statistical analysis
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
- [ ] Quantify generalization penalty
- [ ] Compare model ranking stability

## P8 — Statistical and failure analysis

- [ ] Bootstrap confidence intervals where feasible
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
