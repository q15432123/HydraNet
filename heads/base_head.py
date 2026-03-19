"""
Base Head — shared interface for all decision heads.

HydraNet uses a multi-head architecture where each head
specializes in one domain. The Controller routes data
to heads and fuses their outputs.

Each head:
  INPUT:  Normalized data from pipeline
  OUTPUT: Typed decision with confidence score
"""

from __future__ import annotations

import time
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("hydranet.heads")


@dataclass
class HeadDecision:
    """Standardized output from any decision head."""
    head_name: str
    decision_type: str  # "signal" | "risk_alert" | "trade_plan" | "insight"
    action: str  # "buy" | "sell" | "hold" | "avoid" | "alert"
    confidence: float  # 0.0 - 1.0
    reasoning: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "head": self.head_name,
            "type": self.decision_type,
            "action": self.action,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class BaseHead(ABC):
    """Abstract base for all decision heads."""

    def __init__(self, name: str, weight: float = 1.0):
        self.name = name
        self.weight = weight
        self._total_decisions = 0
        self._correct_decisions = 0
        self._total_latency_ms = 0.0

    @abstractmethod
    async def decide(self, input_data: dict) -> HeadDecision:
        """Process input and produce a decision."""
        ...

    async def run(self, input_data: dict) -> HeadDecision:
        """Wrapper that tracks metrics."""
        start = time.time()
        decision = await self.decide(input_data)
        elapsed = (time.time() - start) * 1000

        self._total_decisions += 1
        self._total_latency_ms += elapsed

        logger.debug(
            f"[{self.name}] {decision.action} "
            f"(conf={decision.confidence:.2f}, {elapsed:.0f}ms)"
        )
        return decision

    def record_outcome(self, was_correct: bool):
        if was_correct:
            self._correct_decisions += 1

    @property
    def accuracy(self) -> float:
        if self._total_decisions == 0:
            return 0.0
        return self._correct_decisions / self._total_decisions

    @property
    def avg_latency_ms(self) -> float:
        if self._total_decisions == 0:
            return 0.0
        return self._total_latency_ms / self._total_decisions

    @property
    def stats(self) -> dict:
        return {
            "name": self.name,
            "weight": self.weight,
            "total_decisions": self._total_decisions,
            "accuracy": round(self.accuracy, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
        }
