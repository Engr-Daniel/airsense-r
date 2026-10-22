# P8 implementation decisions — 2026-10-22

P5/P6 results and P7 aggregate outputs have already been inspected. This record
is therefore **post-results**, not a preregistration. The frozen protocol and
all prior predictions, fitting, tuning, selection rules and budgets are unchanged.

## Acceptance gate and lineage

P7 execution finished at `73c32f0b2cd7fcf447f9483413561b7104536e7f`.
Its local execution review is not scientific acceptance. P8 first verifies the
pinned Git manifest, all referenced Drive prediction CSV bytes, final native model
bytes and identities, preprocessing station/time exclusion, and frozen selection
lineage. It recomputes metrics directly from saved predictions and independently
reconstructs paired calendar moving-block uncertainty with timestamp frequency
weights, rather than the production prefix-sum implementation. Comparisons use
`atol=1e-8`, `rtol=1e-10` for summation-order agreement; these are not model-replay
tolerances. No fitting, model prediction or raw-data acquisition occurs.

P6 inputs are pinned to its final accepted snapshot and independent verification
receipt. All saved prediction/target bundles are checksum-verified again. Its
headline uncertainty is reused with explicit accepted-source attribution, not
represented as a newly computed P8 analysis.

## Descriptive diagnostics

Configuration is `configs/p8_analysis.yaml`. Concentration bands are `<50`,
`50 to <100`, `100 to <200`, and `>=200` micrograms per cubic metre, based on the
observed target. These exploratory bands are neither health thresholds nor AQI
categories. Seasons are calendar DJF/MAM/JJA/SON. The five largest mean absolute
errors per station/model/condition are exported with timestamps and target values.
These choices were made after aggregate outcomes were available; no subgroup
significance tests or confirmatory claims are authorized by them.

Compute each realization's absolute error before averaging over fitted seeds
and corruption seeds. Do not score the mean prediction as if it were an ensemble.
Aggregate within each station first, then give equal weight to nonempty stations.
Report station/target counts because subgroup coverage can differ. Mean prediction
in worst-case exports is descriptive only; absolute error remains mean seed error.
P6 diagnostic tables cover the full test period; accepted ranking/uncertainty
summaries retain both full-period and matched affected-window outage scopes.

Report P7 station-specific validation-to-test rankings, Kendall tau-b, practical
near-ties and selection regret with its independently checked intervals. P7 is
within-Beijing generalization, not a causal penalty or inter-city transfer.
Uncertainty remains conditional on fitted seeds and observed stations. Additional
plots do not add independent experiments or justify stronger novelty claims.

## Repository maintenance and operation

The user authorized cleanup and P8 preparation after P7 execution. Dependency
versions now have one definition in `pyproject.toml`, with optional training,
notebook and development groups. `requirements.txt` is a convenience entry point.
This is not a complete transitive environment lock. Historical commits and pinned
recovery notebooks retain the original experiment environments. Executed notebooks
are relocated byte-for-byte with an index mapping old paths and SHA-256 digests;
original receipts retain their historical paths.

Notebook 07 provides one embedded-revision, four-cell workflow with a reconnectable
worker, incremental checkpoints and a single analysis branch. Live Colab execution
and independent output review remain required before claiming P8 complete.
