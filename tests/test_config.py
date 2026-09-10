import json

from gateway.config import config_path, worker_base_url


def test_worker_url_from_persisted_config(tmp_path, monkeypatch) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"worker_base_url": "https://worker.example"}), encoding="utf-8")
    monkeypatch.setenv("REMOTE_COMPUTE_GATEWAY_CONFIG", str(path))
    monkeypatch.delenv("WORKER_BASE_URL", raising=False)

    assert config_path() == path
    assert worker_base_url() == "https://worker.example"


def test_environment_worker_url_overrides_config(tmp_path, monkeypatch) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"worker_base_url": "https://persisted.example"}), encoding="utf-8")
    monkeypatch.setenv("REMOTE_COMPUTE_GATEWAY_CONFIG", str(path))
    monkeypatch.setenv("WORKER_BASE_URL", "https://override.example")

    assert worker_base_url() == "https://override.example"
