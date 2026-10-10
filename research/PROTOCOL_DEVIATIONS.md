# Protocol Deviations

Record every change made after `PROTOCOL.md` is marked **FROZEN**.

| Date | Protocol item | Change | Reason | Expected impact |
|---|---|---|---|---|
| 2026-10-08 | P3 sections 6–13, input representation and preprocessing | Clarified training-statistic scope, numeric scaling, input layout, leap-year encoding, persistence fallback, eligibility, and stress-boundary history in `P4_IMPLEMENTATION_DECISIONS.md` | Make unspecified implementation choices explicit before model execution | No final-test performance inspected; choices affect model inputs and are recorded before evaluation |

| 2026-10-10 | P3 sections 9, 14, 17, 19 | Declared bounded training search, fixed budgets without early stopping, seed/fold aggregation, CPU execution, persistent model recovery, and timestamp-aware paired bootstrap in P5_IMPLEMENTATION_DECISIONS.md and configs/p5_training.yaml | Resolve implementation details before any model scores | No final-test outcomes inspected; four families, splits, stress levels and frozen uncertainty parameters unchanged |
