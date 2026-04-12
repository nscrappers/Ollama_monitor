"""Unit tests for ollama_monitor.metrics."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ollama_monitor.metrics import (
    OllamaMetrics,
    fetch_metrics,
    format_metrics,
)

_FAKE_TAGS_RESPONSE = {
    "models": [
        {"name": "llama3:latest"},
        {"name": "mistral:7b"},
    ]
}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    mock = MagicMock(spec=httpx.Response)
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


class TestFetchMetrics:
    def test_successful_fetch_returns_reachable_metrics(self):
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.return_value = _mock_response(_FAKE_TAGS_RESPONSE)
            metrics = fetch_metrics()

        assert metrics.is_reachable is True
        assert metrics.model_count == 2
        assert "llama3:latest" in metrics.loaded_models
        assert "mistral:7b" in metrics.loaded_models
        assert metrics.response_time_ms is not None
        assert metrics.response_time_ms >= 0

    def test_timeout_returns_unreachable_metrics(self):
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.side_effect = httpx.TimeoutException("timed out")
            metrics = fetch_metrics()

        assert metrics.is_reachable is False
        assert metrics.model_count == 0
        assert metrics.response_time_ms is None

    def test_http_error_returns_unreachable_metrics(self):
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.side_effect = httpx.HTTPError("connection refused")
            metrics = fetch_metrics()

        assert metrics.is_reachable is False

    def test_empty_model_list(self):
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.return_value = _mock_response({"models": []})
            metrics = fetch_metrics()

        assert metrics.is_reachable is True
        assert metrics.model_count == 0
        assert metrics.loaded_models == []

    def test_custom_base_url_is_used(self):
        custom_url = "http://remote-host:11434"
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.return_value = _mock_response(_FAKE_TAGS_RESPONSE)
            fetch_metrics(base_url=custom_url)

        mock_get.assert_called_once_with(f"{custom_url}/api/tags", timeout=5.0)

    # I run Ollama locally with a longer startup time, so testing a higher
    # timeout value is useful for my setup.
    def test_custom_timeout_is_used(self):
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.return_value = _mock_response(_FAKE_TAGS_RESPONSE)
            fetch_metrics(timeout=15.0)

        mock_get.assert_called_once_with(
            "http://localhost:11434/api/tags", timeout=15.0
        )

    # Useful for my workflow: I sometimes run a second Ollama instance on
    # port 11435 for testing experimental models without affecting the main one.
    def test_alternate_port_base_url(self):
        alt_url = "http://localhost:11435"
        with patch("ollama_monitor.metrics.httpx.get") as mock_get:
            mock_get.return_value = _mock_response(_FAKE_TAGS_RESPONSE)
            fetch_metrics(base_url=alt_url)

        mock_get.assert_called_once_with(f"{alt_url}/api/tags", timeout=5.0)
