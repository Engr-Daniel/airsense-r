"""Run frozen-model P6 preflight or sensor-degradation evaluation."""
import argparse
import logging
from pathlib import Path

from airsense_r.p6 import run_p6


def main() -> None:
    """Require explicit stage, persistent model storage and remote checkpoints."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=["preflight", "evaluate"])
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--sync-remote", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    output = run_p6(Path(__file__).resolve().parents[1], args.run_id,
                    args.model_directory.resolve(), args.sync_remote, args.stage)
    print("P6 stage complete:", args.stage, output, flush=True)


if __name__ == "__main__":
    main()
