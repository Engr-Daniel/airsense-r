# P4 workflow

P4 builds data and recovery infrastructure. It does not train the P5 forecasting models or inspect final-test predictive performance.

## Environment and commands

Use Python 3.11+ in a virtual environment:

```bash
python -m pip install -r requirements-p4.txt -e .
python -m pytest -q
python scripts/run_pipeline.py --run-id p4-development
```

The last command explicitly runs with **local-only durability** and reports that limitation. It verifies the frozen UCI archive in temporary storage, exposes rows only through validation, fits preprocessing on training rows, and writes compact JSON checkpoints under `results/p4/<run-id>/`.

```bash
python scripts/run_pipeline.py --run-id p4-remote --sync-remote https://github.com/Engr-Daniel/airsense-r.git
python scripts/run_pipeline.py --run-id p4-loso-Dingling --held-out Dingling
python scripts/run_pipeline.py --run-id p4-fold0 --internal-fold 0
python scripts/run_pipeline.py --run-id p4-sensitivity --policy sensitivity
python scripts/run_pipeline.py --run-id p4-training-diagnostics --training-diagnostics
python scripts/run_pipeline.py --run-id p4-structural --structural-test-coverage
```

The optional test flag permits structural eligibility counts only. It never computes model scores or test-distribution diagnostics. Each run has different parameters/provenance; use different IDs. Internal fold outputs retain the frozen outer split labels in coverage reports; their fitting cutoff is recorded explicitly in preprocessing metadata.

## Scientific data API

`read_stations` parses and validates station grids. `CausalPreprocessor.fit` restricts fitting to the specified cutoff and excludes the held-out station. Its JSON state contains medians, categories, scaling statistics, and feature order. Each internal fold/LOSO fold must fit its own state. `transform` needs chronological history to carry causal fill across partition boundaries.

`build_windows` stores source features plus compact target/origin indices. `WindowSet.batch` materializes only requested batches; it avoids duplicating the whole dataset into a large three-dimensional tensor. Neural models use scaled numerical features; tabular XGBoost uses unscaled history. The same target keys and original labels are retained. See `research/P4_IMPLEMENTATION_DECISIONS.md` for calendar, persistence and stress conventions.

The runner persists metadata and coverage, not full raw data or trained models. Model input arrays are reproducible from the verified source and fitted state. Later P5 runners should checkpoint prediction shards and, when needed, model training state to an appropriate persistent destination.

## Incremental Git checkpoint behavior

Supply a credential-free Git URL and configure a credential helper. Colab notebooks use the `AIRSENSE_GITHUB_TOKEN` secret through a runtime askpass helper; never paste a token into a notebook or remote URL.

Every saved unit is atomically written and hashed, followed by a manifest update and synchronous commit/push. A separate checkout under `.tmp/checkpoint-checkouts/<run-id>` publishes only approved artifacts to `results/<run-id>`. A real initial marker push checks write capability before expensive acquisition. Artifact branches do not trigger the main-branch audit or test workflow.

Run IDs have a single writer. Concurrent writers produce a non-fast-forward failure rather than overwriting remote work. Push failures stop execution with local results retained. Rerunning the same ID and exact provenance retries pending pushes; after runtime loss, cloning the result branch restores remotely confirmed units. A different config, protocol, environment, code identity or run parameters requires a new ID. Never force-push to resolve divergence.

The per-file Git checkpoint limit is 10 MiB. Do not bypass it with raw data or model binaries. Large model recovery artifacts need separate persistent storage before long training begins. Remote durability does not cover a currently executing cell/model fit or a failed upload.

## Colab notebooks

Open notebooks 01–03 from the P4 source commit on GitHub. Each prompts for the full **same P4 commit SHA** and a run ID, clones that revision, installs the CPU environment, and checks provenance. Use the commit containing the notebook you opened; the SHA identifies the software, not a push command or run name. The notebooks do not silently follow moving `main` during an experiment.

01 reviews saved P2 evidence. 02 runs training-only diagnostics and checkpoints each station. 03 validates the pipeline on an explicitly labelled synthetic fixture. Outputs are separate JSON/CSV checkpoints rather than relying on a final save of the notebook document.

Local/CI notebook tests execute their actual code cells in fresh Python processes using an explicit test-mode bootstrap and temporary bare Git remotes. These tests exercise analysis, per-checkpoint pushes and resume, but do not establish that a user's Colab secret or runtime is configured. User-run live Colab publication and notebook 03 fresh-runtime recovery were reviewed on 2026-10-09; see `results/p4/colab_acceptance.json`. That evidence used the original revision plus the user's notebook import workaround, not the subsequently standardized bootstrap.

## Code revision versus run name

Use the same code commit for notebooks 01?03, but distinct run names such as
`nb01-audit-01`, `nb02-diagnostics-01`, and `nb03-validation-01`.
Each run gets a `results/<run-id>` branch containing compact artifacts and a manifest,
not an automatically saved executed notebook. These branches need not be merged into
`main` for recovery. Existing run names remain valid, including the SHA-shaped name
used for the first audit review.

The bootstrap activates exactly the selected checkout's `src` directory in the
current kernel after installation, verifies the package origin, and refuses cached
imports from another checkout. No recursive path search is needed.

To restore an old run, use its original notebook/code revision and compatible
environment. The bootstrap update changes source identity, so use a new run name
with the updated notebooks. Do not rewrite historical manifests to match new code.
Notebook 03 recomputes its small synthetic check and validates the compatible saved
artifact on resume; it does not skip the calculation.
