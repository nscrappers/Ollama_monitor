"""Tests for ollama_monitor.notifier."""

from __future__ import annotations

from typing import List, Tuple
from unittest.mock import MagicMock

import pytest

from ollama_monitor.alerts import UnreachableAlert, HighResponseTimeAlert
from ollama_monitor.metrics import OllamaMetrics
from ollama_monitor.notifier import Notifier, log_notify


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reachable(response_time: float = 0.1) -> OllamaMetrics:
    return OllamaMetrics(reachable=True, response_time_seconds=response_time)


def _unreachable() -> OllamaMetrics:
    return OllamaMetrics(reachable=False, response_time_seconds=None)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestNotifier:
    def test_no_rules_returns_empty(self):
        notifier = Notifier(rules=[])
        fired = notifier.check(_reachable())
        assert fired == []

    def test_fired_alerts_returned(self):
        notifier = Notifier(rules=[UnreachableAlert()], notify_fn=lambda n, m: None)
        fired = notifier.check(_unreachable())
        assert "UnreachableAlert" in fired

    def test_non_triggered_rule_not_returned(self):
        notifier = Notifier(rules=[UnreachableAlert()], notify_fn=lambda n, m: None)
        fired = notifier.check(_reachable())
        assert fired == []

    def test_notify_fn_called_with_name_and_message(self):
        callback = MagicMock()
        notifier = Notifier(rules=[UnreachableAlert()], notify_fn=callback)
        notifier.check(_unreachable())
        callback.assert_called_once()
        name, message = callback.call_args[0]
        assert name == "UnreachableAlert"
        assert isinstance(message, str) and len(message) > 0

    def test_multiple_rules_all_evaluated(self):
        callback = MagicMock()
        rules = [UnreachableAlert(), HighResponseTimeAlert(threshold_seconds=0.01)]
        notifier = Notifier(rules=rules, notify_fn=callback)
        # reachable but slow — only HighResponseTimeAlert should fire
        fired = notifier.check(_reachable(response_time=5.0))
        assert "HighResponseTimeAlert" in fired
        assert "UnreachableAlert" not in fired

    def test_faulty_notify_fn_does_not_propagate(self):
        def bad_fn(name, message):
            raise RuntimeError("boom")

        notifier = Notifier(rules=[UnreachableAlert()], notify_fn=bad_fn)
        # Should not raise
        fired = notifier.check(_unreachable())
        assert "UnreachableAlert" in fired


class TestLogNotify:
    def test_log_notify_runs_without_error(self, caplog):
        import logging
        with caplog.at_level(logging.WARNING, logger="ollama_monitor.notifier"):
            log_notify("SomeAlert", "Something went wrong")
        assert "SomeAlert" in caplog.text
        assert "Something went wrong" in caplog.text
