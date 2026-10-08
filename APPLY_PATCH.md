# AirSense-R P2 closure patch

This patch is intended for the **current live repository state after the successful authoritative P2 audit**.

Apply it at the repository root, preserving the existing `audit/` directory and its five committed evidence files.

Files replaced:
- `scripts/download_data.py`
- `research/P2_COMPLETION_REPORT.md`
- `research/DATASET.md`
- `README.md`
- `TASK.md`
- `MEMORY.md`

After applying, run:

```bash
python -m compileall scripts src
pytest -q
```

Then commit/push the closure changes. P2 can be treated as closed; P3 may begin.
