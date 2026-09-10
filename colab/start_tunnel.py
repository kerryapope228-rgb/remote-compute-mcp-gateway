from __future__ import annotations

import os
import re
import signal
import subprocess
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


def start_tunnel(worker_url: str | None = None) -> dict[str, object]:
    target = worker_url or os.environ.get("WORKER_LOCAL_URL", "http://127.0.0.1:8001")
    _download_cloudflared()

    existing = _existing_process()
    if existing is not None:
        return {
            "status": "already_running",
            "pid": existing,
            "url": _wait_for_url(timeout=1.0),
        }

    with LOG_PATH.open("w", encoding="utf-8") as log_handle:
        process = subprocess.Popen(
            [str(BIN_PATH), "tunnel", "--url", target, "--no-autoupdate"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    PID_PATH.write_text(str(process.pid), encoding="utf-8")
    url = _wait_for_url()
    return {"status": "started", "pid": process.pid, "url": url}


def stop_tunnel(timeout: float = 5.0) -> dict[str, object]:
    pid = _existing_process()
    if pid is None:
        PID_PATH.unlink(missing_ok=True)
        return {"status": "not_running"}

    os.kill(pid, signal.SIGTERM)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            PID_PATH.unlink(missing_ok=True)
            return {"status": "stopped", "pid": pid}
        time.sleep(0.1)

    os.kill(pid, signal.SIGKILL)
    PID_PATH.unlink(missing_ok=True)
    return {"status": "killed", "pid": pid}


def restart_tunnel(worker_url: str | None = None) -> dict[str, object]:
    previous_url: str | None = None
    try:
        previous_url = _wait_for_url(timeout=1.0)
    except RuntimeError:
        pass

    stop_tunnel()
    result = start_tunnel(worker_url)
    result["previous_url"] = previous_url
    return result


def main() -> None:
    result = start_tunnel()
    print(f"Tunnel status: {result['status']}")
    print(f"PID: {result['pid']}")
    print(result["url"])
    print(f"Log: {LOG_PATH}")


if __name__ == "__main__":
    main()
