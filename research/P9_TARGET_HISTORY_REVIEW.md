# Target-history execution review

Reviewed 2026-10-30. This is the bounded post-results extension declared in
[the checkpoint plan](P9_CHECKPOINT_PLAN.md). Original P5–P8 evidence is unchanged.

Execution is complete at result commit
`a816353692920e56915316b98b6481313e72a461`. All 331 registered Git artifact
checksums pass. The accepted corrected P5 parent commit and manifest match.
The four executed notebook code cells match the published template, have counts
1–4 and contain no error outputs. The executed bytes are preserved under
`notebooks/executed/`; the reusable notebook is restored to its published template.

Independent local aggregation of 25 seed-metric CSVs reproduces all seven
scope summaries and 28 model metric rows, including MAE, RMSE, R², matched-clean
relative degradation, ranks, Kendall tau and selection regret. The review checks
all 12 stations and the expected training/corruption seeds. There are 261 saved
prediction-bundle references. See
[the machine-readable receipt](../results/p9-target-history/execution_review.json).

| Condition | Full-period persistence regret | Outage-affected regret |
| --- | ---: | ---: |
| PM2.5 dropout 10% | 0.000 | — |
| PM2.5 dropout 30% | 0.000 | — |
| PM2.5 dropout 50% | 0.000 | — |
| PM2.5 outage 6 hours | 0.557 | 0.198 |
| PM2.5 outage 12 hours | 0.651 | 2.282 |

Regret is in µg/m³ relative to the lowest-error candidate under the same
condition. The reported 95% interval for 12-hour outage-affected regret is
1.696–2.910, entirely above the prespecified 1 µg/m³ practical threshold.
Full-period averages therefore conceal a meaningful loss during affected windows.
Persistence being best among these candidates during random dropout does not
establish adequate absolute accuracy: its MAE reaches 15.671 at 50% dropout.
These findings do not validate a switching or fallback policy.

## Acceptance boundary

The Colab evaluator compared every interval against an independent
frequency-weight bootstrap implementation. Local review checked recorded
interval settings and recomputed point estimates. It did **not** read the final
Drive prediction arrays or independently recompute interval endpoints from
those saved arrays. Scientific acceptance remains pending that read-only check.
Do not rerun training or inference, change the declared conditions, or present
these findings as accepted manuscript evidence yet.
