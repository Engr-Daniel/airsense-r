"""Small runtime helpers for Colab artifact authentication and notebook runs."""
from __future__ import annotations

from pathlib import Path
import os
import sys

from airsense_r.artifacts import atomic_write


def configure_github_secret(root: Path, token: str) -> None:
    """Keep token in runtime environment; Git obtains it through a secret-free helper."""
    if not token or "\n" in token:
        raise ValueError("A GitHub write credential is required")
    os.environ["AIRSENSE_GITHUB_TOKEN"] = token
    helper = root / ".tmp" / "git-askpass.py"
    script = (f"#!{sys.executable}\n"
              "import os, sys\n"
              "prompt = sys.argv[1].lower() if len(sys.argv) > 1 else ''\n"
              "print('x-access-token' if 'username' in prompt else os.environ['AIRSENSE_GITHUB_TOKEN'])\n")
    atomic_write(helper, script.encode())
    helper.chmod(0o700)
    os.environ["GIT_ASKPASS"] = str(helper)
    os.environ["GIT_TERMINAL_PROMPT"] = "0"
