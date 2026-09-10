ALLOWED_OPERATIONS = frozenset({"hello", "health", "gpu_info"})


class PolicyDenied(ValueError):
    pass


def ensure_operation_allowed(operation: str) -> None:
    if operation not in ALLOWED_OPERATIONS:
        raise PolicyDenied(f"operation is not allowed in phase 1: {operation}")
