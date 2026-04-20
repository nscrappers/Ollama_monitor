"""In-memory metrics history with a configurable rolling window."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, List

from ollama_monitor.metrics import OllamaMetrics


@dataclass
class HistoryEntry:
    """A single timestamped snapshot of metrics."""

    timestamp: datetime
    metrics: OllamaMetrics


@dataclass
class MetricsHistory:
    """Stores the last *maxlen* metric snapshots.

    Parameters
    ----------
    maxlen:
        Maximum number of entries to keep.  Older entries are dropped
        automatically once the buffer is full.
    """

    maxlen: int = 100
    _entries: Deque[HistoryEntry] = field(default_factory=deque, init=False, repr=False)

    def __post_init__(self) -> None:
        self._entries = deque(maxlen=self.maxlen)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def record(self, metrics: OllamaMetrics) -> None:
        """Append *metrics* with the current UTC timestamp."""
        entry = HistoryEntry(
            timestamp=datetime.now(tz=timezone.utc),
            metrics=metrics,
        )
        self._entries.append(entry)

    def clear(self) -> None:
        """Remove all stored entries."""
        self._entries.clear()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def all(self) -> List[HistoryEntry]:
        """Return all entries ordered oldest-first."""
        return list(self._entries)

    def latest(self, n: int = 1) -> List[HistoryEntry]:
        """Return the *n* most-recent entries (newest last)."""
        entries = list(self._entries)
        return entries[-n:] if n <= len(entries) else entries

    def reachable_ratio(self) -> float:
        """Fraction of stored entries where the host was reachable.

        Returns 0.0 when the history is empty.
        """
        entries = list(self._entries)
        if not entries:
            return 0.0
        reachable = sum(1 for e in entries if e.metrics.reachable)
        return reachable / len(entries)

    def __len__(self) -> int:  # pragma: no cover
        return len(self._entries)
