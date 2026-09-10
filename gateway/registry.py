from __future__ import annotations

import json
import time
from pathlib import Path

from pydantic import BaseModel, Field, HttpUrl

from gateway.config import config_path, load_config


class WorkerRegistration(BaseModel):
    worker_id: str = Field(min_length=1, max_length=128)
    base_url: HttpUrl
    worker_kind: str = Field(default="colab", min_length=1, max_length=64)
    capabilities: list[str] = Field(default_factory=list, max_length=16)


class WorkerLease(BaseModel):
    worker_id: str
    base_url: str
    worker_kind: str
    capabilities: list[str]
    updated_at: float


def registry_path() -> Path:
    cfg = load_config()
    explicit = cfg.get("registry_path")
    if isinstance(explicit, str) and explicit.strip():
        return Path(explicit).expanduser()
    return config_path().with_name("worker-registry.json")


def registration_token() -> str | None:
    value = load_config().get("registration_token")
    return value.strip() if isinstance(value, str) and value.strip() else None


def write_lease(registration: WorkerRegistration) -> WorkerLease:
    lease = WorkerLease(
        worker_id=registration.worker_id,
        base_url=str(registration.base_url).rstrip("/"),
        worker_kind=registration.worker_kind,
        capabilities=registration.capabilities,
        updated_at=time.time(),
    )
    path = registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(lease.model_dump_json(indent=2), encoding="utf-8")
    return lease


def read_lease(max_age_seconds: float = 180.0) -> WorkerLease | None:
    path = registry_path()
    if not path.is_file():
        return None
    lease = WorkerLease.model_validate_json(path.read_text(encoding="utf-8"))
    if time.time() - lease.updated_at > max_age_seconds:
        return None
    return lease
