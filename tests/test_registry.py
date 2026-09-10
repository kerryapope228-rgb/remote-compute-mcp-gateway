import json
import time

from fastapi.testclient import TestClient

from gateway.public_app import app
from gateway.registry import WorkerLease, read_lease


def test_registration_requires_token(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"registration_token": "secret"}), encoding="utf-8")
    monkeypatch.setenv("REMOTE_COMPUTE_GATEWAY_CONFIG", str(config))

    client = TestClient(app)
    response = client.post(
        "/workers/register",
        json={
            "worker_id": "w1",
            "base_url": "https://worker.example",
            "worker_kind": "colab",
            "capabilities": ["hello", "health", "gpu_info"],
        },
    )
    assert response.status_code == 401


def test_registration_writes_active_lease(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"registration_token": "secret"}), encoding="utf-8")
    monkeypatch.setenv("REMOTE_COMPUTE_GATEWAY_CONFIG", str(config))

    client = TestClient(app)
    response = client.post(
        "/workers/register",
        headers={"Authorization": "Bearer secret"},
        json={
            "worker_id": "w1",
            "base_url": "https://worker.example",
            "worker_kind": "colab",
            "capabilities": ["hello", "health", "gpu_info"],
        },
    )
    assert response.status_code == 200
    lease = read_lease()
    assert lease is not None
    assert lease.worker_id == "w1"
    assert lease.base_url == "https://worker.example"


def test_expired_lease_is_ignored(tmp_path, monkeypatch) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setenv("REMOTE_COMPUTE_GATEWAY_CONFIG", str(config))
    registry = tmp_path / "worker-registry.json"
    registry.write_text(
        WorkerLease(
            worker_id="w1",
            base_url="https://worker.example",
            worker_kind="colab",
            capabilities=["hello"],
            updated_at=time.time() - 999,
        ).model_dump_json(),
        encoding="utf-8",
    )
    assert read_lease(max_age_seconds=180) is None
