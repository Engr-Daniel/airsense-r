# P5 readiness review

Date: 2026-10-09. Reviewed baseline: c6cdc1258f98f188cc2f83be6bd7d72e9e83d1d1.

## Verdict

Ready to begin P5 implementation; not ready to launch the full benchmark today.
P4 completion remains valid. P5 intentionally introduces model fitting and training
recovery, so passing P4 tests does not establish readiness of those missing components.
No model training or final-test performance inspection was performed in this review.

## Verification result

Full existing suite: **46 passed in 68.60 seconds** on 2026-10-09. These are
P4/current-utility tests, not proof of as-yet-unimplemented P5 training behavior.

## Verified foundation

- Local main and origin/main matched at review start; working tree was clean.
- Frozen configuration/protocol hashes and the dataset receipt agree.
- All three current notebooks embed the current source fingerprint.
- Causal preprocessing and window tests cover future/held-out fit invariance,
  forward-fill caps, station isolation, target preservation and input equivalence.
- User-run Colab execution and recovery evidence is retained at original revisions.
- Completed result branches have been archived with their manifests; start new P5 IDs.
- Canonical title and research rationale are established before results.

## Gates before long training

### 1. Declare the actual training plan

configs/experiment.yaml fixes families, folds and seeds, but contains no model
search spaces, architectures, optimizer/loss choices, batch sizes, epoch/tree
budgets, early-stopping rules, or deterministic hyperparameter-tie resolution.
Declare these before seeing tuning scores. Preserve the frozen original-unit
target convention and common input representation.

Define how tuning scores combine folds, stations and seeds, and how training
duration is chosen for full-training refits. Early stopping must not consume final
test data or turn outer validation into an extra hyperparameter-tuning set.

Adding ridge was discussed but never adopted in the protocol. Keep the frozen
four families unless an explicit amendment changes the candidates and simplicity
order before scores are viewed. Do not silently substitute HistGradientBoosting
for XGBoost; the old MEMORY fallback wording was stale and is corrected.

### 2. Implement and test actual selection, not only regret arithmetic

src/airsense_r/models currently contains only a persistence helper.
There is no P5 runner or executable family selector. tests/test_selection.py tests
regret and winner equality, not equal-station aggregation, the 1.0 near-tie rule,
seed aggregation or exclusion of test labels from selection.

P5 needs a persisted selection decision made from clean validation only, followed
by a separate final-test evaluation entry point that requires that decision.
Test unequal station counts, near-ties and the fixed simplicity ordering.
Use window.persistence (the frozen imputed last input), not a new observed-only
baseline with a different target population.

### 3. Add model-state recovery

RunStore permits compact immutable approved artifacts up to 10 MiB; it is not a
model-training checkpoint store. No persistent model destination or interrupted-fit
resume path exists yet. Define model serialization, optimizer/epoch/random-state
recovery where supported, file checksums and manifest references, and test restore
after a simulated interruption. Completed-model restart must not be described as
mid-fit resume. Large binaries belong in configured persistent storage, not Git.
Choose and verify the actual storage destination in Colab before long fits.

### 4. Extend P5 provenance and environment validation

artifacts.provenance records numpy, pandas, sklearn, PyYAML and requests, but not
XGBoost, TensorFlow/Keras or training hardware. source_hash includes P4 requirements
and experiment.yaml, but would not automatically include a new P5 search config,
a new lock file, or training extras in pyproject.toml.

Extend provenance to cover all effective P5 settings, library versions, seeds and
the relevant CPU/GPU/determinism settings. Snapshot a reproducible environment.
Current CI installs only requirements-p4.txt and cannot validate absent training
dependencies. Consolidating dependencies into extras is reasonable, but is not
itself the readiness criterion: a tested, recorded P5 environment is.

## Evaluation issue found before results

src/airsense_r/evaluation/bootstrap.py is a starter pairwise helper.
It samples contiguous array rows, receives no timestamps/station IDs, and defaults
to 1,000 replicates with seed 42, whereas the protocol specifies 2,000 and 424242.
P4 windows exclude missing targets, so 24 retained rows need not be 24 consecutive
hours; concatenated station arrays could also produce blocks across station borders.

Do not use the helper unchanged for headline intervals. Implement explicit hourly
alignment, appropriate station/seed aggregation, paired sampling and the frozen
parameters before headline analysis. Define the treatment of missing target hours
and cross-station pairing before inspecting final results. Selection-regret intervals
also require the appropriate multi-model statistic; the pairwise helper alone does
not implement them. P5 must preserve station/timestamp/model/seed/partition keys and
original targets in prediction exports so P8 can perform valid analysis.

## Remaining P5 implementation deliverables

- XGBoost, MLP and GRU adapters; training-only tuning and full-training refits.
- Bounded-memory batch/materialization strategy and a small resource smoke test.
- Shared target-key checks and original-unit predictions; per-station and
  equal-station aggregate metrics.
- Versioned config, preprocessing, fitted models and completed-unit checkpoints.
- Prediction shards compatible with artifact size limits and later stress evaluation.
- Notebook 04, plots and dashboard-ready exports with explicit permitted partitions.
- Persistence and model save/load checks; deterministic repeatability checks where
  supported; failure/recovery checks for the actual training workflow.

## Review feedback disposition

Completed: canonical title in repository files; rationale refinement; exact split
dates and phase table in README; mandatory uncertainty wording; archived branches.
Deferred intentionally: a second dataset, ridge, and optional rank correlation.
These are not silently added to the frozen experiment.

Keep AGENTS.md at root. Moving planning files is optional and not a scientific
prerequisite. The GitHub About description was not checked in this local code audit.
The bootstrap still gives a generic checkout-mismatch error; improving that message
is useful within P5 notebook work but is not a scientific blocker.

## Recommended execution order

1. Declare and record P5 training/selection/storage decisions.
2. Implement adapters, runner, provenance and recovery.
3. Pass synthetic integration tests and a small training-only Colab smoke run.
4. Run the frozen tuning/refit/clean-validation workflow and persist selection.
5. Evaluate the untouched final test only after selection is locked.
6. Complete P5 analysis and exports before proceeding to degradation experiments.

No experimental protocol or model family was changed by this audit.
