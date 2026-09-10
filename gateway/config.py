from __future__ import annotations

import json
import os
from pathlib import Path

_CONFIG_ENV = "REMOTE_COMPUTE_GATEWAY_CONFIG"
_PROJECT_CONFIG = Path(__file__).resolve().parents[1] / "config.local.json"
_USER_CONFIG = Path.home() / ".remote-compute-mcp-gateway" / "config.json"


def config_path() -> Path:
    override = os.environ.get(_CONFIG_ENV)
    if override:
        return Path(override).expanduser()
    if _PROJECT_CONFIG.is_file():
        return _PROJECT_CONFIG
    return _USER_CONFIG


def load_config() -> dict:
    path = config_path()
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Gateway config must be a JSON object: {path}")
    return data


def worker_base_url() -> str | None:
    """Resolve the worker URL; environment override wins over persisted config."""
    env_url = os.environ.get("WORKER_BASE_URL")
    if env_url:
        return env_url.strip() or None

    value = load_config().get("worker_base_url")
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("worker_base_url must be a string")
    return value.strip() or None
