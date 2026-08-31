import os
import subprocess
import time
from typing import Any, Dict, List, Optional
import httpx
import yaml

try:
    from yaml import CSafeLoader as YamlSafeLoader, CSafeDumper as YamlSafeDumper
except ImportError:
    from yaml import SafeLoader as YamlSafeLoader, SafeDumper as YamlSafeDumper


try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

DEFAULT_SETTINGS_PATH = os.environ.get(
    "SEARXNG_SETTINGS_PATH", "/config/settings.yml"
)
DEFAULT_SEARXNG_URL = os.environ.get(
    "SEARXNG_URL", "http://localhost:8081"
)
DEFAULT_CONTAINER_NAME = os.environ.get(
    "SEARXNG_CONTAINER_NAME", "searxng-app"
)

mcp = FastMCP("SearXNG Control Plane")


@mcp.tool()
def inspect_settings(settings_path: Optional[str] = None) -> Dict[str, Any]:
    """Inspect SearXNG configuration settings and active/disabled engines from settings.yml.

    Args:
        settings_path: Optional path to settings.yml. Defaults to SEARXNG_SETTINGS_PATH.
    """
    path = settings_path or DEFAULT_SETTINGS_PATH
    if not os.path.exists(path):
        return {
            "success": False,
            "error": f"Settings file not found at path: {path}",
            "settings_path": path,
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.load(f, Loader=YamlSafeLoader) or {}

        engines = data.get("engines", [])
        enabled_engines = []
        disabled_engines = []

        for eng in engines:
            name = eng.get("name", "unknown")
            is_disabled = eng.get("disabled", False)
            if is_disabled:
                disabled_engines.append(name)
            else:
                enabled_engines.append(name)

        return {
            "success": True,
            "settings_path": path,
            "general": data.get("general", {}),
            "server": data.get("server", {}),
            "search": data.get("search", {}),
            "outgoing": data.get("outgoing", {}),
            "use_default_settings": data.get("use_default_settings", True),
            "engine_summary": {
                "total_configured": len(engines),
                "enabled_count": len(enabled_engines),
                "disabled_count": len(disabled_engines),
                "enabled_engines": enabled_engines,
                "disabled_engines": disabled_engines,
            },
            "raw_engines": engines,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to read/parse settings file: {str(e)}",
            "settings_path": path,
        }


@mcp.tool()
def set_engine_status(
    engine_name: str, enabled: bool, settings_path: Optional[str] = None
) -> Dict[str, Any]:
    """Enable or disable a search engine in settings.yml.

    Args:
        engine_name: Name of the engine (e.g. 'google cse', 'duckduckgo', 'bing').
        enabled: True to enable the engine, False to disable it.
        settings_path: Optional path to settings.yml. Defaults to SEARXNG_SETTINGS_PATH.
    """
    path = settings_path or DEFAULT_SETTINGS_PATH
    if not os.path.exists(path):
        return {
            "success": False,
            "error": f"Settings file not found at path: {path}",
            "settings_path": path,
        }

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.load(f, Loader=YamlSafeLoader) or {}

        engines = data.get("engines", [])
        updated = False
        target_name_lower = engine_name.strip().lower()

        for eng in engines:
            if eng.get("name", "").strip().lower() == target_name_lower:
                eng["disabled"] = not enabled
                updated = True
                break

        if not updated:
            engines.append({"name": engine_name, "disabled": not enabled})
            data["engines"] = engines

        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, Dumper=YamlSafeDumper, sort_keys=False, default_flow_style=False)

        status_str = "enabled" if enabled else "disabled"
        return {
            "success": True,
            "engine_name": engine_name,
            "enabled": enabled,
            "message": f"Successfully set search engine '{engine_name}' to {status_str} in {path}.",
            "settings_path": path,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update settings file: {str(e)}",
            "settings_path": path,
        }


@mcp.tool()
def enable_engine(
    engine_name: str, settings_path: Optional[str] = None
) -> Dict[str, Any]:
    """Enable a specific search engine in SearXNG settings.yml.

    Args:
        engine_name: Name of the engine to enable (e.g. 'duckduckgo').
        settings_path: Optional path to settings.yml.
    """
    return set_engine_status(engine_name, enabled=True, settings_path=settings_path)


@mcp.tool()
def disable_engine(
    engine_name: str, settings_path: Optional[str] = None
) -> Dict[str, Any]:
    """Disable a specific search engine in SearXNG settings.yml.

    Args:
        engine_name: Name of the engine to disable (e.g. 'duckduckgo').
        settings_path: Optional path to settings.yml.
    """
    return set_engine_status(engine_name, enabled=False, settings_path=settings_path)


@mcp.tool()
def test_search_api_health(
    url: Optional[str] = None, query: str = "healthcheck"
) -> Dict[str, Any]:
    """Test SearXNG Search API health by issuing a test query and measuring latency.

    Args:
        url: Base URL or search endpoint of SearXNG instance (defaults to SEARXNG_URL).
        query: Test search query string (defaults to 'healthcheck').
    """
    base_url = url or DEFAULT_SEARXNG_URL
    search_url = base_url.rstrip("/")
    if not search_url.endswith("/search"):
        search_url += "/search"

    start_time = time.time()
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(search_url, params={"q": query, "format": "json"})
            latency_ms = round((time.time() - start_time) * 1000, 2)

            if resp.status_code == 200:
                try:
                    json_data = resp.json()
                    results = json_data.get("results", [])
                    sample_titles = [r.get("title", "") for r in results[:3]]
                    return {
                        "healthy": True,
                        "status_code": resp.status_code,
                        "latency_ms": latency_ms,
                        "search_url": search_url,
                        "query": query,
                        "result_count": len(results),
                        "sample_titles": sample_titles,
                    }
                except Exception as parse_err:
                    return {
                        "healthy": False,
                        "status_code": resp.status_code,
                        "latency_ms": latency_ms,
                        "search_url": search_url,
                        "error": f"Response returned status 200 but failed to parse JSON: {str(parse_err)}",
                    }
            else:
                return {
                    "healthy": False,
                    "status_code": resp.status_code,
                    "latency_ms": latency_ms,
                    "search_url": search_url,
                    "error": f"HTTP request failed with status code {resp.status_code}",
                }
    except Exception as req_err:
        latency_ms = round((time.time() - start_time) * 1000, 2)
        return {
            "healthy": False,
            "latency_ms": latency_ms,
            "search_url": search_url,
            "error": f"Connection/Request failed: {str(req_err)}",
        }


@mcp.tool()
def restart_searxng_container(
    container_name: Optional[str] = None
) -> Dict[str, Any]:
    """Restart the SearXNG Docker container via subprocess.

    Args:
        container_name: Name of the docker container (defaults to SEARXNG_CONTAINER_NAME).
    """
    target = container_name or DEFAULT_CONTAINER_NAME
    cmd = ["docker", "restart", target]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        success = res.returncode == 0
        return {
            "success": success,
            "container_name": target,
            "returncode": res.returncode,
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "message": (
                f"Successfully restarted Docker container '{target}'"
                if success
                else f"Failed to restart Docker container '{target}': {res.stderr.strip()}"
            ),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "container_name": target,
            "error": f"Command '{' '.join(cmd)}' timed out after 30 seconds.",
        }
    except Exception as e:
        return {
            "success": False,
            "container_name": target,
            "error": f"Subprocess error executing command: {str(e)}",
        }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
