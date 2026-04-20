"""High-level monitoring loop that wires collector, alerts and notifier."""

from __future__ import annotations

import logging
import time
from typing import List, Optional

from ollama_monitor.alerts import AlertRule, UnreachableAlert, HighResponseTimeAlert
from ollama_monitor.collector import MetricsCollector
from ollama_monitor.notifier import Notifier, log_notify, NotifyFn

logger = logging.getLogger(__name__)

_DEFAULT_RULES: List[AlertRule] = [
    UnreachableAlert(),
    HighResponseTimeAlert(threshold_seconds=2.0),
]


class MonitorRunner:
    """Orchestrates periodic metric collection and alert evaluation.

    Parameters
    ----------
    collector:
        A :class:`~ollama_monitor.collector.MetricsCollector` instance.
    interval_seconds:
        How often (in seconds) to poll and evaluate alerts.
    rules:
        Alert rules to evaluate.  Defaults to :data:`_DEFAULT_RULES`.
    notify_fn:
        Notification callback forwarded to :class:`~ollama_monitor.notifier.Notifier`.
    """

    def __init__(
        self,
        collector: MetricsCollector,
        interval_seconds: float = 30.0,
        rules: Optional[List[AlertRule]] = None,
        notify_fn: NotifyFn = log_notify,
    ) -> None:
        self.collector = collector
        self.interval_seconds = interval_seconds
        self.notifier = Notifier(
            rules=rules if rules is not None else list(_DEFAULT_RULES),
            notify_fn=notify_fn,
        )
        self._running = False

    def run_once(self) -> List[str]:
        """Collect the latest metrics snapshot and evaluate all alert rules.

        Returns the list of alert names that fired.
        """
        metrics = self.collector.latest
        if metrics is None:
            logger.debug("No metrics snapshot available yet; skipping alert evaluation.")
            return []
        return self.notifier.check(metrics)

    def run(self) -> None:  # pragma: no cover
        """Block and run the monitoring loop until interrupted."""
        logger.info(
            "MonitorRunner starting — poll interval %.1fs", self.interval_seconds
        )
        self._running = True
        try:
            while self._running:
                self.run_once()
                time.sleep(self.interval_seconds)
        except KeyboardInterrupt:
            logger.info("MonitorRunner stopped by user.")
        finally:
            self._running = False

    def stop(self) -> None:  # pragma: no cover
        """Signal the run loop to exit after the current iteration."""
        self._running = False
