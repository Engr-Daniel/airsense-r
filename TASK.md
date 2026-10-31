# TASK.md — AirSense-R Execution Plan

## Objective

Complete a scientifically defensible v1 research study, technical manuscript, reproducible repository, and GitHub Pages reliability explorer, with independent verification before phase acceptance.

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

Readiness review: [research/P5_READINESS_REVIEW.md](research/P5_READINESS_REVIEW.md).
P5 is complete after corrected evaluation and independent review on 2026-10-12. See [research/P5_COMPLETION_REPORT.md](research/P5_COMPLETION_REPORT.md). P6 implementation may begin; models and validation selection remain frozen. Completed gates:

- [x] Declare search spaces, architecture/training budgets, early stopping and tuning aggregation before scores
- [x] Test equal-station/seed aggregation, near-tie selection and final-test access gate
- [x] Implement configurable persistent model-state storage and verify interrupted-training recovery locally
- [x] Confirm Colab Drive mount and in-process interruption/reload using notebook 04 smoke (fresh-runtime cloud recovery not demonstrated)
- [x] Extend provenance to P5 settings, training libraries and runtime hardware; validate local CPU training environment
- [x] Implement timestamp-aware uncertainty integration and aligned prediction exports; validate on synthetic fixtures
- [x] Pass bounded real-data training-only local smoke and fresh-process model reload
- [x] Pass a bounded training-only Colab smoke run before long fits; remote artifact checksums reviewed (see results/p5/colab_acceptance.json)

- [x] Persistence baseline
- [x] Tree-based ML model
- [x] MLP
- [x] GRU
- [x] Save predictions and metrics
- [x] Compare against persistence
- [x] Prepare provenance-preserving correction notebook 04b and validation-replay gate
- [x] Validate restored-model development predictions and perform separately versioned corrected test scoring (2026-10-12 preprocessing incident)
- [x] Build `notebooks/04_p5_clean_benchmark_analysis.ipynb`

## P6 — Sensor degradation

P6 was accepted on 2026-10-13 after independent verification of all saved
prediction files, metrics and uncertainty. See
[research/P6_COMPLETION_REPORT.md](research/P6_COMPLETION_REPORT.md),
[docs/P6_WORKFLOW.md](docs/P6_WORKFLOW.md) and
[research/P6_IMPLEMENTATION_DECISIONS.md](research/P6_IMPLEMENTATION_DECISIONS.md).

- [x] Implement frozen-model replay gates, persistent predictions and paired stress summaries
- [x] Complete local lifecycle verification and review before notebook handoff (75 regression tests plus the fresh-process P6 lifecycle test passed)
- [x] Review user-run Colab P6 preflight before full evaluation (2026-10-13; 25 Git artifacts verified; see results/p6/preflight_acceptance.json)
- [x] Preserve completed evaluation notebook, including the failed duplicate invocation and successful final inspection
- [x] Independently verify final Drive prediction files and recompute uncertainty before scientific acceptance
- [x] Provide automatic settings, run/resume and visible status for the next P6 step in notebook 05b; historical experiment notebook 05 remains unchanged apart from its source fingerprint
- [x] Review live notebook 05b output before final P6 acceptance

- [x] Random feature dropout at frozen severities
- [x] Whole-variable dropout at frozen channels
- [x] Measurement-noise injection at frozen severities
- [x] Contiguous outages with full-period and affected-window reports
- [x] Re-evaluate frozen models without retraining unless protocol specifies otherwise
- [x] Compute RPD
- [x] Build `notebooks/05_p6_sensor_degradation_analysis.ipynb`

## P7 — Site shift

P7 execution and independent verification are complete. The P8 Colab verifier
checked saved Drive predictions, native model lineage, metrics and uncertainty;
published verification evidence passed local review on 2026-10-22. See
[P8 completion review](research/P8_COMPLETION_REPORT.md).

- [x] Implement the reconnectable notebook interface with embedded settings for P7 execution
- [x] Implement per-fold tuning, all-fold selection freeze and native development replay before test access
- [x] Implement one result branch, persistent prediction references and automatic checkpoint recovery
- [x] Declare fold-specific selection regret and paired uncertainty before P7 results
- [x] Complete local regression and fresh-process lifecycle verification before notebook handoff
- [x] Review live Colab completion, independently verify saved predictions/metrics/uncertainty, and accept P7
- [x] Train without held-out site(s)
- [x] Evaluate on unseen site(s)
- [x] Quantify cross-site generalization performance (do not call it a penalty without matched comparator)
- [x] Compare model ranking stability
- [x] Build `notebooks/06_p7_site_shift_analysis.ipynb`

