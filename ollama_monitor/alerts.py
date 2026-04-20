"""Alert rules and notification logic for Ollama monitor."""

from dataclasses import dataclass, field
from typing import List, Optional

from ollama_monitor.metrics import OllamaMetrics


@dataclass
class AlertRule:
    """A single alert rule with a name, condition, and optional message."""

    name: str
    message: str
    triggered: bool = field(default=False, init=False)

    def evaluate(self, metrics: OllamaMetrics) -> bool:
        raise NotImplementedError


@dataclass
class UnreachableAlert(AlertRule):
    """Fires when the Ollama endpoint is not reachable."""

    name: str = "ollama_unreachable"
    message: str = "Ollama endpoint is unreachable"

    def evaluate(self, metrics: OllamaMetrics) -> bool:
        self.triggered = not metrics.reachable
        return self.triggered


@dataclass
class HighResponseTimeAlert(AlertRule):
    """Fires when response time exceeds the configured threshold (seconds)."""

    threshold_seconds: float = 2.0
    name: str = "high_response_time"
    message: str = ""

    def __post_init__(self) -> None:
        self.message = (
            f"Response time exceeded {self.threshold_seconds}s threshold"
        )

    def evaluate(self, metrics: OllamaMetrics) -> bool:
        if metrics.response_time_seconds is None:
            self.triggered = False
        else:
            self.triggered = metrics.response_time_seconds > self.threshold_seconds
        return self.triggered


class AlertManager:
    """Evaluates a collection of alert rules against the latest metrics."""

    def __init__(self, rules: Optional[List[AlertRule]] = None) -> None:
        self.rules: List[AlertRule] = rules if rules is not None else [
            UnreachableAlert(),
            HighResponseTimeAlert(),
        ]

    def evaluate(self, metrics: OllamaMetrics) -> List[AlertRule]:
        """Evaluate all rules and return those that are triggered."""
        triggered = []
        for rule in self.rules:
            if rule.evaluate(metrics):
                triggered.append(rule)
        return triggered

    def triggered_names(self, metrics: OllamaMetrics) -> List[str]:
        """Return names of all triggered alert rules."""
        return [rule.name for rule in self.evaluate(metrics)]
