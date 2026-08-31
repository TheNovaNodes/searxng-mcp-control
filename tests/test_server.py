"""Comprehensive unit and integration test suite for SearXNG MCP Control Server."""

import os
import subprocess
from unittest.mock import MagicMock, patch
import pytest
import yaml

from searxng_mcp_control.server import (
    DEFAULT_CONTAINER_NAME,
    DEFAULT_SETTINGS_PATH,
    DEFAULT_SEARXNG_URL,
    disable_engine,
    enable_engine,
    inspect_settings,
    main,
    restart_searxng_container,
    set_engine_status,
    test_search_api_health as api_test_search_health,
)


@pytest.fixture
def sample_settings_dict():
    """Fixture providing a rich sample SearXNG settings dictionary."""
    return {
        "use_default_settings": True,
        "general": {
            "instance_name": "SearXNG Test Engine",
            "enable_metrics": True,
        },
        "server": {
            "secret_key": "test_secret_key_12345",
            "limiter": False,
            "image_proxy": True,
        },
        "search": {
            "safe_search": 0,
            "autocomplete": "google",
            "formats": ["html", "json"],
        },
        "outgoing": {
            "request_timeout": 2.0,
            "max_request_timeout": 3.0,
        },
        "engines": [
            {"name": "duckduckgo", "disabled": True},
            {"name": "google cse", "disabled": False},
            {"name": "bing", "disabled": False},
            {"name": "startpage", "disabled": True},
            {"name": "brave", "disabled": True},
        ],
    }


