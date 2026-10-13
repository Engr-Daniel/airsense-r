"""Review the completed P6 snapshot using saved Drive arrays, without inference."""
from hashlib import sha256
import argparse
import logging
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess

from airsense_r.artifacts import source_hash
from airsense_r.checkpoints import open_run
from airsense_r.evaluation.p6_verify import Snapshot, verify_saved_run
from airsense_r.p5_recovery import local_writer_lock

RESULT_COMMIT = "464574140e7abb79094935313d6f3eb44fce3a93"
SOURCE_COMMIT = "3c9b5d49fb90b30cc967f8d31f9f3c3007b81a0d"
RUN_ID = "p6-sensors-01"
REVIEW_ID = "p6-sensors-01-review-01"


def main() -> None:
    """Bind review checkpoints to exact evidence and verifier implementation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-directory", type=Path, required=True)
    parser.add_argument("--remote", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    logging.basicConfig(level=logging.INFO)
    def git(*parts: str) -> str:
        result = subprocess.run(["git", *parts], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError("Unable to read pinned P6 evidence; original evidence preserved")
        return result.stdout.strip()
    with local_writer_lock(root / ".tmp" / "p6-review-writer.lock"):
        checkout = root / ".tmp" / "p6-review-parent" / RESULT_COMMIT
        if not checkout.exists():
            checkout.parent.mkdir(parents=True, exist_ok=True)
            git("clone", "--no-checkout", "--single-branch", "--branch", f"results/{RUN_ID}",
                "--config", "core.autocrlf=false", args.remote, str(checkout))
            git("-C", str(checkout), "checkout", "--detach", RESULT_COMMIT)
        if (git("-C", str(checkout), "rev-parse", "HEAD") != RESULT_COMMIT
                or git("-C", str(checkout), "remote", "get-url", "origin") != args.remote
                or git("-C", str(checkout), "status", "--porcelain")):
            raise ValueError("Pinned review checkout changed; do not reset existing evidence")
        evidence = Snapshot(checkout / "results" / RUN_ID)
        if evidence.manifest["provenance"]["code_commit"] != SOURCE_COMMIT:
            raise ValueError("Unexpected experiment source")
        preflight = json.loads(git("-C", str(checkout), "show",
            f"9f7b6b199b50f3c514baa8e7e56a566e56665daf:results/{RUN_ID}/manifest.json"))
        if preflight["provenance"] != evidence.manifest["provenance"]:
            raise ValueError("Final run differs from accepted preflight provenance")
        for name, record in preflight["artifacts"].items():
            if evidence.manifest["artifacts"].get(name) != record:
                raise ValueError(f"Accepted preflight artifact changed: {name}")
        provenance = {"phase": "P6_independent_review", "result_commit": RESULT_COMMIT,
            "result_manifest_sha256": sha256(evidence.raw_manifest).hexdigest(),
            "verifier_source_hash": source_hash(root),
            "verifier_commit": git("-C", str(root), "rev-parse", "HEAD"),
            "environment": {"python": platform.python_version(),
                "packages": {name: version(name) for name in ("numpy", "pandas", "threadpoolctl")}},
            "original_provenance": evidence.manifest["provenance"],
            "method": "timestamp_frequency_weight_bootstrap", "atol": 1e-8, "rtol": 1e-10}
        output = open_run(root, REVIEW_ID, provenance, args.remote)
        verify_saved_run(evidence, args.model_directory / "p6-artifacts" / RUN_ID, output,
                         lambda message: print(message, flush=True))


if __name__ == "__main__":
    main()
