"""Tests for ThresholdConfig validation."""
from __future__ import annotations

import pytest

from ollama_monitor.thresholds import ThresholdConfig


class TestThresholdConfigDefaults:
    def test_default_values(self):
        cfg = ThresholdConfig()
        assert cfg.max_response_time_s == 2.0
        assert cfg.unreachable_streak == 1
        assert cfg.min_success_rate == 0.8
        assert cfg.window == 10

    def test_custom_values(self):
        cfg = ThresholdConfig(
            max_response_time_s=5.0,
            unreachable_streak=3,
            min_success_rate=0.9,
            window=20,
        )
        assert cfg.max_response_time_s == 5.0
        assert cfg.unreachable_streak == 3


class TestThresholdConfigValidation:
    def test_valid_config_passes(self):
        ThresholdConfig().validate()  # should not raise

    def test_negative_response_time_raises(self):
        with pytest.raises(ValueError, match="max_response_time_s"):
            ThresholdConfig(max_response_time_s=-1.0).validate()

    def test_zero_response_time_raises(self):
        with pytest.raises(ValueError):
            ThresholdConfig(max_response_time_s=0.0).validate()

    def test_zero_streak_raises(self):
        with pytest.raises(ValueError, match="unreachable_streak"):
            ThresholdConfig(unreachable_streak=0).validate()

    def test_success_rate_above_one_raises(self):
        with pytest.raises(ValueError, match="min_success_rate"):
            ThresholdConfig(min_success_rate=1.1).validate()

    def test_negative_success_rate_raises(self):
        with pytest.raises(ValueError, match="min_success_rate"):
            ThresholdConfig(min_success_rate=-0.1).validate()

    def test_zero_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            ThresholdConfig(window=0).validate()
