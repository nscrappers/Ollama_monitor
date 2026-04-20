"""Configurable threshold definitions for alert rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ThresholdConfig:
    """Holds numeric thresholds used by alert rules."""

    # Maximum acceptable response time in seconds before alerting.
    max_response_time_s: float = 2.0

    # Number of consecutive unreachable checks before alerting.
    unreachable_streak: int = 1

    # Minimum success-rate (0.0–1.0) over the rolling window.
    min_success_rate: float = 0.8

    # Rolling window size (number of recent records) for rate calculations.
    window: int = 10

    def validate(self) -> None:
        """Raise ValueError if any threshold is out of a sensible range."""
        if self.max_response_time_s <= 0:
            raise ValueError("max_response_time_s must be positive")
        if self.unreachable_streak < 1:
            raise ValueError("unreachable_streak must be >= 1")
        if not (0.0 <= self.min_success_rate <= 1.0):
            raise ValueError("min_success_rate must be between 0.0 and 1.0")
        if self.window < 1:
            raise ValueError("window must be >= 1")


DEFAULT_THRESHOLDS: ThresholdConfig = ThresholdConfig()
