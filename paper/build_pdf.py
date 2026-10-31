"""Compile the manuscript and supplement locally with portable Tectonic."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Keep PDFs, logs and package cache outside the tracked manuscript source."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--compiler", type=Path)
    parser.add_argument("--output-directory", type=Path, default=ROOT / ".tmp/paper-build")
    args = parser.parse_args()
    local = ROOT / ".tmp/tectonic" / ("tectonic.exe" if os.name == "nt" else "tectonic")
    compiler = args.compiler or (local if local.is_file() else shutil.which("tectonic"))
    if not compiler:
        raise SystemExit("Install Tectonic or pass --compiler PATH; see paper/overleaf/README.md")
    compiler = Path(compiler).resolve()
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "paper/overleaf"
    env = {**os.environ, "TECTONIC_CACHE_DIR": str(ROOT / ".tmp/tectonic-cache")}
    version = subprocess.check_output([str(compiler), "--version"], text=True).strip()
    receipt = {"compiler": version, "inputs": {}, "outputs": {}, "layout_warnings": {}}
    for path in sorted(source.rglob("*")):
        if path.suffix in {".tex", ".bib", ".pdf", ".png"}:
            receipt["inputs"][path.relative_to(ROOT).as_posix()] = sha256(path.read_bytes()).hexdigest()
    for name in ["main", "supplement"]:
        subprocess.run([str(compiler), "--keep-logs", "--keep-intermediates",
                        "--outdir", str(output), f"{name}.tex"], cwd=source, env=env, check=True)
        receipt["outputs"][f"{name}.pdf"] = sha256((output / f"{name}.pdf").read_bytes()).hexdigest()
        log = (output / f"{name}.log").read_text(encoding="utf-8", errors="replace")
        receipt["layout_warnings"][name] = [line for line in log.splitlines()
            if "Overfull" in line or "Underfull" in line or "Warning:" in line]
        if "There were undefined references" in log:
            raise RuntimeError(f"Unresolved references in {name}; inspect {output / (name + '.log')}")
    (output / "build_receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(f"Compiled manuscript and supplement: {output}")


if __name__ == "__main__":
    main()
