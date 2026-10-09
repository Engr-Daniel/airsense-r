# Research notebooks

The naming sequence and required conventions are defined in [the notebook guide](../docs/NOTEBOOK_GUIDE.md).

Build notebooks 01–03 during P4, and notebooks 04–07 alongside P5–P8. The P2 notebook reviews saved evidence; it does not perform the authoritative audit. Reusable implementation belongs in the package and reproducible execution in scripts.

Notebooks 01–03 and shared checkpoint synchronization/resume support are implemented. They push checkpoints when a remote and credentials are configured; local/CI tests use temporary bare Git remotes. User-run live Colab publication and notebook 03 fresh-runtime recovery were reviewed on 2026-10-09. The import workaround is now standardized in bootstrap and tested locally. See `docs/P4_WORKFLOW.md`.

Google Colab is the intended execution environment. Every notebook starts with a bootstrap section that clones the repository in a fresh runtime, verifies a recorded code revision, installs dependencies and the package, and initializes or restores run checkpoints. Rerunning setup must preserve existing work. Follow the guide's Colab bootstrap requirements.


## Canonical title and historical execution evidence

The canonical study title comes from CITATION.cff. Current notebook title pages
are generated from it. The title-generator update changes the recorded source
fingerprint; use the same commit as the opened notebook and a new run ID.
Successful executed notebooks remain preserved at
[commit c28c02b](https://github.com/Engr-Daniel/airsense-r/tree/c28c02b87dca1c82c480cd24e7ccd6271792369d/notebooks)
and checkpoint artifacts remain in results/p4/colab-archive/.
Current source notebooks are regenerated without historical outputs to avoid
attributing old executions to updated source. No additional user rerun is needed.
