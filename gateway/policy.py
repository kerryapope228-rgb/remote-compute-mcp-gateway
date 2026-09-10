ALLOWED_OPERATIONS = frozenset({"hello", "health", "gpu_info", "gpu_benchmark"})


class PolicyDenied(ValueError):
    pass


def ensure_operation_allowed(operation: str) -> None:
    if operation not in ALLOWED_OPERATIONS:
        raise PolicyDenied(f"operation is not allowed: {operation}")
