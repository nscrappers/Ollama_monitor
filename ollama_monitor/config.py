"""Load and persist monitor configuration from a TOML/dict source."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ollama_monitor.thresholds import ThresholdConfig


_DEFAULTS: Dict[str, Any] = {
    "ollama_url": "http://localhost:11434",
    "poll_interval_s": 15.0,
    "thresholds": {},
}


class MonitorConfig:
    """Runtime configuration for Ollama Monitor."""

    def __init__(
        self,
        ollama_url: str = _DEFAULTS["ollama_url"],
        poll_interval_s: float = _DEFAULTS["poll_interval_s"],
        thresholds: Optional[ThresholdConfig] = None,
    ) -> None:
        self.ollama_url = ollama_url
        self.poll_interval_s = poll_interval_s
        self.thresholds: ThresholdConfig = thresholds or ThresholdConfig()

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ollama_url": self.ollama_url,
            "poll_interval_s": self.poll_interval_s,
            "thresholds": {
                "max_response_time_s": self.thresholds.max_response_time_s,
                "unreachable_streak": self.thresholds.unreachable_streak,
                "min_success_rate": self.thresholds.min_success_rate,
                "window": self.thresholds.window,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MonitorConfig":
        t_data = data.get("thresholds", {})
        thresholds = ThresholdConfig(**t_data) if t_data else ThresholdConfig()
        return cls(
            ollama_url=data.get("ollama_url", _DEFAULTS["ollama_url"]),
            poll_interval_s=float(
                data.get("poll_interval_s", _DEFAULTS["poll_interval_s"])
            ),
            thresholds=thresholds,
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "MonitorConfig":
        with path.open() as fh:
            return cls.from_dict(json.load(fh))

    def save_json(self, path: Path) -> None:
        path.write_text(json.dumps(self.to_dict(), indent=2))
