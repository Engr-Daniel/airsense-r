"""Replay frozen validation predictions and correct P5 test scoring without training."""
import argparse
import logging
from pathlib import Path

from airsense_r.p5_recovery import recover_test


def main() -> None:
    """Run the explicitly versioned post-results correction."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--sync-remote", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    result = recover_test(Path(__file__).resolve().parents[1], args.run_id,
                          args.model_directory.resolve(), args.sync_remote)
    print("Corrected evaluation complete:", result, flush=True)


if __name__ == "__main__":
    main()
