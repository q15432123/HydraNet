"""
Agent DNA — the genetic blueprint of every agent in HydraNet.

Each agent is defined by its DNA: purpose, inputs, decision logic,
output actions, and performance metrics. Agents are storable,
cloneable, and mutable.
"""

from __future__ import annotations

import json
import uuid
import copy
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    DEAD = "dead"


@dataclass
class PerformanceMetrics:
    accuracy: float = 0.0
    profitability: float = 0.0
    latency_ms: float = 0.0
    resource_usage: float = 0.0
    total_runs: int = 0
    successful_runs: int = 0
    created_at: float = field(default_factory=time.time)
    last_run_at: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def composite_score(self) -> float:
        """Weighted composite score for evolution decisions."""
        w_accuracy = 0.35
        w_profit = 0.30
        w_success = 0.25
        w_latency = 0.10
        latency_score = max(0, 1.0 - (self.latency_ms / 10000))
        return (
            w_accuracy * self.accuracy
            + w_profit * min(1.0, max(0, self.profitability))
            + w_success * self.success_rate
            + w_latency * latency_score
        )


@dataclass
class AgentDNA:
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    purpose: str = ""
    agent_type: str = "generic"
    input_sources: list[str] = field(default_factory=list)
    decision_prompt: str = ""
    output_actions: list[str] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)
    metrics: PerformanceMetrics = field(default_factory=PerformanceMetrics)
    status: AgentStatus = AgentStatus.IDLE
    generation: int = 0
    parent_id: str | None = None
    tags: list[str] = field(default_factory=list)

    def clone(self, mutate: bool = False) -> AgentDNA:
        """Deep clone this agent DNA. Optionally flag as mutated."""
        new_dna = copy.deepcopy(self)
        new_dna.agent_id = str(uuid.uuid4())[:12]
        new_dna.generation = self.generation + 1
        new_dna.parent_id = self.agent_id
        new_dna.metrics = PerformanceMetrics()
        new_dna.status = AgentStatus.IDLE
        if mutate:
            new_dna.tags.append("mutated")
        return new_dna

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = self.status.value
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> AgentDNA:
        metrics_data = data.pop("metrics", {})
        status_val = data.pop("status", "idle")
        dna = cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        dna.metrics = PerformanceMetrics(**metrics_data)
        dna.status = AgentStatus(status_val)
        return dna

    @classmethod
    def from_json(cls, json_str: str) -> AgentDNA:
        return cls.from_dict(json.loads(json_str))
