from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


CLOUDFLARED_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/"
    "cloudflared-linux-amd64"
)
BIN_PATH = Path("/tmp/cloudflared")
LOG_PATH = Path("/tmp/remote-compute-mcp-tunnel.log")
PID_PATH = Path("/tmp/remote-compute-mcp-tunnel.pid")


def _download_cloudflared() -> None:
    if BIN_PATH.exists():
        return
    print("Downloading cloudflared...")
    urllib.request.urlretrieve(CLOUDFLARED_URL, BIN_PATH)
    BIN_PATH.chmod(0o755)


def _existing_process() -> int | None:
    if not PID_PATH.exists():
        return None
    try:
        pid = int(PID_PATH.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        PID_PATH.unlink(missing_ok=True)
        return None


def _wait_for_url(timeout: float = 20.0) -> str:
    pattern = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if LOG_PATH.exists():
            text = LOG_PATH.read_text(encoding="utf-8", errors="replace")
            match = pattern.search(text)
            if match:
                return match.group(0)
        time.sleep(0.5)
    raise RuntimeError(f"Tunnel URL not found. Check log: {LOG_PATH}")


def main() -> None:
    worker_url = os.environ.get("WORKER_LOCAL_URL", "http://127.0.0.1:8001")
    _download_cloudflared()

    existing = _existing_process()
    if existing is not None:
        print(f"Tunnel already running with PID {existing}")
        try:
            print(_wait_for_url(timeout=1.0))
        except RuntimeError:
            print(f"Log: {LOG_PATH}")
        return

    with LOG_PATH.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            [str(BIN_PATH), "tunnel", "--url", worker_url, "--no-autoupdate"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    PID_PATH.write_text(str(process.pid), encoding="utf-8")
    url = _wait_for_url()
    print(f"Tunnel started with PID {process.pid}")
    print(url)
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
