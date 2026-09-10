from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from gateway.tools import gpu_info as gateway_gpu_info
from gateway.tools import health as gateway_health
from gateway.tools import hello as gateway_hello


_allowed_hosts = [
    host.strip()
    for host in os.environ.get("MCP_ALLOWED_HOSTS", "127.0.0.1:8000,localhost:8000,mcp.itaka.cc.cd").split(",")
    if host.strip()
]


mcp = FastMCP(
    name="Remote Compute MCP Gateway",
    instructions=(
        "Phase 1 isolated remote compute gateway. Only hello, health, and gpu_info "
        "are exposed. Raw exec, shell, arbitrary command execution, and arbitrary "
        "code execution are intentionally unavailable."
    ),
    host=os.environ.get("MCP_HOST", "127.0.0.1"),
    port=int(os.environ.get("MCP_PORT", "8000")),
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts,
    ),
)


@mcp.tool()
def hello() -> dict:
    """Verify the MCP-to-Gateway-to-Worker call path."""
    return gateway_hello()


@mcp.tool()
def health() -> dict:
    """Return the current remote Worker health information."""
    return gateway_health()


@mcp.tool()
def gpu_info() -> dict:
    """Return the remote Worker's GPU information without exposing shell access."""
    return gateway_gpu_info()


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
