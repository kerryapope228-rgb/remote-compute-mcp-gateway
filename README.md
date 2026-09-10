# Remote Compute MCP Gateway

Phase 1 isolated proof of concept for a stable MCP Gateway with pluggable remote compute Workers.

## Phase 1 scope

Allowed operations:

- `hello`
- `health`
- `gpu_info`

Explicitly out of scope:

- raw `exec`
- shell access
- arbitrary command execution
- arbitrary code execution

## Architecture

```text
ChatGPT / MCP client
        |
        v
Fixed MCP Gateway
        |
        v
Policy / Sandbox boundary
        |
        v
Worker adapter
        |
        v
Google Colab Worker (first provider)
```

The current worker adapter is local and exists only to validate the Gateway/Worker protocol. The next step is to replace the local transport with a real HTTPS/tunnel connection to a Colab Worker without changing the public tool surface.

## Development

Install the project in an isolated Python environment, including the `dev` extra, then run `pytest`.