## P8 — Statistical and failure analysis

Completed and reviewed on 2026-10-22. See [the completion report](research/P8_COMPLETION_REPORT.md).
Subgroup diagnostics remain exploratory; final figure layout/captions belong to P9.

- [x] Consolidate dependencies and preserve executed notebooks separately
- [x] Implement independent P7 prediction/native-lineage/uncertainty verification
- [x] Implement resumable descriptive diagnostics and exported tables/figures
- [x] Verify local regression, native interruption/recovery, notebook execution and pinned Git inputs

- [x] Compute required paired dependence-aware uncertainty / temporal-block bootstrap intervals
- [x] Analyze worst-error cases
- [x] Check error by pollution regime
- [x] Check whether clean ranking persists under degradation
- [x] Create publication figures/tables
- [x] Build `notebooks/07_p8_statistical_failure_analysis.ipynb`

## P9 — Paper

First complete manuscript draft prepared from accepted results; see [paper/manuscript.md](paper/manuscript.md).
The checks below indicate drafted sections, not journal submission readiness.
Publication figures and seven supplementary tables are generated from accepted evidence.

Post-results checkpoint authorized 2026-10-29; primary P5–P8 remains accepted
and unchanged. See [checkpoint plan](research/P9_CHECKPOINT_PLAN.md).

- [x] Declare bounded PM2.5 dropout/outage extension and record post-results status
- [x] Generate separate interpretation and counterfactual-selection tolerance tables
- [x] Document focused prior-work comparison and cautious contribution wording
- [x] Complete target-history Colab execution; verify Git checksums, lineage and metric aggregation; preserve executed notebook
- [x] Independently verify final saved target-history Drive predictions and uncertainty before scientific acceptance
- [x] Prepare and locally test pinned read-only notebook 08b; live verification accepted 2026-10-30
- [x] Integrate accepted target-history findings, including adverse outage-affected result, then close bounded experiments

The full-text Semper et al. comparison remains a submission check; the focused
audit distinguishes inspected abstract/minimal code from unavailable full text.

- [x] Abstract
- [x] Introduction
- [x] Related work
- [x] Dataset
- [x] Methods
- [x] Experimental protocol
- [x] Results
- [x] Discussion
- [x] Limitations
- [x] Future work / Edge-ML path
- [x] Conclusion

- [x] Technical edit of Overleaf draft: chronology, aggregation, uncertainty, selection diagram, outage intervals and correction disclosure
- [x] Build and verify rank/regret, absolute-error stress and descriptive subgroup figures from accepted evidence; integrate main-paper and supplementary assets
- [x] Compile and inspect revised Overleaf PDF for layout, overflow and references (local Tectonic; main 8 pages, supplement 1 page)
- [ ] Resolve title and author-name differences between Overleaf and repository citation metadata
- [x] Record confirmed affiliation (Ormedian Research Group) and correspondence (oyewaledanieloyewola@gmail.com)
- [ ] Author review of contributions and remaining declarations
- [ ] Target-journal formatting and final citation/novelty review
- [ ] Public release plan for large prediction/model artifacts before submission

## P10 — GitHub Pages explorer

Scope (2026-10-31): a deployment-styled reliability decision-support explorer built
only from accepted evidence. It is not a live deployment. A separate Deployment concept
page is explicitly labelled as not evaluated. A real deployment dashboard needs live data
and remains out of v1 scope.

- [x] Export dashboard-ready result JSON (`scripts/build_explorer_data.py`; checksum-verified, clean MAE recomputed from 60 prediction files)
- [x] Overview decision dashboard (selected family, clean/sensor/station/target-history status tiles, all-scope regret strip)
- [x] Clean benchmark with step-through selection rule
- [x] Model selector / training-seed selector for prediction windows
- [x] Condition, severity, policy and scope selectors (sensor and PM2.5-history stress)
- [x] Station/site selector with per-station evidence
- [x] Actual vs predicted plot (fixed calendar weeks, seeds never averaged)
- [x] Metrics + RPD cards and model comparison charts/tables
- [x] Practical-threshold sensitivity control (1.0 frozen; others labelled post-results)
- [x] Failure analysis, methodology, deployment concept and about/provenance pages
- [x] Local static rendering check (headless Chrome, light/dark) and export tests
- [x] Validate live GitHub Pages deployment from `/docs` (2026-10-31, commit 927ee2f: served bytes match commit; all nine routes render without errors)

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
