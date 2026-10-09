# Protocol Deviations

Record every change made after `PROTOCOL.md` is marked **FROZEN**.

| Date | Protocol item | Change | Reason | Expected impact |
|---|---|---|---|---|
| 2026-10-08 | P3 sections 6–13, input representation and preprocessing | Clarified training-statistic scope, numeric scaling, input layout, leap-year encoding, persistence fallback, eligibility, and stress-boundary history in `P4_IMPLEMENTATION_DECISIONS.md` | Make unspecified implementation choices explicit before model execution | No final-test performance inspected; choices affect model inputs and are recorded before evaluation |
