"""Explicit P5 entry point; test access requires a saved selection decision."""
import argparse
import logging
from pathlib import Path

from airsense_r.p5 import run_benchmark, export_run


def main() -> None:
    """Run a resumable, provenance-bound stage without notebook-only scientific logic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["smoke", "select", "test"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--sync-remote")
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    root = Path(__file__).resolve().parents[1]
    directory = run_benchmark(root, args.run_id, args.model_directory.resolve(), stage=args.stage,
                              remote=args.sync_remote, local_only=args.local_only)
    export_run(root, directory)
    print("Verified outputs:", directory)


if __name__ == "__main__":
    main()
