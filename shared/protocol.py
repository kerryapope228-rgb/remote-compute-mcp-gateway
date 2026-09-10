from typing import Any, Literal

from pydantic import BaseModel, Field


AllowedOperation = Literal["hello", "health", "gpu_info", "gpu_benchmark"]


class WorkerRequest(BaseModel):
    request_id: str = Field(min_length=1)
    operation: AllowedOperation
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerResponse(BaseModel):
    request_id: str
    ok: bool
    result: dict[str, Any] | None = None
    error: str | None = None
