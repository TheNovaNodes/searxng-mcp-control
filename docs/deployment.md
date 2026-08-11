# Deployment & Setup Guide

This document provides instructions on how to install, configure, and run the **SearXNG MCP Control Server**.

## 1. Installation

The server is packaged as a standard Python module. It is recommended to use a virtual environment.

```bash
# Clone the repository
git clone <repository_url>
cd searxng-mcp-control

# Install the package with development dependencies
pip install -e .[dev]
```

## 2. Configuration (Environment Variables)

The MCP server uses environment variables to configure its connection to the underlying SearXNG infrastructure. These variables dictate where the configuration file is located, how to test the API, and how to control the Docker container.

| Variable | Default Value | Description |
| --- | --- | --- |
| `SEARXNG_SETTINGS_PATH` | `/home/ddoctorm/services/searxng/settings.yml` | Absolute path to the SearXNG YAML configuration file on the host machine. |
| `SEARXNG_URL` | `http://localhost:8081` | Base URL used for testing search API health. |
| `SEARXNG_CONTAINER_NAME` | `searxng-app` | Name of the Docker container running the SearXNG instance. |

**Example `.env` configuration:**
```env
SEARXNG_SETTINGS_PATH=/opt/searxng/settings.yml
SEARXNG_URL=http://localhost:8080
SEARXNG_CONTAINER_NAME=searxng
```

## 3. Running the Server

Once installed and configured, you can start the MCP server using the command-line interface provided by the package:

```bash
searxng-mcp-control
```

Alternatively, you can run the Python module directly:
```bash
python -m searxng_mcp_control.server
```

*(Note: The server runs in standard I/O mode for MCP, intended to be invoked by an MCP client rather than run as a standalone HTTP daemon.)*

## 4. Docker Container Lifecycle

The MCP server acts as a control plane for an *already running* Docker container.

The `restart_searxng_container` tool executes:
```bash
docker restart <SEARXNG_CONTAINER_NAME>
```

### Important Security Context:
- The MCP server must be run by a user that has permissions to execute `docker` commands (e.g., added to the `docker` group) on the host machine.
- Alternatively, if run within its own container, it must have the Docker socket mounted (`-v /var/run/docker.sock:/var/run/docker.sock`).

### TODO: SearXNG Infrastructure Deployment
*The scope of this project is to manage an existing SearXNG instance. For instructions on how to deploy the initial SearXNG Docker container (networks, volumes, port mapping), please refer to the official [SearXNG Docker Documentation](https://docs.searxng.org/admin/installation-docker.html).*
