from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(os.environ.get("GATEWAY_REPO", "/content/remote-compute-mcp-gateway"))
    if not repo_root.exists():
        raise SystemExit(
            f"Repository not found at {repo_root}. Clone or mount the project there, "
            "or set GATEWAY_REPO to the correct path."
        )

    os.environ.setdefault("WORKER_KIND", "colab")
    os.chdir(repo_root)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "worker.app:app",
            "--host",
            "0.0.0.0",
            "--port",
            os.environ.get("WORKER_PORT", "8001"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
