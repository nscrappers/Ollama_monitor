"""Notification dispatching for triggered alerts."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, List

from ollama_monitor.alerts import AlertRule
from ollama_monitor.metrics import OllamaMetrics

logger = logging.getLogger(__name__)


NotifyFn = Callable[[str, str], None]


def log_notify(alert_name: str, message: str) -> None:
    """Default notifier: writes triggered alerts to the logger."""
    logger.warning("[ALERT] %s: %s", alert_name, message)


@dataclass
class Notifier:
    """Evaluates a collection of alert rules against fresh metrics
    and dispatches notifications for any that fire.

    Parameters
    ----------
    rules:
        Alert rules to evaluate on each call to :meth:`check`.
    notify_fn:
        Callable invoked with ``(alert_name, message)`` whenever a rule
        triggers.  Defaults to :func:`log_notify`.
    """

    rules: List[AlertRule] = field(default_factory=list)
    notify_fn: NotifyFn = field(default=log_notify)

    def check(self, metrics: OllamaMetrics) -> List[str]:
        """Evaluate all rules against *metrics*.

        Returns a list of alert names that fired during this check.
        """
        fired: List[str] = []
        for rule in self.rules:
            triggered, message = rule.evaluate(metrics)
            if triggered:
                name = type(rule).__name__
                fired.append(name)
                try:
                    self.notify_fn(name, message)
                except Exception:  # noqa: BLE001
                    logger.exception("Notifier callback raised an exception for rule %s", name)
        return fired
