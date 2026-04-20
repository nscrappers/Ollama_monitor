"""Tests for ollama_monitor.alerts module."""

import pytest

from ollama_monitor.alerts import (
    AlertManager,
    HighResponseTimeAlert,
    UnreachableAlert,
)
from ollama_monitor.metrics import OllamaMetrics


def _reachable(response_time: float = 0.5) -> OllamaMetrics:
    return OllamaMetrics(reachable=True, response_time_seconds=response_time)


def _unreachable() -> OllamaMetrics:
    return OllamaMetrics(reachable=False, response_time_seconds=None)


class TestUnreachableAlert:
    def test_triggers_when_unreachable(self):
        alert = UnreachableAlert()
        assert alert.evaluate(_unreachable()) is True
        assert alert.triggered is True

    def test_does_not_trigger_when_reachable(self):
        alert = UnreachableAlert()
        assert alert.evaluate(_reachable()) is False
        assert alert.triggered is False


class TestHighResponseTimeAlert:
    def test_triggers_above_threshold(self):
        alert = HighResponseTimeAlert(threshold_seconds=1.0)
        assert alert.evaluate(_reachable(response_time=1.5)) is True

    def test_does_not_trigger_below_threshold(self):
        alert = HighResponseTimeAlert(threshold_seconds=1.0)
        assert alert.evaluate(_reachable(response_time=0.5)) is False

    def test_does_not_trigger_when_response_time_is_none(self):
        alert = HighResponseTimeAlert(threshold_seconds=1.0)
        assert alert.evaluate(_unreachable()) is False

    def test_message_contains_threshold(self):
        alert = HighResponseTimeAlert(threshold_seconds=3.0)
        assert "3.0" in alert.message


class TestAlertManager:
    def test_returns_triggered_alerts_for_unreachable(self):
        manager = AlertManager()
        triggered = manager.evaluate(_unreachable())
        names = [r.name for r in triggered]
        assert "ollama_unreachable" in names

    def test_no_alerts_for_healthy_metrics(self):
        manager = AlertManager()
        triggered = manager.evaluate(_reachable(response_time=0.1))
        assert triggered == []

    def test_triggered_names_convenience_method(self):
        manager = AlertManager()
        names = manager.triggered_names(_unreachable())
        assert "ollama_unreachable" in names

    def test_custom_rules_respected(self):
        custom_rule = HighResponseTimeAlert(threshold_seconds=0.1)
        manager = AlertManager(rules=[custom_rule])
        triggered = manager.evaluate(_reachable(response_time=0.5))
        assert len(triggered) == 1
        assert triggered[0].name == "high_response_time"
