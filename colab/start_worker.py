from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PID_FILE = Path("/tmp/remote-compute-mcp-worker.pid")
LOG_FILE = Path("/tmp/remote-compute-mcp-worker.log")


def main() -> None:
    repo_root = Path(os.environ.get("GATEWAY_REPO", "/content/remote-compute-mcp-gateway"))
    if not repo_root.exists():
        raise SystemExit(
            f"Repository not found at {repo_root}. Clone or mount the project there, "
            "or set GATEWAY_REPO to the correct path."
        )

    os.environ.setdefault("WORKER_KIND", "colab")
    os.chdir(repo_root)

    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            print(f"Worker already running with PID {pid}")
            print(f"Log: {LOG_FILE}")
            return
        except (ValueError, ProcessLookupError, PermissionError):
            PID_FILE.unlink(missing_ok=True)

    log_handle = LOG_FILE.open("a", encoding="utf-8")
    process = subprocess.Popen(
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
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    print(f"Worker started in background with PID {process.pid}")
    print(f"Listening on http://127.0.0.1:{os.environ.get('WORKER_PORT', '8001')}")
    print(f"Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
