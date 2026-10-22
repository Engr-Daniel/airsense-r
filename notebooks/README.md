# Research notebooks

**Status (22 October 2026): completed and reviewed. No rerun is required.**
Next: P9 manuscript. See [the completion report](../research/P8_COMPLETION_REPORT.md).
The execution instructions below are retained for reproducibility.

**Completed workflow: [07 — statistical and failure analysis](07_p8_statistical_failure_analysis.ipynb).**
Open it in Colab, choose a CPU runtime and Run all with the original Drive account
and GitHub secret. No SHA or stage entry is needed. It verifies P7 before analyzing
saved P6/P7 evidence. See [the workflow](../docs/P8_WORKFLOW.md).

| Notebook | Purpose | Current status |
|---|---|---|
| 01–03 | Dataset review, development diagnostics, pipeline validation | Completed |
| 04 / 04b | Clean benchmark / corrected frozen-model scoring | Accepted; no rerun |
| 05 / 05b | Sensor degradation / independent verification | Accepted; no rerun |
| 06 / 06b | Site shift / recovery in replacement Colab runtime | Accepted after independent verification in 07 |
| 07 | Independent P7 verification and P8 failure analysis | Completed and reviewed |

Numbered notebooks are source templates. Historical recovery/review notebooks
embed their original commits and environments; do not repoint them to current
source or use them to start a new analysis. Reusable science belongs in the
package; scripts execute experiments, while notebooks explain and inspect evidence.

Executed notebooks live in [executed/](executed/). Its [index](executed/index.json)
maps each original path to the relocated file and SHA-256 checksum. Their bytes,
including historical failures, are unchanged. Old receipt paths identify where
the notebooks lived at the time of review; use the index to locate them now.
Do not copy debugging edits from executed notebooks into templates.

Earlier P4 executions remain in the [checkpoint archive](../results/p4/colab-archive/README.md)
and [their original commit](https://github.com/Engr-Daniel/airsense-r/tree/c28c02b87dca1c82c480cd24e7ccd6271792369d/notebooks).
Follow [the notebook guide](../docs/NOTEBOOK_GUIDE.md) for contributor conventions.
