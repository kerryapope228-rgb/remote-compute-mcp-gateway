from __future__ import annotations

import os
import platform
import socket
import time
from typing import Any

from fastapi import FastAPI, HTTPException

from shared.protocol import WorkerRequest, WorkerResponse
from worker.colab_worker import handle_request

app = FastAPI(title="Remote Compute Worker", version="0.1.0")
STARTED_AT = time.time()
WORKER_ID = os.environ.get("WORKER_ID", socket.gethostname())
WORKER_KIND = os.environ.get("WORKER_KIND", "colab")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "worker_id": WORKER_ID,
        "worker_kind": WORKER_KIND,
        "hostname": socket.gethostname(),
        "python": platform.python_version(),
        "uptime_seconds": round(time.time() - STARTED_AT, 3),
        "capabilities": ["hello", "health", "gpu_info", "gpu_benchmark"],
    }


@app.get("/registration")
def registration() -> dict[str, Any]:
    return {
        "worker_id": WORKER_ID,
        "worker_kind": WORKER_KIND,
        "capabilities": ["hello", "health", "gpu_info", "gpu_benchmark"],
        "protocol_version": "1",
    }


@app.post("/invoke", response_model=WorkerResponse)
def invoke(request: WorkerRequest) -> WorkerResponse:
    response = handle_request(request)
    if not response.ok and response.error == "unsupported operation":
        raise HTTPException(status_code=403, detail=response.error)
    return response