@pytest.fixture
def temp_settings_file(tmp_path, sample_settings_dict):
    """Fixture creating a temporary settings.yml file."""
    settings_file = tmp_path / "settings.yml"
    with open(settings_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(sample_settings_dict, f)
    return str(settings_file)


class TestInspectSettings:
    """Unit tests for the inspect_settings tool."""

    def test_inspect_settings_nonexistent_file(self, tmp_path):
        """Test inspect_settings with a path that does not exist."""
        nonexistent = str(tmp_path / "does_not_exist.yml")
        res = inspect_settings(nonexistent)

        assert res["success"] is False
        assert "Settings file not found" in res["error"]
        assert res["settings_path"] == nonexistent

    def test_inspect_settings_valid_file(self, temp_settings_file):
        """Test inspect_settings with a valid settings.yml file."""
        res = inspect_settings(temp_settings_file)

        assert res["success"] is True
        assert res["settings_path"] == temp_settings_file
        assert res["use_default_settings"] is True
        assert res["general"]["instance_name"] == "SearXNG Test Engine"
        assert res["server"]["limiter"] is False
        assert res["search"]["formats"] == ["html", "json"]
        assert res["server"]["secret_key"] == "***REDACTED***"
        assert res["outgoing"]["request_timeout"] == 2.0

        summary = res["engine_summary"]
        assert summary["total_configured"] == 5
        assert summary["enabled_count"] == 2
        assert summary["disabled_count"] == 3
        assert "google cse" in summary["enabled_engines"]
        assert "bing" in summary["enabled_engines"]
        assert "duckduckgo" in summary["disabled_engines"]
        assert "startpage" in summary["disabled_engines"]
        assert "brave" in summary["disabled_engines"]
        assert len(res["raw_engines"]) == 5

    def test_inspect_settings_corrupted_yaml(self, tmp_path):
        """Test inspect_settings with invalid / corrupted YAML file."""
        corrupt_file = tmp_path / "corrupt.yml"
        corrupt_file.write_text("invalid_yaml: [unclosed bracket", encoding="utf-8")

        res = inspect_settings(str(corrupt_file))
        assert res["success"] is False
        assert "Failed to read/parse settings file" in res["error"]
        assert res["settings_path"] == str(corrupt_file)

    def test_inspect_settings_empty_file(self, tmp_path):
        """Test inspect_settings with an empty YAML file."""
        empty_file = tmp_path / "empty.yml"
        empty_file.write_text("", encoding="utf-8")

        res = inspect_settings(str(empty_file))
        assert res["success"] is True
        assert res["engine_summary"]["total_configured"] == 0
        assert res["engine_summary"]["enabled_count"] == 0
        assert res["engine_summary"]["disabled_count"] == 0
        assert res["raw_engines"] == []

    def test_inspect_settings_engines_with_missing_fields(self, tmp_path):
        """Test inspect_settings with engines missing name or disabled fields."""
        custom_file = tmp_path / "custom.yml"
        data = {
            "engines": [
                {"disabled": False},  # Missing 'name' -> defaults to 'unknown'
                {"name": "engine_default_enabled"},  # Missing 'disabled' -> defaults to enabled
            ]
        }
        with open(custom_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f)

        res = inspect_settings(str(custom_file))
        assert res["success"] is True
        assert res["engine_summary"]["total_configured"] == 2
        assert res["engine_summary"]["enabled_count"] == 2
        assert "unknown" in res["engine_summary"]["enabled_engines"]
        assert "engine_default_enabled" in res["engine_summary"]["enabled_engines"]

    def test_inspect_settings_default_path(self, monkeypatch, temp_settings_file):
        """Test inspect_settings falling back to DEFAULT_SETTINGS_PATH."""
        monkeypatch.setattr(
            "searxng_mcp_control.server.DEFAULT_SETTINGS_PATH", temp_settings_file
        )
        res = inspect_settings(None)
        assert res["success"] is True
        assert res["settings_path"] == temp_settings_file


class TestSetEngineStatus:
    """Unit tests for set_engine_status, enable_engine, and disable_engine."""

    def test_set_engine_status_nonexistent_file(self, tmp_path):
        """Test setting engine status when file does not exist."""
        nonexistent = str(tmp_path / "missing.yml")
        res = set_engine_status("duckduckgo", enabled=True, settings_path=nonexistent)
        assert res["success"] is False
        assert "Settings file not found" in res["error"]

    def test_set_engine_status_enable_existing_disabled_engine(self, temp_settings_file):
        """Test enabling an existing engine that was disabled."""
        res = set_engine_status("duckduckgo", enabled=True, settings_path=temp_settings_file)
        assert res["success"] is True
        assert res["enabled"] is True
        assert res["engine_name"] == "duckduckgo"
        assert "enabled" in res["message"]

        # Verify disk persistence
        insp = inspect_settings(temp_settings_file)
        assert "duckduckgo" in insp["engine_summary"]["enabled_engines"]
        assert "duckduckgo" not in insp["engine_summary"]["disabled_engines"]

    def test_set_engine_status_disable_existing_enabled_engine(self, temp_settings_file):
        """Test disabling an existing engine that was enabled (case-insensitive)."""
        # Test case-insensitivity: 'Google CSE' matching 'google cse'
        res = set_engine_status("Google CSE", enabled=False, settings_path=temp_settings_file)
        assert res["success"] is True
        assert res["enabled"] is False

        # Verify disk persistence
        insp = inspect_settings(temp_settings_file)
        assert "google cse" in insp["engine_summary"]["disabled_engines"]
        assert "google cse" not in insp["engine_summary"]["enabled_engines"]

    def test_set_engine_status_add_new_engine(self, temp_settings_file):
        """Test setting status for a previously unconfigured engine."""
        res = set_engine_status("searxng_new_engine", enabled=True, settings_path=temp_settings_file)
        assert res["success"] is True

        insp = inspect_settings(temp_settings_file)
        assert insp["engine_summary"]["total_configured"] == 6
        assert "searxng_new_engine" in insp["engine_summary"]["enabled_engines"]

    def test_set_engine_status_write_error(self, temp_settings_file, monkeypatch):
        """Test error handling when writing to file fails."""
        def mock_open_failure(*args, **kwargs):
            if "w" in args or kwargs.get("mode") == "w":
                raise IOError("Permission denied writing to file")
            return open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open_failure):
            res = set_engine_status("duckduckgo", enabled=True, settings_path=temp_settings_file)
            assert res["success"] is False
            assert "Failed to update settings file" in res["error"]

    def test_enable_engine_wrapper(self, temp_settings_file):
        """Test enable_engine wrapper tool."""
        res = enable_engine("startpage", settings_path=temp_settings_file)
        assert res["success"] is True
        assert res["enabled"] is True

        insp = inspect_settings(temp_settings_file)
        assert "startpage" in insp["engine_summary"]["enabled_engines"]

    def test_disable_engine_wrapper(self, temp_settings_file):
        """Test disable_engine wrapper tool."""
        res = disable_engine("bing", settings_path=temp_settings_file)
        assert res["success"] is True
        assert res["enabled"] is False

        insp = inspect_settings(temp_settings_file)
        assert "bing" in insp["engine_summary"]["disabled_engines"]


