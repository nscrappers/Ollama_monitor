"""Unit tests for ollama_monitor.history."""
from __future__ import annotations

from unittest.mock import patch
from datetime import datetime, timezone

import pytest

from ollama_monitor.history import MetricsHistory
from ollama_monitor.metrics import OllamaMetrics


def _reachable(response_time: float = 0.1) -> OllamaMetrics:
    return OllamaMetrics(reachable=True, response_time=response_time)


def _unreachable() -> OllamaMetrics:
    return OllamaMetrics(reachable=False, response_time=None)


class TestMetricsHistoryRecord:
    def test_empty_on_init(self):
        h = MetricsHistory()
        assert h.all() == []

    def test_record_adds_entry(self):
        h = MetricsHistory()
        h.record(_reachable())
        assert len(h.all()) == 1

    def test_entry_has_utc_timestamp(self):
        h = MetricsHistory()
        h.record(_reachable())
        entry = h.all()[0]
        assert entry.timestamp.tzinfo is not None

    def test_rolling_window_drops_oldest(self):
        h = MetricsHistory(maxlen=3)
        for i in range(5):
            h.record(_reachable(float(i)))
        entries = h.all()
        assert len(entries) == 3
        assert entries[0].metrics.response_time == 2.0

    def test_clear_removes_all(self):
        h = MetricsHistory()
        h.record(_reachable())
        h.clear()
        assert h.all() == []


class TestMetricsHistoryLatest:
    def test_latest_returns_n_most_recent(self):
        h = MetricsHistory()
        for i in range(5):
            h.record(_reachable(float(i)))
        result = h.latest(2)
        assert len(result) == 2
        assert result[-1].metrics.response_time == 4.0

    def test_latest_clamps_to_available(self):
        h = MetricsHistory()
        h.record(_reachable())
        result = h.latest(10)
        assert len(result) == 1

    def test_latest_default_one(self):
        h = MetricsHistory()
        h.record(_reachable(0.5))
        h.record(_reachable(0.9))
        result = h.latest()
        assert len(result) == 1
        assert result[0].metrics.response_time == 0.9


class TestReachableRatio:
    def test_empty_history_returns_zero(self):
        h = MetricsHistory()
        assert h.reachable_ratio() == 0.0

    def test_all_reachable(self):
        h = MetricsHistory()
        for _ in range(4):
            h.record(_reachable())
        assert h.reachable_ratio() == 1.0

    def test_mixed_reachability(self):
        h = MetricsHistory()
        h.record(_reachable())
        h.record(_reachable())
        h.record(_unreachable())
        h.record(_unreachable())
        assert h.reachable_ratio() == pytest.approx(0.5)
