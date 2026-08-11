# SearXNG Control Plane MCP Server

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![MCP](https://img.shields.io/badge/Protocol-MCP-green)
![Docker](https://img.shields.io/badge/Docker-Control-blue)
![License](https://img.shields.io/badge/License-MIT-green)

An **Model Context Protocol (MCP)** server for managing SearXNG instances.

This server acts as a control plane, empowering LLM agents to inspect settings, toggle search engines dynamically, monitor API health, and manage container lifecycles securely and reliably.

This repository is part of the **TheNovaNodes Antigravity Agent Ecosystem**.

## 📚 Documentation

For an in-depth understanding of the system, please refer to the documentation:

* 🏗️ **[Architecture](docs/architecture.md):** High-level design, Mermaid.js diagrams, subsystem logic, and data flows.
* 🛠️ **[API Reference](docs/api-reference.md):** Detailed documentation of all MCP tools, parameters, and payloads.
* 🚀 **[Deployment Guide](docs/deployment.md):** Installation, configuration (environment variables), and execution.

## Quickstart

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests
python -m pytest tests/

# Start the MCP server
searxng-mcp-control
```

## License
MIT
