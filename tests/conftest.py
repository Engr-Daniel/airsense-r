"""Make repository script helpers importable with either pytest entry point."""
from pathlib import Path
import sys


# scripts/ is intentionally not part of the installed src-layout package.
# Unlike python -m pytest, the pytest console script does not add this root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