class TestSearchApiHealth:
    """Unit tests for test_search_api_health."""

    def test_health_check_success_200(self):
        """Test successful health check with 200 OK response and JSON results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"title": "Result 1: Python Testing Guide", "url": "https://example.com/1"},
                {"title": "Result 2: MCP Protocol Docs", "url": "https://example.com/2"},
                {"title": "Result 3: SearXNG Configuration", "url": "https://example.com/3"},
                {"title": "Result 4: Extra Title", "url": "https://example.com/4"},
            ]
        }

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client):
            res = api_test_search_health(url="http://localhost:8081", query="pytest")

            assert res["healthy"] is True
            assert res["status_code"] == 200
            assert res["query"] == "pytest"
            assert res["search_url"] == "http://localhost:8081/search"
            assert res["result_count"] == 4
            # Should contain at most 3 sample titles
            assert len(res["sample_titles"]) == 3
            assert res["sample_titles"][0] == "Result 1: Python Testing Guide"
            assert "latency_ms" in res
            assert isinstance(res["latency_ms"], float)

    def test_health_check_url_formatting(self):
        """Test URL formatting handles trailing slashes and /search suffix properly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client):
            # Case 1: URL already contains /search
            res1 = api_test_search_health(url="http://searxng.local/search")
            assert res1["search_url"] == "http://searxng.local/search"

            # Case 2: URL with trailing slash
            res2 = api_test_search_health(url="http://searxng.local/")
            assert res2["search_url"] == "http://searxng.local/search"

            # Case 3: URL without trailing slash or /search
            res3 = api_test_search_health(url="http://searxng.local:8080")
            assert res3["search_url"] == "http://searxng.local:8080/search"

    def test_health_check_http_error_status(self):
        """Test health check when server returns non-200 status code."""
        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client):
            res = api_test_search_health(url="http://localhost:8081")

            assert res["healthy"] is False
            assert res["status_code"] == 503
            assert "HTTP request failed with status code 503" in res["error"]
            assert "latency_ms" in res

    def test_health_check_invalid_json_payload(self):
        """Test health check when status is 200 but body is not valid JSON."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client):
            res = api_test_search_health(url="http://localhost:8081")

            assert res["healthy"] is False
            assert res["status_code"] == 200
            assert "failed to parse JSON" in res["error"]

    def test_health_check_connection_failure(self):
        """Test health check when connection fails (e.g. server down)."""
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.side_effect = Exception("Connection refused to host")

        with patch("httpx.Client", return_value=mock_client):
            res = api_test_search_health(url="http://127.0.0.1:9999")

            assert res["healthy"] is False
            assert "Connection/Request failed" in res["error"]
            assert "Connection refused" in res["error"]
            assert "latency_ms" in res

    def test_health_check_default_url(self, monkeypatch):
        """Test health check uses DEFAULT_SEARXNG_URL when url is None."""
        monkeypatch.setattr(
            "searxng_mcp_control.server.DEFAULT_SEARXNG_URL", "http://default-host:8081"
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.get.return_value = mock_response

        with patch("httpx.Client", return_value=mock_client):
            res = api_test_search_health(url=None)
            assert res["search_url"] == "http://default-host:8081/search"


class TestRestartSearxngContainer:
    """Unit tests for restart_searxng_container."""

    def test_restart_container_success(self):
        """Test successful container restart with exit code 0."""
        mock_completed = subprocess.CompletedProcess(
            args=["docker", "restart", "searxng-app"],
            returncode=0,
            stdout="searxng-app\n",
            stderr="",
        )

        with patch("subprocess.run", return_value=mock_completed) as mock_run:
            res = restart_searxng_container("searxng-app")

            mock_run.assert_called_once_with(
                ["docker", "restart", "searxng-app"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert res["success"] is True
            assert res["container_name"] == "searxng-app"
            assert res["returncode"] == 0
            assert res["stdout"] == "searxng-app"
            assert "Successfully restarted" in res["message"]

    def test_restart_container_docker_failure(self):
        """Test container restart failure with non-zero returncode."""
        mock_completed = subprocess.CompletedProcess(
            args=["docker", "restart", "searxng-app"],
            returncode=1,
            stdout="",
            stderr="Error: No such container: searxng-app",
        )

        with patch("subprocess.run", return_value=mock_completed):
            res = restart_searxng_container("searxng-app")

            assert res["success"] is False
            assert res["returncode"] == 1
            assert "No such container" in res["stderr"]
            assert "Failed to restart" in res["message"]

    def test_restart_container_timeout(self):
        """Test container restart encountering subprocess timeout."""
        with patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd=["docker", "restart"], timeout=30),
        ):
            res = restart_searxng_container("searxng-app")

            assert res["success"] is False
            assert res["container_name"] == "searxng-app"
            assert "timed out after 30 seconds" in res["error"]

    def test_restart_container_subprocess_os_error(self):
        """Test container restart encountering OS/execution error (e.g. docker not found)."""
        with patch("subprocess.run", side_effect=FileNotFoundError("docker binary not found")):
            res = restart_searxng_container("searxng-app")

            assert res["success"] is False
            assert res["container_name"] == "searxng-app"
            assert "Subprocess error executing command" in res["error"]

    def test_restart_container_default_name(self, monkeypatch):
        """Test restart container using DEFAULT_CONTAINER_NAME."""
        monkeypatch.setattr(
            "searxng_mcp_control.server.DEFAULT_CONTAINER_NAME", "default-searx-container"
        )
        mock_completed = subprocess.CompletedProcess(
            args=["docker", "restart", "default-searx-container"],
            returncode=0,
            stdout="default-searx-container",
            stderr="",
        )

        with patch("subprocess.run", return_value=mock_completed) as mock_run:
            res = restart_searxng_container(None)
            mock_run.assert_called_once_with(
                ["docker", "restart", "default-searx-container"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert res["container_name"] == "default-searx-container"


class TestMainEntryPoint:
    """Unit test for server entrypoint."""

    def test_main_calls_mcp_run(self):
        """Verify main() invokes mcp.run()."""
        with patch("searxng_mcp_control.server.mcp.run") as mock_mcp_run:
            main()
            mock_mcp_run.assert_called_once()


class TestRealEnvironmentChecks:
    """Real checks using local environment paths/endpoints if present."""

    def test_real_searxng_settings_if_available(self):
        """Inspect the real settings.yml on the host if available."""
        real_path = "/home/ddoctorm/services/searxng/settings.yml"
        if os.path.exists(real_path):
            res = inspect_settings(real_path)
            assert res["success"] is True
            assert "engine_summary" in res
            assert res["engine_summary"]["total_configured"] > 0
            assert "enabled_engines" in res["engine_summary"]
            assert "disabled_engines" in res["engine_summary"]

    def test_real_searxng_live_health_if_running(self):
        """Check live SearXNG endpoint at http://localhost:8081 if container is up."""
        res = api_test_search_health(url="http://localhost:8081", query="searxng")
        # Ensure the test does not crash, and correctly returns status
        assert "healthy" in res
        assert "latency_ms" in res
        if res["healthy"]:
            assert res["status_code"] == 200
            assert isinstance(res["sample_titles"], list)
