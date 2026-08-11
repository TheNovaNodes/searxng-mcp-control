# API Reference (Data Flow & MCP Tools)

The SearXNG MCP Control Server exposes several MCP (Model Context Protocol) tools that allow agents to interact with the SearXNG infrastructure. This document details each tool, its parameters, data flow, and expected responses.

## 1. Data Transformation and Flow Overview

- **Input Sanitization:** All file paths passed as arguments fallback to environment variable defaults if omitted.
- **YAML Data Flow:**
  - Read: `settings.yml` -> `yaml.safe_load()` -> Python `dict`.
  - Process: Iteration over `engines` list, matching engine names (case-insensitively).
  - Write: Python `dict` -> `yaml.safe_dump(sort_keys=False, default_flow_style=False)` -> `settings.yml`.
- **Search Data Flow:**
  - URL provided by the user -> normalized to end in `/search`.
  - HTTP GET request sent with query parameters `?q={query}&format=json`.
  - JSON response parsed -> subset of fields (`results`, `title`) extracted and counted -> MCP response object.

---

## 2. MCP Tools Documentation

### 2.1. `inspect_settings`

Reads and parses the SearXNG `settings.yml` configuration. It aggregates search engine states (enabled/disabled) and general server parameters.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `settings_path` | `string` | No | `SEARXNG_SETTINGS_PATH` | Path to the SearXNG `settings.yml` file. |

**Response Format**

Returns a dictionary containing configuration settings.

| Field | Type | Description |
| --- | --- | --- |
| `success` | `boolean` | Indicates if parsing was successful. |
| `settings_path` | `string` | The path of the file that was read. |
| `engine_summary` | `object` | Summary of engine states (counts and lists of enabled/disabled engines). |
| `general` | `object` | The parsed `general` section of `settings.yml`. |
| `server` | `object` | The parsed `server` section of `settings.yml`. |
| `search` | `object` | The parsed `search` section of `settings.yml`. |
| `error` | `string` | Contains error message if `success` is `false`. |

---

### 2.2. `set_engine_status`

Explicitly enables or disables a search engine in `settings.yml`.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `engine_name` | `string` | Yes | - | Name of the search engine (e.g., 'google cse', 'duckduckgo'). |
| `enabled` | `boolean`| Yes | - | `True` to enable, `False` to disable the engine. |
| `settings_path` | `string` | No | `SEARXNG_SETTINGS_PATH` | Path to the SearXNG `settings.yml` file. |

**Response Format**

| Field | Type | Description |
| --- | --- | --- |
| `success` | `boolean` | Indicates if the file was updated successfully. |
| `engine_name` | `string` | The requested engine name. |
| `enabled` | `boolean` | The new state applied to the engine. |
| `message` | `string` | Success message. |
| `error` | `string` | Contains error message if `success` is `false`. |

---

### 2.3. `enable_engine`

Convenience wrapper to enable a specific search engine.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `engine_name` | `string` | Yes | - | Name of the search engine to enable. |
| `settings_path` | `string` | No | `SEARXNG_SETTINGS_PATH` | Path to the SearXNG `settings.yml` file. |

**Response:** Same as `set_engine_status`.

---

### 2.4. `disable_engine`

Convenience wrapper to disable a specific search engine.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `engine_name` | `string` | Yes | - | Name of the search engine to disable. |
| `settings_path` | `string` | No | `SEARXNG_SETTINGS_PATH` | Path to the SearXNG `settings.yml` file. |

**Response:** Same as `set_engine_status`.

---

### 2.5. `test_search_api_health`

Tests the SearXNG Search API health by issuing a test query and measuring latency.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `url` | `string` | No | `SEARXNG_URL` | Base URL or search endpoint of the SearXNG instance. |
| `query` | `string` | No | `"healthcheck"` | Test search query string. |

**Response Format**

| Field | Type | Description |
| --- | --- | --- |
| `healthy` | `boolean` | `true` if the HTTP request returns 200 and JSON parses successfully. |
| `status_code` | `integer` | HTTP status code returned by the server. |
| `latency_ms` | `float` | Wall-clock latency in milliseconds. |
| `search_url` | `string` | The normalized endpoint URL queried. |
| `result_count`| `integer` | Number of items in the parsed JSON `results` array. |
| `sample_titles`| `array` | Preview sample of up to 3 result titles. |
| `error` | `string` | Detailed error context if `healthy` is `false`. |

---

### 2.6. `restart_searxng_container`

Restarts the SearXNG Docker container via a shell subprocess.

**Parameters**

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `container_name` | `string` | No | `SEARXNG_CONTAINER_NAME`| Name of the Docker container running SearXNG. |

**Response Format**

| Field | Type | Description |
| --- | --- | --- |
| `success` | `boolean` | `true` if the shell command returns exit code `0`. |
| `container_name` | `string` | The container target used. |
| `returncode` | `integer` | Subprocess exit code. |
| `stdout` | `string` | Standard output captured from the Docker daemon. |
| `stderr` | `string` | Standard error captured from the Docker daemon. |
| `message` | `string` | Summary message of the action. |
| `error` | `string` | Error trace if subprocess times out or crashes. |
