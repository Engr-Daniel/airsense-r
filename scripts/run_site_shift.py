"""Run/resume P7 without manual stage switches."""
import argparse
import logging
from pathlib import Path

from airsense_r.p7 import run_site_shift


def main() -> None:
    """Execute the pinned automatic workflow with persistent model storage."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--remote", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    run_site_shift(Path(__file__).resolve().parents[1], args.model_directory.resolve(), args.remote)


if __name__ == "__main__":
    main()
