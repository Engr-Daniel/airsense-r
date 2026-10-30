# Protocol Deviations

Record every change made after `PROTOCOL.md` is marked **FROZEN**.

2026-10-30 P9 saved-prediction review: target-history outcomes HAVE been inspected.
Extend the independent saved-array verifier with an explicit target-history mode;
P6 retains its unchanged-persistence check. P9 verifies the predefined five
conditions, allowing persistence predictions to change under PM2.5 missingness.
No predictions, estimands, thresholds, seeds, tolerances or original evidence
change. The separate review notebook recomputes metrics and bootstrap intervals
from saved arrays without model fitting or inference.

2026-10-29 P9 post-results extension: P5–P8 outcomes HAVE been inspected.
The user authorized a bounded target-history checkpoint and tolerance audit;
see `P9_CHECKPOINT_PLAN.md`. The original protocol and accepted evidence remain
unchanged. Additional evaluation uses frozen models with PM2.5 input dropout
(10/30/50%) and outages (6/12 hours), primary imputation only, original labels,
seeds and paired uncertainty. Separate descriptive sensitivity considers
0.5/1/1.5/2 tolerances without replacing the primary rule. No retraining,
test-based model choice, additional architecture, drift or adaptive policy.
This probes the protected target-history limitation and dependence on the
practical tolerance; results may weaken or narrow the existing interpretation.

2026-10-20 P7 recovery correction: replacement Colab runtimes changed their
preinstalled package inventories and prevented resume despite unchanged core
model/data package versions. A separately pinned recovery adapter retains the
original scientific source, experiment identity and native model identities.
It restores exact original versions throughout the active scientific dependency
closure, permits unrelated inventory changes only, and records the actual
environment separately. Completed selections undergo saved development prediction
replay before further training; final-test gates and tolerances are unchanged.
P5/P6 results have been inspected, but no P7 final-test results exist at the
time of this correction. No budgets, station splits, seeds, model candidates,
selection rules or statistical estimands change. Originals remain immutable.

| Date | Protocol item | Change | Reason | Expected impact |
|---|---|---|---|---|
| 2026-10-08 | P3 sections 6–13, input representation and preprocessing | Clarified training-statistic scope, numeric scaling, input layout, leap-year encoding, persistence fallback, eligibility, and stress-boundary history in `P4_IMPLEMENTATION_DECISIONS.md` | Make unspecified implementation choices explicit before model execution | No final-test performance inspected; choices affect model inputs and are recorded before evaluation |

| 2026-10-10 | P3 sections 9, 14, 17, 19 | Declared bounded training search, fixed budgets without early stopping, seed/fold aggregation, CPU execution, persistent model recovery, and timestamp-aware paired bootstrap in P5_IMPLEMENTATION_DECISIONS.md and configs/p5_training.yaml | Resolve implementation details before any model scores | No final-test outcomes inspected; four families, splits, stress levels and frozen uncertainty parameters unchanged |
| 2026-10-12 | P3 sections 7, 11, 19; restored preprocessing input order | Align saved scaling statistics to the original numeric column order; invalidate original P5 neural test predictions and require separately versioned corrected scoring with frozen models | Sorted JSON mapping keys caused pandas to reorder scaled inputs after reload; reproduced on synthetic data | Final-test outcomes HAVE been inspected. No retuning, refitting, selection change or protocol-parameter change is authorized by this correction. Original artifacts retained; see P5_TEST_REVIEW.md |
| 2026-10-12 | P3 section 19; corrective evaluation lineage | Dedicated correction run imports frozen development evidence and original model hashes; records old/new environments; requires exact preprocessing replay and validation prediction agreement (`atol=1e-5`, `rtol=1e-6`) before test access | Recover the original trained models without bypassing old-run provenance or repeating selection | Post-results software correction only. Tolerances check numerical reproduction, not predictive superiority. Stop on mismatch; never tune tolerances using test scores. See docs/P5_RECOVERY.md |
| 2026-10-12 | P3 section 19; replay CSV deserialization | Explicit round-trip float parsing for validation replay only | Default CSV parsing changed two stored decimal targets by up to 1.42108547e-14 and stopped recovery before corrected test scoring | Exact target equality and prediction tolerances unchanged; no new fitting, selection or ordinary metric-reader changes. New correction run ID ends in -02. |
| 2026-10-12 | P3 sections 11, 13–19; P6 execution details | Execute full matrix for primary and inference-only no-forward-fill sensitivity with unchanged models/statistics; one deterministic whole-loss realization; lossless persistent predictions; matched seed/station aggregation and calendar bootstrap, with explicit unavailable sparse affected-window intervals | Make unspecified implementation and durability details explicit before P6 scores | Clean P5 test outcomes already inspected; no real P6 stress outcomes inspected. Frozen levels, seeds, time split, targets, model selection and main uncertainty settings unchanged. See P6_IMPLEMENTATION_DECISIONS.md |
| 2026-10-13 | P3 section 19; saved-result verification and notebook interface | Add an independent timestamp-frequency-weight implementation to verify saved metrics/intervals and a reconnectable four-cell review notebook with embedded settings | Verify final Drive files after a possible duplicate writer; remove manual SHA/stage/process management from the next user step | Post-P6 execution verification only. Original predictions, estimator, seeds, protocol, replay tolerances and result branch are unchanged. Arithmetic comparison uses atol 1e-8 and rtol 1e-10 solely for summation-order agreement. See docs/P6_VERIFICATION.md |
| 2026-10-14 | P3 sections 12, 16, 17, 19; P7 operational detail | Repeat the complete frozen search within every LOSO fold; freeze all selections before test access; define aggregate regret as mean station-specific regret and retain policy-minus-fixed-family differences separately; use one result branch and persistent prediction references | Make the fold-dependent selection estimand and automatic recovery explicit before P7 scores | P5/P6 outcomes already inspected; no P7 outcomes inspected. Frozen stations, splits, families, budgets, seeds, primary preprocessing and bootstrap settings unchanged. See P7_IMPLEMENTATION_DECISIONS.md |

| 2026-10-22 | P8 diagnostics and repository maintenance | Independently verify P7 saved predictions/native lineage/uncertainty before analysis; add concentration bands, seasons and worst-error tables; consolidate dependency declarations and relocate executed notebooks byte-for-byte | User authorized cleanup and P8 after P7 execution | Aggregate P5/P6/P7 outcomes have been inspected. Subgroup choices are post-results descriptive, not confirmatory. No refitting, reselection, prediction replacement or frozen-protocol change. P6 accepted intervals retain original lineage. See P8_IMPLEMENTATION_DECISIONS.md. |
