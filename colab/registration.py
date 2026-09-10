from __future__ import annotations

import os
import socket
import threading
import time
from typing import Any

import httpx

from colab.start_tunnel import _wait_for_url

_DEFAULT_GATEWAY = "https://mcp.itaka.cc.cd"
_THREAD: threading.Thread | None = None
_STOP = threading.Event()


def _registration_token(explicit: str | None = None) -> str | None:
    if explicit:
        return explicit
    env_token = os.environ.get("GATEWAY_REGISTRATION_TOKEN")
    if env_token:
        return env_token
    try:
        from google.colab import userdata

        return userdata.get("GATEWAY_REGISTRATION_TOKEN")
    except Exception:
        return None


def register_once(
    *,
    gateway_url: str | None = None,
    token: str | None = None,
    worker_url: str | None = None,
) -> dict[str, Any]:
    gateway = (gateway_url or os.environ.get("GATEWAY_PUBLIC_URL") or _DEFAULT_GATEWAY).rstrip("/")
    bearer = _registration_token(token)
    if not bearer:
        raise RuntimeError("GATEWAY_REGISTRATION_TOKEN is required")

    public_worker_url = worker_url or _wait_for_url()
    payload = {
        "worker_id": os.environ.get("WORKER_ID", socket.gethostname()),
        "base_url": public_worker_url,
        "worker_kind": os.environ.get("WORKER_KIND", "colab"),
        "capabilities": ["hello", "health", "gpu_info"],
    }
    response = httpx.post(
        f"{gateway}/workers/register",
        headers={"Authorization": f"Bearer {bearer}"},
        json=payload,
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json()


def start_heartbeat(interval_seconds: float = 60.0) -> dict[str, Any]:
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        return {"status": "already_running", "thread": _THREAD.name}

    _STOP.clear()

    def loop() -> None:
        while not _STOP.is_set():
            try:
                register_once()
            except Exception as exc:
                print(f"Worker registration heartbeat failed: {exc}")
            _STOP.wait(interval_seconds)

    _THREAD = threading.Thread(
        target=loop,
        name="remote-compute-worker-registration",
        daemon=True,
    )
    _THREAD.start()
    return {"status": "started", "thread": _THREAD.name, "interval_seconds": interval_seconds}


def stop_heartbeat() -> dict[str, Any]:
    _STOP.set()
    return {"status": "stopping"}
