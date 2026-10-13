# P6 execution review — 2026-10-13

**Execution complete; final scientific acceptance pending.**

**Update 2026-10-13:** the subsequent independent review passed and P6 is now
accepted. See [P6_COMPLETION_REPORT.md](P6_COMPLETION_REPORT.md) and
`results/p6/final_acceptance.json`. The pending status below records the earlier
review boundary and is retained as incident history.

Run `p6-sensors-01` published its completion record at result commit
`464574140e7abb79094935313d6f3eb44fce3a93`. The generating code remains
`3c9b5d49fb90b30cc967f8d31f9f3c3007b81a0d`. The final notebook inspection
displays completion for all 15 conditions under both policies and the result
table and plot. The accepted P5 parent identity remains unchanged.

## Interruption incident

After a connection interruption, the user removed the writer-lock file and
launched another invocation. That invocation eventually failed with
`Git add failed (exit 128)`. Another evaluation process remained present and
the remote branch continued receiving checkpoints. The notebook later records
that the process stopped, artifact verification succeeded, and the completion
record was present. Concurrent writers are a plausible explanation for the Git
failure, but its underlying stderr was not retained in the displayed error.

Preserve this history. The complete submitted notebook, including its failed
invocation and subsequent successful inspection, is archived byte-for-byte as
`notebooks/05_p6_sensor_degradation_evaluation_executed.ipynb` (SHA-256
`805655f55708d7db74fe24295a2d7888444a3ef87cb4bf2c89d33f75f29867bd`).
The source template has been restored without the lock-deletion edit.

## Acceptance boundary

All 1,520 registered Git artifacts passed checksum verification. The 30
condition/policy reports contain 42 full-period/affected-window reports and
1,280 prediction-file references. Independent aggregation of saved station,
training-seed and corruption-seed metrics reproduced reported MAE/RMSE/R2,
matched clean metrics, RPD and selection regret for all 42 reports. All reported
intervals are available; their point-regret estimates agree with the metric
aggregation. This checks internal consistency, not independent interval bounds.

The machine-readable review is `results/p6/evaluation_review.json`. Verification
of Git artifacts and aggregation of saved station/seed metrics cannot establish
that every final Drive prediction file still matches its published reference
after overlapping writers. Verify those files against the final manifest and
independently recompute headline metrics and paired uncertainty from the arrays
before declaring P6 scientifically accepted or beginning P7. The existing saved
predictions should be used for that review; no experiment rerun is requested.

## Workflow follow-up

The user should not need repeated SHA/stage decisions or manual process checks.
The next interface revision should embed compatible code identity, detect and
resume existing runs, display durable progress and explicit completion/failure,
and prevent duplicate launches without deleting locks. Test reconnection and
interruption behavior before handing over that interface. Keep this completed
run and its generating identity unchanged.

The follow-up is implemented as a separate saved-result verification notebook
`05b_p6_saved_result_verification.ipynb`, with an independent verifier and
reconnectable worker. See `docs/P6_VERIFICATION.md`. It keeps the completed
experiment read-only and publishes review evidence separately. Live execution
of that verifier remains pending; implementation tests are not acceptance of
the user's Drive arrays.

Local verification of the follow-up: 83 regression tests passed (the unchanged,
long P6 experiment lifecycle fixture was excluded from this invocation). The
final eight verifier/job tests also passed after expanding the serialized review
fixture to all four model families. These cover independent bootstrap agreement,
partial final blocks, masked targets, exact outage boundaries, altered intervals,
Drive-file corruption, provenance rejection, interruption/resume, stale unlocked
files, duplicate workers, failure recovery, and fresh-process execution of all
four notebook cells. Seven current notebook templates passed format/fingerprint
checks; archived executions and frozen protocol/configuration are unchanged.

A synthetic calculation at the full array dimensions (five realizations, four
models, 12 stations, 8,760 hours and 2,000 replicates) completed in 2.56 seconds
locally. This checks that the independent method is computationally practical;
it is not a forecast result or a promise about Colab/Drive wall time. Real file
verification and independent interval agreement remain pending the user run.
