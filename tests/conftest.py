"""Make repository script helpers importable with either pytest entry point."""
from pathlib import Path
import sys


# scripts/ is intentionally not part of the installed src-layout package.
# Unlike python -m pytest, the pytest console script does not add this root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import json
import pytest


@pytest.fixture
def current_source_notebook():
    """Test historical cells against current code without rewriting published files."""
    from airsense_r.artifacts import source_hash
    root = Path(__file__).resolve().parents[1]
    historical = json.loads((root / "results/p8/final_acceptance.json").read_bytes())["source_hash"]
    def adapt(notebook):
        changed = 0
        for cell in notebook["cells"]:
            source = cell["source"]
            text = source if isinstance(source, str) else "".join(source)
            changed += text.count(historical)
            cell["source"] = text.replace(historical, source_hash(root))
        assert changed == 1, "Historical notebook fingerprint differs from accepted P8 source"
        return notebook
    return adapt
