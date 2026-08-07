# SearXNG Control Plane MCP Server

An Model Context Protocol (MCP) server for managing SearXNG instances, configuration settings, search engine states, API health checking, and container lifecycle.

## Features

- **Inspect Settings**: Read and parse SearXNG configuration settings (`settings.yml`), listing active/disabled engines and configuration parameters.
- **Enable/Disable Search Engines**: Toggle individual search engines on or off directly within `settings.yml`.
- **Health Testing**: Test search API health by sending query requests and verifying HTTP response codes, latency, and JSON result payloads.
- **Container Control**: Restart the SearXNG Docker container (`searxng-app`) via subprocess.

## Configuration

Environment variables can be used to override default settings:

| Variable | Default Value | Description |
| --- | --- | --- |
| `SEARXNG_SETTINGS_PATH` | `/home/ddoctorm/services/searxng/settings.yml` | Path to SearXNG `settings.yml` file |
| `SEARXNG_URL` | `http://localhost:8081` | Base URL of SearXNG instance |
| `SEARXNG_CONTAINER_NAME` | `searxng-app` | Name of the Docker container running SearXNG |

## Installation & Setup

```bash
pip install -e .
```

## Available MCP Tools

- `inspect_settings`: Inspect current SearXNG configuration settings and list enabled/disabled search engines.
- `enable_engine`: Enable a specific search engine in `settings.yml`.
- `disable_engine`: Disable a specific search engine in `settings.yml`.
- `set_engine_status`: Set explicit enabled/disabled state for a search engine in `settings.yml`.
- `test_search_api_health`: Perform a health check query against the SearXNG search endpoint.
- `restart_searxng_container`: Restart the SearXNG Docker container via subprocess.

## License

MIT
