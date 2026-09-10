from __future__ import annotations

from typing import Any

import colab.registration as registration


class DummyResponse:
    def __init__(self, data: dict[str, Any]):
        self._data = data

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._data


def test_register_once_uses_worker_health_capabilities(monkeypatch) -> None:
    posted: dict[str, Any] = {}

    monkeypatch.setattr(registration, "_registration_token", lambda explicit=None: "secret")
    monkeypatch.setattr(registration, "_wait_for_url", lambda: "https://worker.example")

    def fake_get(url: str, timeout: float):
        assert url == "http://127.0.0.1:8001/health"
        assert timeout == 10.0
        return DummyResponse(
            {
                "worker_id": "worker-1",
                "worker_kind": "colab",
                "capabilities": ["hello", "health", "gpu_info", "gpu_benchmark"],
            }
        )

    def fake_post(url: str, headers: dict[str, str], json: dict[str, Any], timeout: float):
        posted.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return DummyResponse({"status": "registered", "capabilities": json["capabilities"]})

    monkeypatch.setattr(registration.httpx, "get", fake_get)
    monkeypatch.setattr(registration.httpx, "post", fake_post)

    result = registration.register_once()

    assert posted["json"]["capabilities"] == ["hello", "health", "gpu_info", "gpu_benchmark"]
    assert posted["json"]["worker_id"] == "worker-1"
    assert posted["json"]["worker_kind"] == "colab"
    assert result["capabilities"][-1] == "gpu_benchmark"


def test_register_once_rejects_invalid_health_capabilities(monkeypatch) -> None:
    monkeypatch.setattr(registration, "_registration_token", lambda explicit=None: "secret")
    monkeypatch.setattr(registration, "_wait_for_url", lambda: "https://worker.example")
    monkeypatch.setattr(
        registration.httpx,
        "get",
        lambda url, timeout: DummyResponse({"capabilities": "hello,health"}),
    )

    try:
        registration.register_once()
    except RuntimeError as exc:
        assert "invalid capabilities" in str(exc)
    else:
        raise AssertionError("register_once should reject invalid capabilities")
