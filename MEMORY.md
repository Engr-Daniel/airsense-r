# MEMORY.md — AirSense-R Project Memory

Current status (2026-10-13): P6 accepted. Independent Colab verification checked all 1,281 Drive prediction/target bundles and recomputed metrics and bootstrap for all 30 condition/policy reports (42 scopes). All 32 review artifacts and 1,520 original artifacts were checksum-verified locally with matching lineage. See research/P6_COMPLETION_REPORT.md and results/p6/final_acceptance.json. P7 may begin under the frozen protocol using the simpler reconnectable notebook interface. No P6 rerun is needed. Preserve original models, Drive predictions, result branches and interruption evidence. Earlier entries below are historical.

This file stores durable project context so future contributors/agents can resume work without reconstructing prior decisions.

P6 saved-result verifier prepared (2026-10-13): notebook `05b_p6_saved_result_verification.ipynb` provides four cells with embedded settings, automatic review resume, a file-log worker and explicit status. It reads original Drive arrays and the final pinned Git snapshot; independently recomputes metrics and bootstrap using timestamp-frequency weights; pushes each reviewed condition to `results/p6-sensors-01-review-01`. It never fits or predicts. Original 05 remains the historical advanced experiment template. Connected Drive discovery found the prediction folder, but the connector listing did not expose all files; live verification must run against mounted Drive. Final scientific acceptance is still pending that output. See docs/P6_VERIFICATION.md. No P6 experiment rerun or user-entered SHA/stage is needed for 05b.

P6 evaluation execution finished (2026-10-13): run `p6-sensors-01` published completion at result commit `464574140e7abb79094935313d6f3eb44fce3a93`, with all 15 conditions for primary/no-forward-fill policies. User's executed notebook includes a failed duplicate invocation after manually deleting the writer lock, then confirms the surviving process stopped and displays completion/results. Preserve that incident evidence in `05_p6_sensor_degradation_evaluation_executed.ipynb`; source template restored without the lock-deletion edit. Original source and accepted P5 lineage match. Scientific acceptance remains pending independent Drive prediction-file and bootstrap verification; do not call P6 fully accepted or start P7 yet. User requests a simpler automatic run/resume notebook with visible progress, no repeated SHA/stage decisions. Do not require experiment reruns merely to improve its interface.

P6 preflight accepted (2026-10-13): user-run notebook completed all five cells at source `3c9b5d49fb90b30cc967f8d31f9f3c3007b81a0d`, run `p6-sensors-01`. Result commit `9f7b6b199b50f3c514baa8e7e56a566e56665daf` has 25 verified Git artifacts and matching accepted P5 lineage. Ten development replays passed on 103,287 targets each; Colab confirmed accepted clean predictions on 102,753 test targets and persistent-array round trips. Drive arrays/native models were not independently downloaded during this review. Executed notebook preserved separately; see results/p6/preflight_acceptance.json. Next: stage `evaluate` with the SAME source SHA, run ID and original Drive directory. No P5 rerun; P6 scientific completion remains pending. Earlier implementation checkpoints below are historical.

P6 implementation checkpoint (2026-10-12): notebook 05 has explicit preflight/evaluate stages. It preserves accepted P5 selection/models, replays development and clean-test predictions, and saves lossless derived arrays in Drive with incremental Git references. All 15 frozen conditions and 63 realizations are implemented for primary and inference-only no-forward-fill policies. Paired hourly uncertainty preserves station/seed aggregation and matched outage subsets. No real P6 stress results have been generated. See docs/P6_WORKFLOW.md and research/P6_IMPLEMENTATION_DECISIONS.md; live Colab preflight remains required.

## Project identity

P6 local verification (2026-10-12): 75 regression tests and the separate fresh-process P6 notebook lifecycle test passed. The latter verified preflight, interruption/resume, completed-unit reuse, original-model/evidence preservation and bare-Git synchronization. All six current templates have matching source fingerprints. See research/P6_IMPLEMENTATION_REPORT.md. Next user action is notebook 05, new run `p6-sensors-01`, stage `preflight`; review its live evidence before `evaluate`. P5 needs no rerun.

- Name: **AirSense-R**
- Working paper title: **AirSense-R: Do Air-Quality Forecasters Keep Their Rank Under Sensor Degradation and Site Shift?**
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
- Tree-based ML baseline: XGBoost (frozen P3 candidate; substitutions require a protocol amendment)
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
- P4 data-pipeline implementation and acceptance are complete; P5 clean benchmark is next.
- Material post-freeze methodological changes must be recorded in `research/PROTOCOL_DEVIATIONS.md`.

