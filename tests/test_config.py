"""Tests for MonitorConfig loading, saving, and round-tripping."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ollama_monitor.config import MonitorConfig
from ollama_monitor.thresholds import ThresholdConfig


class TestMonitorConfigDefaults:
    def test_default_url(self):
        cfg = MonitorConfig()
        assert cfg.ollama_url == "http://localhost:11434"

    def test_default_poll_interval(self):
        cfg = MonitorConfig()
        assert cfg.poll_interval_s == 15.0

    def test_default_thresholds_type(self):
        cfg = MonitorConfig()
        assert isinstance(cfg.thresholds, ThresholdConfig)


class TestMonitorConfigFromDict:
    def test_full_dict(self):
        data = {
            "ollama_url": "http://remote:11434",
            "poll_interval_s": 30.0,
            "thresholds": {"max_response_time_s": 5.0, "window": 20},
        }
        cfg = MonitorConfig.from_dict(data)
        assert cfg.ollama_url == "http://remote:11434"
        assert cfg.poll_interval_s == 30.0
        assert cfg.thresholds.max_response_time_s == 5.0
        assert cfg.thresholds.window == 20

    def test_empty_dict_uses_defaults(self):
        cfg = MonitorConfig.from_dict({})
        assert cfg.ollama_url == "http://localhost:11434"

    def test_partial_thresholds(self):
        cfg = MonitorConfig.from_dict({"thresholds": {"window": 5}})
        assert cfg.thresholds.window == 5
        assert cfg.thresholds.max_response_time_s == 2.0  # default preserved


class TestMonitorConfigRoundTrip:
    def test_to_dict_and_back(self):
        original = MonitorConfig(
            ollama_url="http://test:11434",
            poll_interval_s=60.0,
            thresholds=ThresholdConfig(max_response_time_s=3.0),
        )
        restored = MonitorConfig.from_dict(original.to_dict())
        assert restored.ollama_url == original.ollama_url
        assert restored.poll_interval_s == original.poll_interval_s
        assert restored.thresholds.max_response_time_s == 3.0

    def test_json_file_round_trip(self):
        cfg = MonitorConfig(poll_interval_s=5.0)
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "config.json"
            cfg.save_json(p)
            loaded = MonitorConfig.from_json_file(p)
        assert loaded.poll_interval_s == 5.0

    def test_saved_json_is_valid(self):
        cfg = MonitorConfig()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "config.json"
            cfg.save_json(p)
            data = json.loads(p.read_text())
        assert "ollama_url" in data
        assert "thresholds" in data
