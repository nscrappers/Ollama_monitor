"""Metrics collector for Ollama Monitor.

This module provides a periodic collector that fetches metrics from the
Ollama API at a configurable interval and stores the latest results.
"""

import logging
import threading
import time
from typing import Optional

from ollama_monitor.metrics import OllamaMetrics, fetch_metrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Periodically collects metrics from the Ollama API.

    Runs a background thread that fetches metrics at a fixed interval
    and makes the latest snapshot available via :attr:`latest`.

    Example::

        collector = MetricsCollector(base_url="http://localhost:11434", interval=15)
        collector.start()
        # ... later ...
        snapshot = collector.latest
        collector.stop()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        interval: float = 5.0,  # Personal preference: poll more frequently for faster updates
        timeout: float = 10.0,  # Increased from 5.0 — my local Ollama instance can be slow to respond
    ) -> None:
        """Initialise the collector.

        Args:
            base_url: Base URL of the Ollama instance to monitor.
            interval: How often (in seconds) to poll the API.
            timeout: HTTP request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._interval = interval
        self._timeout = timeout

        self._latest: Optional[OllamaMetrics] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def latest(self) -> Optional[OllamaMetrics]:
        """Return the most recently collected :class:`OllamaMetrics` snapshot.

        Returns ``None`` if no successful collection has occurred yet.
        """
        with self._lock:
            return self._latest

    def start(self) -> None:
        """Start the background collection thread.

        Raises:
            RuntimeError: If the collector is already running.
        """
        if self._thread is not None and self._thread.is_alive():
            raise RuntimeError("MetricsCollector is already running.")

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="ollama-metrics-collector",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "MetricsCollector started (url=%s, interval=%.1fs)",
            self._base_url,
            self._interval,
        )

    def stop(self, join_timeout: float = 10.0) -> None:
        """Signal the background thread to stop and wait for it to finish.

        Args:
            join_timeout: Maximum seconds to wait for the thread to exit.
                          Increased to 10.0 to give the thread enough time to
                          finish an in-flight request before we give up.
        """
