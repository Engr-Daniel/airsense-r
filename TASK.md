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
- [x] Verify authoritative file/station metadata and implement runtime inventory verification
- [x] Implement reproducible structural audit for missingness, timestamp continuity, gaps and suspicious values (distribution-driven EDA deferred to development data)
- [x] Record source/units/station inventory and implement runtime SHA-256, duplicate, gap and missing-run evidence outputs
- [x] Implement station-level observed-target and provisional usable-window coverage reporting
- [x] Separate full-data structural checks from development-only exploratory/modeling analysis
- [x] Confirm PM2.5 target and raw pollutant/meteorological feature inventory
- [x] Complete dataset card + P2 report and define compact `audit/` output contract
- [x] Authoritative UCI Action produced and committed the frozen acquisition receipt + structural reports
- [x] Inspect authoritative outputs and close P2 dataset verification

## P3 — Freeze protocol BEFORE final experiments

- [x] Finalize hypotheses
- [x] Finalize forecasting horizon
- [x] Finalize lookback window
- [x] Finalize feature set
- [x] Finalize timestamp-based train/validation/test strategy
- [x] Finalize clean-validation model-selection rule
- [x] Finalize practical near-tie threshold
- [x] Finalize primary imputation policy and one sensitivity policy
- [x] Finalize repeated held-out-site strategy
- [x] Finalize corruption levels
- [x] Finalize model families
- [x] Finalize metrics/statistical analysis including selection regret and temporal-block bootstrap
- [x] Set protocol status to `FROZEN` in `research/PROTOCOL.md`
- [x] Record completion in `research/P3_COMPLETION_REPORT.md`

## P4 — Data pipeline

- [x] Parse and combine station files
- [x] Construct timestamp
- [x] Sort and validate time order
- [x] Implement missing-value policy
- [x] Build lag/window features without leakage
- [x] Fit train-only preprocessing
- [x] Persist processed data metadata
- [x] Implement provenance-validated artifact loaders and frozen-configuration checks
- [x] Implement atomic incremental checkpoints, automatic Git artifact synchronization, and verified resume support (local bare-remote integration tests)
- [x] Test interrupted writes, failed pushes, provenance mismatch, and artifact-only staging
- [x] Build notebooks 01–03 under `notebooks/` following `docs/NOTEBOOK_GUIDE.md`
- [x] Add pinned-revision Colab bootstrap; execute notebook analysis and checkpoint/resume paths in fresh local processes/kernels using explicit fixture setup
- [x] Complete live Colab acceptance: user-executed notebooks with import workaround, GitHub checkpoint publication, and notebook 03 fresh-runtime recovery reviewed on 2026-10-09

P4 implementation, local verification, and user-run live Colab acceptance are complete. The standardized bootstrap fix is covered by local regression tests; live evidence used the user's equivalent import workaround. See `research/P4_COMPLETION_REPORT.md`.

## P5 — Clean benchmark

- [ ] Persistence baseline
- [ ] Tree-based ML model
- [ ] MLP
- [ ] GRU
- [ ] Save predictions and metrics
- [ ] Compare against persistence
- [ ] Build `notebooks/04_p5_clean_benchmark_analysis.ipynb`

## P6 — Sensor degradation

- [ ] Random feature dropout at frozen severities
- [ ] Whole-variable dropout at frozen channels
- [ ] Measurement-noise injection at frozen severities
- [ ] Re-evaluate frozen models without retraining unless protocol specifies otherwise
- [ ] Compute RPD
- [ ] Build `notebooks/05_p6_sensor_degradation_analysis.ipynb`

## P7 — Site shift

- [ ] Train without held-out site(s)
- [ ] Evaluate on unseen site(s)
- [ ] Quantify cross-site generalization performance (do not call it a penalty without matched comparator)
- [ ] Compare model ranking stability
- [ ] Build `notebooks/06_p7_site_shift_analysis.ipynb`

## P8 — Statistical and failure analysis

- [ ] Compute required paired dependence-aware uncertainty / temporal-block bootstrap intervals
- [ ] Analyze worst-error cases
- [ ] Check error by pollution regime
- [ ] Check whether clean ranking persists under degradation
- [ ] Create publication figures/tables
- [ ] Build `notebooks/07_p8_statistical_failure_analysis.ipynb`

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
