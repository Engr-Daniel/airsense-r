# Notebook conventions

Scripts reproduce the experiment. The package implements the experiment. Notebooks explain, validate, and interpret the evidence.

## Ownership and organization

Reusable scientific logic belongs in `src/airsense_r/`, experiment entry points in `scripts/`, and research notebooks in `notebooks/`. The planned sequence is:

1. `01_p2_dataset_audit_review.ipynb`
2. `02_p3_development_diagnostics.ipynb`
3. `03_p4_pipeline_validation.ipynb`
4. `04_p5_clean_benchmark_analysis.ipynb`
5. `05_p6_sensor_degradation_analysis.ipynb`
6. `06_p7_site_shift_analysis.ipynb`
7. `07_p8_statistical_failure_analysis.ipynb`

Build the first three during P4 and the others alongside their respective phases. The P2 notebook inspects saved audit evidence; authoritative acquisition and auditing remain script/CI responsibilities.

## Google Colab bootstrap

Google Colab is the intended notebook execution environment. Every notebook must be independently runnable in a fresh runtime, without relying on a previous notebook's filesystem or variables.

After the introductory Markdown and partition declaration, include a clearly labelled bootstrap section before any project imports or analysis:

1. Declare the repository URL (`https://github.com/Engr-Daniel/airsense-r`) and an explicit code revision. Use a pinned commit or release for reproducible research runs and record the resolved commit SHA. Record the notebook source revision too, and verify compatibility with the checked-out package.
2. Clone the repository into the runtime workspace if absent, then check out the requested revision. On rerun, verify the existing checkout's remote, revision, and working-tree state; reuse a matching checkout. Do not delete, reset, or overwrite an existing checkout with uncommitted changes. Fail clearly on mismatch.
3. Install the declared compatible dependencies and the package into the notebook kernel's environment before importing project modules. Verify Python 3.11+ and record actual environment versions. If installation requires a kernel restart, explain it explicitly and make rerunning bootstrap safe.
4. Resolve repository-relative paths and load the frozen configuration. Run provenance and permitted-partition checks before data or result access.
5. Configure GitHub synchronization using runtime secrets, verify write capability, and create the isolated artifact checkout. A public clone needs no write credential; pushing results does. Never embed credentials in clone URLs or outputs.
6. For a resumed run, accept an explicit run ID, restore confirmed remote checkpoints, and validate their provenance against the selected code/configuration before continuing. For a new run, initialize a new manifest.

Keep this initial bootstrap minimal and consistent across notebooks; after cloning, invoke shared setup/checkpoint utilities rather than duplicating scientific logic. Dependency installation is permitted in this dedicated setup section, never mixed into analysis cells. Opening a notebook in Colab does not replace cloning its supporting repository.

Treat runtime files as disposable. Cloning restores committed source and artifacts on the checked-out revision; results on `results/<run-id>` must be restored separately. Colab's saved notebook document is not a backup of arbitrary runtime result files. Raw-data acquisition remains temporary and checksum-verified.

## Notebook narrative

Start with purpose, research question, protocol identity, prerequisites, expected runtime, inputs, outputs, and an explicit permitted-partitions declaration:

- `TRAIN ONLY`
- `TRAIN + VALIDATION`
- `FINAL TEST — READ ONLY`
- `STRUCTURAL AUDIT ARTIFACTS ONLY` for the P2 review.

State exact time boundaries and station exclusions and enforce them through shared loaders. Final-test read-only analysis may save reports, but cannot tune methods or alter model selection.

Continue with setup, provenance checks, input validation, focused analysis, findings, limitations, and artifact references. Alternate explanatory Markdown with focused code cells. Distinguish observations, interpretation, and exploratory findings.

- Use descriptive names, explicit imports, `pathlib`, and the installed package. Avoid user-specific paths and `sys.path` edits.
- Keep each cell focused on one coherent operation; separate expensive execution from presentation.
- Put reusable functions in tested package modules with type hints and docstrings.
- Require fresh-kernel, top-to-bottom execution without hidden state or manual execution-order dependencies.
- Make repeated execution safe, and fail clearly on invalid inputs.
- Document environment setup in the repository and mirror the necessary steps in the dedicated Colab bootstrap; do not install dependencies in analysis cells.
- Label figures with units, legends, sample counts, and appropriate uncertainty. Save publication figures through shared plotting functions.
- Keep compact useful outputs; remove huge arrays, full datasets, verbose logs, abandoned cells, and stale claims.

