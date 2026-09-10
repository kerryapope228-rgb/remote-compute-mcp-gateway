import pytest

from gateway.policy import PolicyDenied, ensure_operation_allowed


@pytest.mark.parametrize("operation", ["hello", "health", "gpu_info"])
def test_phase1_operations_are_allowed(operation: str) -> None:
    ensure_operation_allowed(operation)


@pytest.mark.parametrize("operation", ["exec", "shell", "run_python", "command"])
def test_execution_operations_are_denied(operation: str) -> None:
    with pytest.raises(PolicyDenied):
        ensure_operation_allowed(operation)
