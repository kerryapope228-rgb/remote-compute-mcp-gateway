from __future__ import annotations

import httpx

from gateway.config import worker_base_url
from gateway.registry import read_lease
from shared.protocol import WorkerRequest, WorkerResponse
from worker.colab_worker import handle_request


class LocalWorkerClient:
    """Local adapter used for tests and offline validation."""

    def call(self, request: WorkerRequest) -> WorkerResponse:
        return handle_request(request)

    def health(self) -> dict:
        return {"status": "ok", "transport": "local"}


class RemoteWorkerClient:
    """HTTP client for a remote worker exposing only the Phase 1 API."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def call(self, request: WorkerRequest) -> WorkerResponse:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/invoke",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return WorkerResponse.model_validate(response.json())

    def health(self) -> dict:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    def registration(self) -> dict:
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = client.get(f"{self.base_url}/registration")
            response.raise_for_status()
            return response.json()


def build_worker_client():
    lease = read_lease()
    if lease:
        return RemoteWorkerClient(lease.base_url)

    worker_url = worker_base_url()
    if worker_url:
        return RemoteWorkerClient(worker_url)
    return LocalWorkerClient()
