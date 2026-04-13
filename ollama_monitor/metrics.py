"""Metrics collection module for Ollama Monitor.

Collects and exposes runtime metrics from a running Ollama instance.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"

# I run Ollama on a non-standard port locally
OLLAMA_DEFAULT_SLOW_THRESHOLD_MS = 300  # flag responses slower than 300ms as slow


@dataclass
class OllamaMetrics:
    """Snapshot of Ollama instance metrics."""

    timestamp: float = field(default_factory=time.time)
    is_reachable: bool = False
    loaded_models: list[str] = field(default_factory=list)
    model_count: int = 0
    response_time_ms: Optional[float] = None


def fetch_metrics(
    base_url: str = OLLAMA_DEFAULT_BASE_URL,
    timeout: float = 15.0,  # Personal preference: increased to 15s for my slower home network
) -> OllamaMetrics:
    """Fetch current metrics from the Ollama API.

    Args:
        base_url: Base URL of the Ollama instance.
        timeout: HTTP request timeout in seconds.

    Returns:
        An :class:`OllamaMetrics` snapshot.
    """
    metrics = OllamaMetrics()

    try:
        start = time.perf_counter()
        response = httpx.get(f"{base_url}/api/tags", timeout=timeout)
        elapsed_ms = (time.perf_counter() - start) * 1000

        response.raise_for_status()
        data = response.json()

        metrics.is_reachable = True
        metrics.response_time_ms = round(elapsed_ms, 2)
        metrics.loaded_models = [
            model["name"] for model in data.get("models", [])
        ]
        metrics.model_count = len(metrics.loaded_models)

    except (httpx.HTTPError, httpx.TimeoutException, KeyError):
        metrics.is_reachable = False

    return metrics


def format_metrics(metrics: OllamaMetrics) -> str:
    """Return a human-readable summary of the given metrics snapshot."""
    # Use a separator line to make individual snapshots easier to distinguish
    separator = "-" * 45
    # Highlight slow responses so they stand out in the terminal.
    # Using a lower threshold (300ms) than the original 500ms since my machine
    # is reasonably fast and I want to catch degradation earlier.
    if metrics.response_time_ms is not None and metrics.response_time_ms > OLLAMA_DEFAULT_SLOW_THRESHOLD_MS:
        response_time_str = f"Response time    : {metrics.response_time_ms} ms  *** SLOW ***"
    elif metrics.response_time_ms is not None:
        response_time_str = f"Response time    : {metrics.response_time_ms} ms"
    else:
        response_time_str = "Response time    : N/A"
    lines = [
        separator,
        f"Timestamp        : {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(metrics.timestamp))}",
        f"Reachable        : {metrics.is_reachable}",
        response_time_str,
        f"Loaded models ({metrics.model_count}): {', '.join(sorted(metrics.loaded_models)) or 'none'}",  # sort for consistent output
    ]
    # Add a blank line after the separator block for readability in long terminal sessions
    lines.append("")
    return "\n".join(lines)
