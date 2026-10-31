"""Export accepted, checksum-verified evidence to docs/data/ for the reliability explorer."""
from __future__ import annotations

import argparse
from pathlib import Path

from airsense_r.explorer import write_explorer_data

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Verify accepted result commits from local Git objects and write explorer JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "docs/data")
    args = parser.parse_args()
    write_explorer_data(ROOT, args.out.resolve())


if __name__ == "__main__":
    main()
