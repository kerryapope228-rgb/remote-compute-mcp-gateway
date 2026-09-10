from fastapi import FastAPI, HTTPException

from gateway.policy import PolicyDenied
from gateway.tools import gpu_info, health, hello

app = FastAPI(title="Remote Compute MCP Gateway", version="0.1.0")


@app.get("/health")
def gateway_health() -> dict:
    return {"gateway": "ok", "worker": health()}


@app.post("/tools/hello")
def tool_hello() -> dict:
    return hello()


@app.post("/tools/health")
def tool_health() -> dict:
    return health()


@app.post("/tools/gpu_info")
def tool_gpu_info() -> dict:
    return gpu_info()


@app.exception_handler(PolicyDenied)
def policy_denied_handler(_, exc: PolicyDenied):
    raise HTTPException(status_code=403, detail=str(exc))
