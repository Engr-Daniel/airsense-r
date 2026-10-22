# P8: statistical and failure analysis

Open `notebooks/07_p8_statistical_failure_analysis.ipynb` in Colab and **Run all**
on a CPU runtime. The published notebook embeds its matching source revision.
Connect the original Drive account and the `AIRSENSE_GITHUB_TOKEN` Colab secret.
There are no SHA, stage or run-name questions. P5/P6/P7 experiments need no rerun.

1. Setup installs the analysis environment from `pyproject.toml`.
2. Connect the existing `MyDrive/AirSense-R/model-checkpoints` directory.
3. Verify and analyze saved evidence, with progress and incremental Git saves.
4. Inspect completion and save the notebook with outputs for review.

P7 execution is complete, but independent scientific acceptance is pending.
The first part of P8 checks its 720 prediction CSVs and 108 final native models,
recomputes validation choices and test metrics, and independently reproduces the
paired calendar-block confidence intervals. A mismatch stops the workflow.
It reads model bytes for lineage; it never loads models for inference or fitting.

After that gate, P8 checks the accepted P6 arrays and generates concentration-band,
seasonal and worst-error tables, rank/regret summaries and figures. These are
post-results descriptive diagnostics; the concentration bands are not AQI or
health categories. P6 headline intervals retain their existing independent
acceptance lineage. P7 intervals are independently recomputed from saved rows.

## Interruption and recovery

One worker and one result branch, `results/p8-analysis-01`, are used. If the
browser disconnects, rerun cell 3 to reconnect. If Colab replaces the runtime,
open the same published notebook and Run all. Keep the same Drive account and
only one active runtime. Never delete a lock file. Completed diagnostic units
are reused, but original input checksums are checked again on resume. P7
verification is repeated before reusing its analysis, so initial Drive reading
can take time even when some checkpoints already exist.

The output branch contains immutable tables, PNG figures, diagnostic settings,
input commits and manifest checksums, environment metadata and completion records.
Figures are also exported to `figures/p8-runs/p8-analysis-01/`, and a compact JSON
to `docs/data/p8-runs/p8-analysis-01/` in the runtime. Git publication is incremental;
Drive originals and earlier result branches remain unchanged.

## Scientific acceptance

A successful final cell means **execution complete, review pending**. Preserve
the executed notebook separately in `notebooks/executed/`. Review the published
manifest, verification records, tables and figures before marking P7/P8 accepted
or making manuscript claims. Local synthetic tests do not verify the user's
Drive data or establish live Colab success.

Local verification on 22 October 2026 covered 104 tests across passing runs:
102 regression checks, the separate native P7 interruption/recovery and independent
verification check, and the P8 output-assembly check. The single dependency
definition builds successfully as an editable package. All 15,402 Git artifact
checksums across the three pinned input snapshots were also verified locally.
These checks establish implementation readiness, not completion of live P8 analysis.

For local execution against an existing model-storage copy:

```bash
python -m pip install -e ".[notebooks]"
python scripts/run_failure_analysis.py --model-directory /path/to/model-checkpoints --remote https://github.com/Engr-Daniel/airsense-r.git
```
