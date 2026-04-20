"""Produce human-readable summary reports from a MetricsHistory."""
from __future__ import annotations

from io import StringIO
from typing import Optional

from ollama_monitor.history import MetricsHistory


def _fmt_duration(seconds: float) -> str:
    """Format a duration in seconds to a short human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.3f} s"


def summary_report(history: MetricsHistory, title: Optional[str] = None) -> str:
    """Return a plain-text summary of *history*.

    The report includes:
    - Total snapshots stored
    - Reachability percentage
    - Min / mean / max response time (reachable entries only)
    """
    entries = history.all()
    buf = StringIO()

    header = title or "Ollama Monitor — History Summary"
    buf.write(f"{header}\n")
    buf.write("=" * len(header) + "\n")

    if not entries:
        buf.write("No data recorded yet.\n")
        return buf.getvalue()

    total = len(entries)
    ratio = history.reachable_ratio()
    buf.write(f"Snapshots  : {total}\n")
    buf.write(f"Reachable  : {ratio * 100:.1f}%\n")

    response_times = [
        e.metrics.response_time
        for e in entries
        if e.metrics.reachable and e.metrics.response_time is not None
    ]

    if response_times:
        mn = min(response_times)
        mx = max(response_times)
        mean = sum(response_times) / len(response_times)
        buf.write(f"Response   : min={_fmt_duration(mn)}"
                  f"  mean={_fmt_duration(mean)}"
                  f"  max={_fmt_duration(mx)}\n")
    else:
        buf.write("Response   : n/a (no reachable snapshots)\n")

    first_ts = entries[0].timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    last_ts = entries[-1].timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    buf.write(f"Period     : {first_ts}  →  {last_ts}\n")

    return buf.getvalue()
