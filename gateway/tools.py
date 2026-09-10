from __future__ import annotations

from uuid import uuid4

from gateway.policy import ensure_operation_allowed
from gateway.worker_client import build_worker_client
from shared.protocol import WorkerRequest


def call_tool(operation: str, payload: dict | None = None) -> dict:
    ensure_operation_allowed(operation)
    request = WorkerRequest(
        request_id=str(uuid4()),
        operation=operation,
        payload=payload or {},
    )
    worker = build_worker_client()
    response = worker.call(request)
    if not response.ok:
        raise RuntimeError(response.error or "worker call failed")
    return response.result or {}


def hello() -> dict:
    return call_tool("hello")


def health() -> dict:
    return call_tool("health")


def gpu_info() -> dict:
    return call_tool("gpu_info")