## P4 implementation checkpoint

- Implemented causal preprocessing, station-isolated target-indexed windows, train-only fitting, robust noise scales, categorical dropout, and stream-level stress utilities.
- Added frozen configuration/protocol identity checks, source provenance, atomic immutable run checkpoints, and isolated Git artifact branches with verified resume.
- Added Colab notebooks 01–03. They require the matching published code commit and runtime GitHub credentials; user-run live Colab publication and notebook 03 fresh-runtime recovery were reviewed on 2026-10-09. See results/p4/colab_acceptance.json. Standardized checkout import activation replaces the user's workaround; new revisions require new run IDs. Local tests use explicit fixture setup and bare Git remotes.
- Real UCI P4 verification completed with compact coverage/preprocessing evidence in `results/p4/p4-final/`; no forecasting models or final-test performance were evaluated.
- P4 representation/scaling/persistence/calendar/boundary clarifications are recorded in `research/P4_IMPLEMENTATION_DECISIONS.md` and the protocol deviation log.


## Pre-P5 title and rationale

Canonical study title is the title field in CITATION.cff, adopted 2026-10-09 before P5 results. See research/RESEARCH_RATIONALE.md for independently checked motivation, novelty limits, and falsifiable contribution criteria. The user's research document and subsequent reviewer feedback have been incorporated, with verified additional references and explicit limits on novelty and null-result interpretation. No model family or frozen protocol was changed.

## P5 readiness audit

See research/P5_READINESS_REVIEW.md. Ready for implementation, not immediate full training. Training search/selection settings, model-state recovery, P5 provenance and environment integration remain required. The starter bootstrap uses row blocks rather than timestamp-aware hourly blocks and must not produce headline intervals unchanged. Ridge and a second dataset remain proposals, not adopted protocol changes.

## P5 implementation checkpoint (2026-10-10)

The declared search in configs/p5_training.yaml is locked by configs/p5_identity.json. CPU XGBoost/MLP/GRU adapters support persistent native model snapshots and epoch/round-boundary recovery. Selection is validation-only with equal-station/seed aggregation and the frozen near-tie rule; final-test loading requires its saved record. P5 provenance records the full environment and training settings. Timestamp-aware paired bootstrap and aligned prediction exports are implemented. Notebook 04 uses explicit smoke/select/test stages. P5 full benchmark is NOT complete: live Colab storage smoke and full fitting/evaluation remain pending. See docs/P5_WORKFLOW.md. No ridge/second dataset was added and no final-test performance was inspected.

Local P5 verification: 59 tests passed. The real UCI smoke run p5-local-smoke-20261010 used only Aotizhongxin through 2013-03-10; all three learned models passed interruption/reload comparisons with zero prediction difference. Evidence and limitations are in research/P5_IMPLEMENTATION_REPORT.md. The actual Colab persistent-storage smoke remains pending before long training.

## P5 Colab smoke acceptance (2026-10-10)

User-run notebook 04 used unchanged code at 2201c0ff6d30cd40898cda1716b1b15b47e92bf8, stage smoke, run p5-smoke-01, and mounted Google Drive. All three learned models passed interruption/resume and native reload checks with zero prediction difference. Remote branch results/p5-smoke-01 at 9be8907ac418f9bdb5fb9fd8780334cfcaac84f6 has verified manifest checksums and a completion marker. See results/p5/colab_acceptance.json. Fresh-runtime cloud recovery was not demonstrated by this saved notebook. Ready for select using new run ID p5-clean-01, the same pinned code and model directory; full P5 benchmark remains pending.

Recovery workflow (2026-10-12): use notebook 04b_p5_corrected_test.ipynb and docs/P5_RECOVERY.md, with new correction run p5-clean-01-corrected-01 and original Drive model directory. It verifies frozen native hashes and development predictions before any corrected test scoring; it does not retrain. Corrected live outputs are still pending.

Recovery follow-up: corrected-01 stopped at persistence replay because default CSV parsing changed two decimal labels by 1.42108547e-14. Round-trip parsing now preserves exact labels; no tolerance relaxation. Use the latest notebook 04b with new run p5-clean-01-corrected-02, original models and no retraining. Corrected live scoring remains pending.
