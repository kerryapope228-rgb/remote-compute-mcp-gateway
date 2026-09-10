from fastapi.testclient import TestClient

from worker.app import app


client = TestClient(app)


def test_worker_registration_is_whitelisted():
    response = client.get("/registration")
    assert response.status_code == 200
    data = response.json()
    assert data["capabilities"] == ["hello", "health", "gpu_info"]
    assert data["protocol_version"] == "1"


def test_worker_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_worker_invoke_hello():
    response = client.post(
        "/invoke",
        json={"request_id": "test-1", "operation": "hello", "payload": {}},
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_worker_rejects_exec_at_schema_boundary():
    response = client.post(
        "/invoke",
        json={"request_id": "test-2", "operation": "exec", "payload": {"command": "whoami"}},
    )
    assert response.status_code == 422
