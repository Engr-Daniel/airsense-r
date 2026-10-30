"""Review the completed P9 target-history snapshot using saved Drive arrays, without inference."""
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

RESULT_COMMIT = "a816353692920e56915316b98b6481313e72a461"
SOURCE_COMMIT = "0cd6c470471625409affb97dffbc4b3473663602"
RUN_ID = "p9-target-history-01"
REVIEW_ID = "p9-target-history-review-01"


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
            raise RuntimeError("Unable to read pinned P9 evidence; original evidence preserved")
        return result.stdout.strip()
    with local_writer_lock(root / ".tmp" / "p9-review-writer.lock"):
        checkout = root / ".tmp" / "p9-review-parent" / RESULT_COMMIT
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
        if sha256(evidence.raw_manifest).hexdigest() != "751cec98c86b0c9fda2c5569c5a86aa918f81f8e8b4050eccf2cffd1e89401b1":
            raise ValueError("Unexpected completed experiment manifest")
        storage = json.loads((args.model_directory / "storage.json").read_bytes())
        if storage["storage_id"] != evidence.manifest["provenance"]["parameters"]["model_storage_id"]:
            raise ValueError("Wrong Drive storage")
        provenance = {"phase": "P9_target_history_independent_review", "result_commit": RESULT_COMMIT,
            "result_manifest_sha256": sha256(evidence.raw_manifest).hexdigest(),
            "verifier_source_hash": source_hash(root),
            "verifier_commit": git("-C", str(root), "rev-parse", "HEAD"),
            "environment": {"python": platform.python_version(),
                "packages": {name: version(name) for name in ("numpy", "pandas", "threadpoolctl")}},
            "original_provenance": evidence.manifest["provenance"],
            "method": "timestamp_frequency_weight_bootstrap", "atol": 1e-8, "rtol": 1e-10}
        output = open_run(root, REVIEW_ID, provenance, args.remote)
        verify_saved_run(evidence, args.model_directory / "p9-target-history" / RUN_ID, output,
                         lambda message: print(message, flush=True), target_history=True)


if __name__ == "__main__":
    main()
