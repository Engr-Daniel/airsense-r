# Research notebooks

The naming sequence and required conventions are defined in [the notebook guide](../docs/NOTEBOOK_GUIDE.md).

Build notebooks 01–03 during P4, and notebooks 04–07 alongside P5–P8. The P2 notebook reviews saved evidence; it does not perform the authoritative audit. Reusable implementation belongs in the package and reproducible execution in scripts.

Notebooks 01–03 and shared checkpoint synchronization/resume support are implemented. They push checkpoints when a remote and credentials are configured; local/CI tests use temporary bare Git remotes. Live Colab acceptance still requires publishing the P4 source commit and configuring Colab Secrets. See `docs/P4_WORKFLOW.md`.

Google Colab is the intended execution environment. Every notebook starts with a bootstrap section that clones the repository in a fresh runtime, verifies a recorded code revision, installs dependencies and the package, and initializes or restores run checkpoints. Rerunning setup must preserve existing work. Follow the guide's Colab bootstrap requirements.