## Frozen configuration and provenance

Load `configs/experiment.yaml` as the source of truth. Never silently override frozen values. Explicit exploratory overrides are allowed only in clearly marked development notebooks with separate artifacts and saved effective configuration. They must not feed final evaluation unless the methodological change is recorded in `research/PROTOCOL_DEVIATIONS.md`.

Before loading results, validate the artifact manifest against the intended run:

- effective configuration snapshot and deterministic hash;
- protocol status and version/content hash;
- frozen dataset checksum;
- generating code commit SHA where available, plus modified-source identity when applicable;
- schema, feature ordering, permitted partitions/stations, seeds, and artifact checksums.

Refuse incompatible or unverified combinations. Legacy P2 evidence uses its acquisition receipt and documented schema; never invent absent historical metadata. Record Python/dependency versions at run start. Artifact-publication commits do not replace the generating code identity.

## Incremental persistence and automatic GitHub synchronization

Completed outputs must be saved and pushed during execution, not deferred to the final notebook cell. Implement this in shared checkpoint utilities used by scripts and notebooks.

1. Create a unique run ID and immutable configuration/protocol/data provenance before computation.
2. Save each completed unit immediately: a station, fold, model/seed result, prediction shard, table, or figure. Write a temporary file and atomically rename on the same filesystem before updating the manifest. Never mark partial output complete.
3. Automatically queue each completed checkpoint for commit and push. Use one serialized writer per run with bounded retry/backoff. Small adjacent outputs may be batched with a documented maximum delay; flush at normal shutdown.
4. Use a dedicated `results/<run-id>` branch and isolated checkout/worktree. Stage only an explicit allowlist of that run's artifacts. Never use `git add .`, force-push, or commit unrelated edits. Artifact pushes must not trigger repeated authoritative dataset audits.
5. Display pending, failed, and remotely confirmed checkpoint status. Confirm the remote commit before reporting successful synchronization. Failed pushes retain local files and are retried; they must not silently appear successful.
6. Resume by validating provenance and checksums, restoring remotely confirmed outputs when necessary, and recomputing incomplete units. Never combine incompatible runs.

Check authentication and write capability before expensive execution. Keep credentials in runtime secrets/credential storage, never in notebooks, outputs, Git URLs, or configuration committed to Git. If remote synchronization is unavailable, explicitly report local-only durability instead of silently downgrading the requested behavior.

Use `results/`, `figures/`, and `docs/data/` for their established artifact purposes. Ordinary Git should contain compact approved outputs. Exclude raw datasets, caches, credentials, and large model binaries. Large required recovery artifacts need an explicitly configured persistent artifact destination with checksum references; never quietly omit them.

Saved metrics and predictions are the recovery source of truth. Incrementally saved executed notebook snapshots are supplementary: use the execution runner's supported save mechanism at cell boundaries, rather than assuming the kernel can save its frontend document. Keep partial snapshots labelled and separate from the reviewed source notebook. Resuming inside long model fits additionally requires framework training checkpoints.

No workflow guarantees zero loss of in-flight computation. During network outages, locally saved outputs can still be lost if an ephemeral runtime disappears before upload. Only remotely confirmed checkpoints survive loss of that runtime.

## Testing and maintenance

Package tests verify scientific behavior; notebook execution checks verify the documented workflow. Use small synthetic fixtures for routine checks and execute full notebooks at phase checkpoints. Test interrupted writes, resume, failed pushes, provenance mismatch, and artifact-only staging.

Before committing a reviewed notebook, restart and run all cells, inspect its diff, remove secrets and excessive output, and verify that conclusions match the saved evidence. Passing execution alone does not establish scientific correctness.

## Implementation status

Shared provenance loaders, checkpoint persistence, Git synchronization, resume support, and notebooks 01–03 are implemented in P4. Local integration tests cover these behaviors using bare Git remotes and explicit notebook fixture setup. Actual GitHub pushing requires runtime credentials; fresh Colab clone/install/authentication acceptance remains a separate check before long experiments. See `P4_WORKFLOW.md` and `../research/P4_COMPLETION_REPORT.md`.
