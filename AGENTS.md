# AGENTS.md — Contributor / Coding-Agent Instructions

## Mission

Build AirSense-R as a reproducible scientific software project, not as a notebook-only demo. Every code change should support the frozen research protocol, reproducibility, or the public reliability explorer.

## Non-negotiable rules

1. Read `MEMORY.md`, `TASK.md`, and `research/PROTOCOL.md` before modifying experiment logic.
2. Do not alter the final evaluation protocol after seeing results without documenting the change in `research/PROTOCOL_DEVIATIONS.md`.
3. Keep raw data immutable. Derived artifacts belong in `data/processed/` or `results/`.
4. Avoid data leakage. All scalers/imputers/model preprocessing must be fit on training data only.
5. Use deterministic random seeds wherever supported.
6. Save experiment metadata (config, seed, commit when available, metrics) with outputs.
7. Do not claim Edge-ML or embedded deployment unless actual deployment is implemented and tested.
8. Keep dependencies modest; the project must remain runnable on a normal CPU when possible.
9. Prefer reusable modules under `src/airsense_r/` over duplicated notebook code.
10. Tests must cover critical data split, corruption, and metric logic.

## Coding style

Google Colab is the intended notebook runtime. Each notebook must bootstrap its own repository checkout and environment, verify the code revision, and initialize or restore run checkpoints before analysis. Setup must be safe to rerun without discarding existing work.

Follow `docs/NOTEBOOK_GUIDE.md` for notebooks under `notebooks/`, explicit permitted partitions, provenance checks, and frozen-configuration handling. Implement shared incremental artifact saving, automatic GitHub synchronization, and tested resume support before long experiments; never defer all saves to the final notebook cell.

- Python 3.11+
- Use type hints for reusable functions.
- Keep functions small and purpose-specific.
- Use `pathlib` for filesystem paths.
- Use docstrings for public functions/classes.
- Never hard-code user-specific absolute paths.
- Log key experiment steps and seeds.

## Verification before handing a notebook to the user

- Treat preprocessing serialization, CSV parsing and native model reload as part
  of the scientific pipeline. Test the actual on-disk formats, not just in-memory
  objects. Assert feature names/order, labels and predictions survive round trips.
- Include noninteger targets, missing values, categorical inputs and all supported
  model families in relevant integration fixtures. Include the known 74.3/81.8 CSV
  precision cases. Keep replay tolerances explicit; never loosen them to pass a run.
- For recovery or inference-path changes, replay frozen development predictions
  with reloaded models before exposing test rows. Confirm no fitting or selection
  occurs during recovery. Record any post-results correction and preserve originals.
- Verify fresh-process execution, interruption/resume and duplicate-writer behavior
  for affected workflows. Distinguish locally tested behavior from live Colab checks.
- Review the final diff, run relevant regression/integration checks, regenerate
  source fingerprints, and give a notebook link pinned to its matching full commit.
  Preserve executed notebooks separately before regenerating templates.
- Before declaring a phase complete, inspect its actual completion records, verify
  artifact checksums and lineage, and independently recompute headline metrics and
  uncertainty. A successful cell or passing unit tests alone is insufficient.

## Experiment outputs

Every experiment should save structured outputs that can be reused by the manuscript and dashboard:

- metrics CSV/JSON
- prediction CSV/Parquet where practical
- config snapshot
- plots to `figures/`
- dashboard-ready export to `docs/data/`

## Scope discipline

V1 is forecasting reliability under sensor degradation and site shift. Do not add anomaly detection, source apportionment, AQI classification, transformer architectures, or Edge deployment unless all core tasks are complete and `TASK.md` is updated.

## Definition of done for v1

- Dataset acquisition/audit reproducible
- Protocol frozen
- Clean benchmark complete
- Sensor dropout experiment complete
- Noise experiment complete
- Site-shift experiment complete
- Statistical/failure analysis complete
- Manuscript draft complete
- GitHub Pages explorer functional
- README reproduces core workflow
- Tests pass
- Release artifacts versioned
