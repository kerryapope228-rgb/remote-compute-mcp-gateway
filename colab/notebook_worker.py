from __future__ import annotations

import threading
import time

import uvicorn

from worker.app import app


_server: uvicorn.Server | None = None
_thread: threading.Thread | None = None


def start_worker(host: str = "127.0.0.1", port: int = 8001, timeout: float = 10.0) -> dict[str, object]:
    global _server, _thread

    if _thread is not None and _thread.is_alive() and _server is not None:
        return {
            "status": "already_running",
            "host": host,
            "port": port,
        }

    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True, name="remote-compute-worker")

    _server = server
    _thread = thread
    thread.start()

    deadline = time.time() + timeout
    while time.time() < deadline:
        if server.started:
            return {
                "status": "started",
                "host": host,
                "port": port,
                "thread": thread.name,
            }
        if not thread.is_alive():
            break
        time.sleep(0.05)

    raise RuntimeError("Worker did not start within timeout")


def stop_worker(timeout: float = 5.0) -> dict[str, object]:
    global _server, _thread

    if _server is None or _thread is None or not _thread.is_alive():
        return {"status": "not_running"}

    _server.should_exit = True
    _thread.join(timeout=timeout)
    stopped = not _thread.is_alive()

    if stopped:
        _server = None
        _thread = None

    return {"status": "stopped" if stopped else "stopping"}
