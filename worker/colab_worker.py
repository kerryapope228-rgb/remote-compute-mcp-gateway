from __future__ import annotations

import platform
import socket
import time
from typing import Any


def _detect_gpu() -> dict[str, Any]:
    try:
        import torch
    except ImportError:
        return {
            "available": False,
            "provider": "colab",
            "backend": "torch",
            "detail": "PyTorch is not installed in the worker environment.",
        }

    available = bool(torch.cuda.is_available())
    result: dict[str, Any] = {
        "available": available,
        "provider": "colab",
        "backend": "torch",
        "torch_version": torch.__version__,
    }
    if available:
        index = torch.cuda.current_device()
        props = torch.cuda.get_device_properties(index)
        result.update(
            {
                "device_index": index,
                "device_name": torch.cuda.get_device_name(index),
                "device_count": torch.cuda.device_count(),
                "total_memory_bytes": props.total_memory,
                "compute_capability": [props.major, props.minor],
            }
        )
    else:
        result["detail"] = "CUDA is not available to PyTorch in this runtime."
    return result

def _gpu_benchmark(payload: dict[str, Any]) -> dict[str, Any]:
    """Run a bounded CUDA matrix-multiplication benchmark; never executes user code."""
    size = payload.get("matrix_size", 2048)
    iterations = payload.get("iterations", 5)
    if type(size) is not int or not 256 <= size <= 4096:
        raise ValueError("matrix_size must be an integer between 256 and 4096")
    if type(iterations) is not int or not 1 <= iterations <= 20:
        raise ValueError("iterations must be an integer between 1 and 20")

    try:
        import torch
    except ImportError:
        return {"available": False, "detail": "PyTorch is not installed."}

    if not torch.cuda.is_available():
        return {"available": False, "detail": "CUDA is not available to PyTorch."}

    device = torch.device("cuda")
    a = torch.randn((size, size), device=device, dtype=torch.float32)
    b = torch.randn((size, size), device=device, dtype=torch.float32)
    torch.matmul(a, b)
    torch.cuda.synchronize()

    started = time.perf_counter()
    for _ in range(iterations):
        torch.matmul(a, b)
    torch.cuda.synchronize()
    elapsed = time.perf_counter() - started

    operations = 2 * (size**3) * iterations
    return {
        "available": True,
        "device_name": torch.cuda.get_device_name(torch.cuda.current_device()),
        "matrix_size": size,
        "iterations": iterations,
        "dtype": "float32",
        "elapsed_seconds": round(elapsed, 6),
        "estimated_tflops": round(operations / elapsed / 1e12, 3),
    }


from shared.protocol import WorkerRequest, WorkerResponse


def handle_request(request: WorkerRequest) -> WorkerResponse:
    if request.operation == "hello":
        result: dict[str, Any] = {"message": "hello from colab worker"}
    elif request.operation == "health":
        result = {
            "status": "ok",
            "hostname": socket.gethostname(),
            "python": platform.python_version(),
        }
    elif request.operation == "gpu_info":
        result = _detect_gpu()
    elif request.operation == "gpu_benchmark":
        try:
            result = _gpu_benchmark(request.payload)
        except ValueError as exc:
            return WorkerResponse(request_id=request.request_id, ok=False, error=str(exc))
    else:
        return WorkerResponse(
            request_id=request.request_id,
            ok=False,
            error="unsupported operation",
        )

    return WorkerResponse(request_id=request.request_id, ok=True, result=result)
