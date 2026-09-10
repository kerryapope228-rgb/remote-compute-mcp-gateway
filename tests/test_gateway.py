from gateway.tools import gpu_info, health, hello


def test_hello() -> None:
    result = hello()
    assert result["message"] == "hello from colab worker"


def test_health() -> None:
    result = health()
    assert result["status"] == "ok"
    assert "python" in result


def test_gpu_info_contract() -> None:
    result = gpu_info()
    assert result["provider"] == "colab"
    assert "available" in result
