"""Run the P4 data pipeline without fitting forecasting models."""
from pathlib import Path
import argparse
import logging

from airsense_r.p4 import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sync-remote", help="Credential-free Git URL; omit for explicit local-only execution")
    parser.add_argument("--held-out")
    parser.add_argument("--policy", choices=["primary", "sensitivity"], default="primary")
    parser.add_argument("--internal-fold", type=int, choices=[0, 1, 2])
    parser.add_argument("--training-diagnostics", action="store_true")
    parser.add_argument("--structural-test-coverage", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    print(run_pipeline(Path(__file__).resolve().parents[1], args.run_id, remote=args.sync_remote,
                       held_out=args.held_out, policy=args.policy, internal_fold=args.internal_fold,
                       training_diagnostics=args.training_diagnostics,
                       structural_test_coverage=args.structural_test_coverage))


if __name__ == "__main__":
    main()
