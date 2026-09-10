from __future__ import annotations

import platform
import socket
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
    else:
        return WorkerResponse(
            request_id=request.request_id,
            ok=False,
            error="unsupported operation",
        )

    return WorkerResponse(request_id=request.request_id, ok=True, result=result)
