"""
Evaluation Metrics — comprehensive system-level benchmarking.

Tracks accuracy, latency, cost, and ROI across all agents and heads.

I/O:
  INPUT:  Agent outputs + ground truth outcomes
  OUTPUT: Metric reports, leaderboards, degradation alerts
"""

from __future__ import annotations

import time
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("hydranet.pipeline.evaluation")


@dataclass
class MetricSnapshot:
    """Point-in-time measurement."""
    name: str
    value: float
    unit: str
    timestamp: float = field(default_factory=time.time)
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects, aggregates, and reports system metrics."""

    def __init__(self):
        self._metrics: dict[str, list[MetricSnapshot]] = {}
        self._alerts: list[dict] = []

    def record(self, name: str, value: float, unit: str = "", tags: dict | None = None):
        """Record a metric data point."""
        snapshot = MetricSnapshot(name=name, value=value, unit=unit, tags=tags or {})
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(snapshot)

        # Keep last 1000 per metric
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-1000:]

    def get_latest(self, name: str) -> float | None:
        entries = self._metrics.get(name, [])
        return entries[-1].value if entries else None

    def get_average(self, name: str, window: int = 100) -> float | None:
        entries = self._metrics.get(name, [])
        if not entries:
            return None
        recent = entries[-window:]
        return sum(e.value for e in recent) / len(recent)

    def get_trend(self, name: str, window: int = 50) -> str:
        """Returns 'improving', 'degrading', or 'stable'."""
        entries = self._metrics.get(name, [])
        if len(entries) < window:
            return "insufficient_data"

        recent = entries[-window:]
        mid = len(recent) // 2
        first_half = sum(e.value for e in recent[:mid]) / mid
        second_half = sum(e.value for e in recent[mid:]) / (len(recent) - mid)

        diff = (second_half - first_half) / max(abs(first_half), 0.001)
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "degrading"
        return "stable"

    def check_degradation(self, name: str, threshold: float, window: int = 50):
        """Alert if metric drops below threshold."""
        avg = self.get_average(name, window)
        if avg is not None and avg < threshold:
            alert = {
                "metric": name,
                "value": round(avg, 4),
                "threshold": threshold,
                "timestamp": time.time(),
                "trend": self.get_trend(name),
            }
            self._alerts.append(alert)
            logger.warning(f"DEGRADATION: {name}={avg:.4f} < {threshold}")
            return alert
        return None

    def full_report(self) -> dict:
        """Generate comprehensive metrics report."""
        report = {}
        for name, entries in self._metrics.items():
            if not entries:
                continue
            values = [e.value for e in entries]
            report[name] = {
                "latest": round(values[-1], 4),
                "average": round(sum(values) / len(values), 4),
                "min": round(min(values), 4),
                "max": round(max(values), 4),
                "count": len(values),
                "trend": self.get_trend(name),
                "unit": entries[-1].unit,
            }
        return report

    def agent_scorecard(self, agent_id: str) -> dict:
        """Generate scorecard for a specific agent."""
        prefix = f"agent.{agent_id}."
        card = {}
        for name, entries in self._metrics.items():
            if name.startswith(prefix):
                metric_name = name[len(prefix):]
                values = [e.value for e in entries]
                card[metric_name] = {
                    "latest": round(values[-1], 4),
                    "average": round(sum(values) / len(values), 4),
                    "count": len(values),
                }
        return card

    @property
    def alerts(self) -> list[dict]:
        return self._alerts[-50:]


# ─── Standard metric names ───

METRIC_ACCURACY = "accuracy"
METRIC_LATENCY = "latency_ms"
METRIC_COST_USD = "cost_usd"
METRIC_SIGNAL_ROI = "signal_roi"
METRIC_WIN_RATE = "win_rate"
METRIC_THROUGHPUT = "tx_per_second"
METRIC_AGENT_SCORE = "agent_composite_score"
