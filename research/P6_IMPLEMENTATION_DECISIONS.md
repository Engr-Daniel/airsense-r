# P6 implementation decisions

Declared 2026-10-12 after clean P5 test inspection, before any real P6 stress scores.
The frozen protocol and experiment YAML remain unchanged. These decisions resolve
execution, aggregation and storage details; they are not tuned using stress outcomes.

- Reuse the exact original `p5-clean-01` models and validation selection. The accepted
  clean comparator is corrected run `p5-clean-01-corrected-02` at result commit
  `118ae94a23517319d1c31b1159f25a9b77f6b230`. No model fitting is permitted.
- Preflight replays all original development predictions, confirms native model
  hashes, and matches accepted clean-test predictions before evaluating new stresses.
  Replay uses exact target deserialization and the existing `atol=1e-5`, `rtol=1e-6`
  prediction tolerances. This is not a test-based tuning step.
- Execute all 15 frozen stress settings. Five corruption seeds apply to random
  dropout, noise and outages. Whole-channel loss is deterministic and has one
  realization tagged seed -1. This produces 63 realizations per imputation policy.
- Primary imputation is unchanged. The frozen no-forward-fill sensitivity is an
  **inference-only** preprocessing intervention: retain original training medians,
  vocabulary, scaling statistics, trained models and family selection. Compare it
  to its own no-forward-fill clean baseline. It does not estimate the performance
  of a separately trained no-forward-fill pipeline. Evaluate the full matrix for
  both policies rather than selecting a subset after seeing scores.
- Reuse P4's station-seeded chronological corruption operators and boundary rules:
  start 24 hours before the first test target, end at the final forecast origin;
  monthly outages occur within test-year months. Preserve historical PM2.5 and
  all original targets. Noise scales use raw training rows through 2015-02-28 only.
- Apply one realization before windowing and share it across all models and seeds.
  Retain seed/channel/event schedules, changed-cell counts and a hash of the stressed
  observation interval. Realizations are regenerated deterministically; no raw data
  or full perturbed observation streams are retained.
- Save lossless compressed prediction arrays to the explicit persistent Drive
  directory under `p6-artifacts/<run-id>`. Store keys/targets once; each model/seed
  prediction unit has a checksummed immutable Git reference. Native NPZ loading
  forbids pickled objects. Git stores lineage, references, metrics, plots and exports.
  A pending model's inference may repeat after interruption; there is no model
  training to resume. Failed publication stops computation. One writer per run.
- For each station compute MAE/RMSE/R² per training and corruption seed. Average
  training-seed metrics, then corruption realizations, then stations equally. RPD
  is the percentage change in this aggregate MAE against the matched clean aggregate,
  not the average of hourly percentages. Numerical ranks use average ranks for exact
  ties. Report numerical winner retention, frozen practical near-ties and Kendall
  tau-b as descriptive measures; none replaces the paired uncertainty rule.
- Outage-affected targets have input windows intersecting an event, including its
  final affected observation. Save both full-period and affected-window reports.
  Match clean and stressed subsets within each realization; different outage seeds
  can have different subsets, so aggregate each realization's station metric before
  averaging seeds. Do not pool their rows as independent samples.
- Paired 24-hour calendar bootstrap uses the frozen 2,000 replicates and seed424242.
  Share sampled times across models, clean/stress, stations and corruption realizations.
  Average fitted-seed absolute errors before resampling; average each realization's
  station error after resampling. Recompute the retrospective oracle each replicate.
  Report selected-minus-comparator MAE, selection regret, and station-level
  stressed-minus-clean MAE intervals. They are conditional on the fitted and
  corruption seed sets, not a separate resampling of training runs.
- A sparse affected-window replicate with no eligible observations for any
  station/realization yields an explicitly unavailable sensitivity interval. Do not
  redraw until success or replace it with independent-row bootstrap. Full-period
  headline intervals must be available before marking a condition complete.
- Scientific completion requires every condition, both policies, all seeds, a
  verified dashboard export and live output review. Local engineering tests do not
  count as real P6 experimental completion. Preserve all P5 evidence and disclosures.
