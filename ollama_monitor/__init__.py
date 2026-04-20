"""Ollama Monitor — public package surface."""
from ollama_monitor.config import MonitorConfig
from ollama_monitor.thresholds import ThresholdConfig, DEFAULT_THRESHOLDS

__all__ = [
    "MonitorConfig",
    "ThresholdConfig",
    "DEFAULT_THRESHOLDS",
]
