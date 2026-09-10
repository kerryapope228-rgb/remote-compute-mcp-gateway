from __future__ import annotations

import hmac
import os

import uvicorn
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from gateway.mcp_server import mcp
from gateway.policy import ALLOWED_OPERATIONS
from gateway.registry import WorkerRegistration, registration_token, write_lease


async def register_worker(request: Request) -> JSONResponse:
    expected = registration_token()
    if not expected:
        return JSONResponse({"detail": "worker registration is not configured"}, status_code=503)

    authorization = request.headers.get("authorization")
    prefix = "Bearer "
    if not authorization or not authorization.startswith(prefix):
        return JSONResponse({"detail": "missing bearer token"}, status_code=401)
    supplied = authorization[len(prefix) :]
    if not hmac.compare_digest(supplied, expected):
        return JSONResponse({"detail": "invalid bearer token"}, status_code=403)

    try:
        registration = WorkerRegistration.model_validate(await request.json())
    except (ValidationError, ValueError) as exc:
        return JSONResponse({"detail": str(exc)}, status_code=422)

    if not set(registration.capabilities).issubset(ALLOWED_OPERATIONS):
        return JSONResponse({"detail": "unsupported worker capabilities"}, status_code=422)

    lease = write_lease(registration)
    return JSONResponse(
        {
            "status": "registered",
            "worker_id": lease.worker_id,
            "worker_kind": lease.worker_kind,
            "capabilities": lease.capabilities,
            "lease_seconds": 180,
        }
    )


app = mcp.streamable_http_app()
app.routes.insert(0, Route("/workers/register", register_worker, methods=["POST"]))


def main() -> None:
    uvicorn.run(
        "gateway.public_app:app",
        host=os.environ.get("MCP_HOST", "127.0.0.1"),
        port=int(os.environ.get("MCP_PORT", "8000")),
    )


if __name__ == "__main__":
    main()
