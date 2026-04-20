"""Unit tests for ollama_monitor.reporter."""
from __future__ import annotations

from ollama_monitor.history import MetricsHistory
from ollama_monitor.metrics import OllamaMetrics
from ollama_monitor.reporter import summary_report, _fmt_duration


def _reachable(rt: float = 0.2) -> OllamaMetrics:
    return OllamaMetrics(reachable=True, response_time=rt)


def _unreachable() -> OllamaMetrics:
    return OllamaMetrics(reachable=False, response_time=None)


class TestFmtDuration:
    def test_sub_second(self):
        assert _fmt_duration(0.05) == "50.0 ms"

    def test_one_second_or_more(self):
        assert _fmt_duration(1.5) == "1.500 s"


class TestSummaryReport:
    def test_empty_history(self):
        h = MetricsHistory()
        report = summary_report(h)
        assert "No data recorded yet" in report

    def test_custom_title_appears(self):
        h = MetricsHistory()
        report = summary_report(h, title="My Custom Title")
        assert "My Custom Title" in report

    def test_snapshot_count(self):
        h = MetricsHistory()
        for _ in range(5):
            h.record(_reachable())
        report = summary_report(h)
        assert "Snapshots  : 5" in report

    def test_reachability_percentage_all_up(self):
        h = MetricsHistory()
        for _ in range(4):
            h.record(_reachable())
        report = summary_report(h)
        assert "100.0%" in report

    def test_reachability_percentage_mixed(self):
        h = MetricsHistory()
        h.record(_reachable())
        h.record(_unreachable())
        report = summary_report(h)
        assert "50.0%" in report

    def test_response_time_stats_present(self):
        h = MetricsHistory()
        h.record(_reachable(0.1))
        h.record(_reachable(0.3))
        report = summary_report(h)
        assert "min=" in report
        assert "mean=" in report
        assert "max=" in report

    def test_no_reachable_entries_shows_na(self):
        h = MetricsHistory()
        h.record(_unreachable())
        report = summary_report(h)
        assert "n/a" in report

    def test_period_line_present(self):
        h = MetricsHistory()
        h.record(_reachable())
        report = summary_report(h)
        assert "Period     :" in report
        assert "UTC" in report
