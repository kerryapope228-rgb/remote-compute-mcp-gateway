from __future__ import annotations

import os
import socket
import threading
import time
from typing import Any

import httpx

from colab.start_tunnel import _wait_for_url

_DEFAULT_GATEWAY = "https://mcp.itaka.cc.cd"
_DEFAULT_LOCAL_WORKER = "http://127.0.0.1:8001"
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
    local_worker_url = os.environ.get("LOCAL_WORKER_URL", _DEFAULT_LOCAL_WORKER).rstrip("/")
    health_response = httpx.get(f"{local_worker_url}/health", timeout=10.0)
    health_response.raise_for_status()
    health = health_response.json()

    capabilities = health.get("capabilities")
    if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
        raise RuntimeError("worker /health returned invalid capabilities")

    payload = {
        "worker_id": health.get("worker_id") or os.environ.get("WORKER_ID", socket.gethostname()),
        "base_url": public_worker_url,
        "worker_kind": health.get("worker_kind") or os.environ.get("WORKER_KIND", "colab"),
        "capabilities": capabilities,
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
