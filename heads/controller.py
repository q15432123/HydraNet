"""
Controller — fuses decisions from all heads into final action.

This is the "brain" that combines multiple specialized heads
using weighted voting with risk veto power.

Data flow:
  Raw Data → [Market, Trading, Risk, OnChain] → Controller → Final Decision

The controller resolves conflicts:
  - If Risk says "avoid", override all others
  - Otherwise, weighted vote based on head confidence × weight
"""

from __future__ import annotations

import logging
import time
from typing import Any

from heads.base_head import BaseHead, HeadDecision

logger = logging.getLogger("hydranet.heads.controller")


class FusedDecision:
    """The final system-level decision after multi-head fusion."""

    def __init__(
        self,
        action: str,
        confidence: float,
        reasoning: str,
        head_decisions: list[HeadDecision],
        metadata: dict[str, Any] = None,
    ):
        self.action = action
        self.confidence = confidence
        self.reasoning = reasoning
        self.head_decisions = head_decisions
        self.metadata = metadata or {}
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "heads": [d.to_dict() for d in self.head_decisions],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class HeadController:
    """Orchestrates multi-head decision making."""

    def __init__(self):
        self._heads: list[BaseHead] = []
        self._decision_log: list[FusedDecision] = []

    def register_head(self, head: BaseHead):
        self._heads.append(head)
        logger.info(f"Registered head: {head.name} (weight={head.weight})")

    async def decide(self, input_data: dict) -> FusedDecision:
        """
        Run all heads in parallel, then fuse their decisions.

        Decision fusion algorithm:
        1. Run all heads concurrently
        2. Check for risk veto (Risk head says "avoid" with high confidence)
        3. Weighted vote: sum(confidence × weight) per action
        4. Highest weighted score wins
        """
        import asyncio

        # Run all heads in parallel
        tasks = [head.run(input_data) for head in self._heads]
        decisions: list[HeadDecision] = await asyncio.gather(*tasks)

        # Step 1: Check risk veto
        risk_decisions = [d for d in decisions if d.head_name == "RiskManagement"]
        for rd in risk_decisions:
            if rd.action == "avoid" and rd.confidence > 0.3:
                fused = FusedDecision(
                    action="avoid",
                    confidence=rd.confidence,
                    reasoning=f"RISK VETO: {rd.reasoning}",
                    head_decisions=decisions,
                    metadata={"vetoed_by": "RiskManagement"},
                )
                self._decision_log.append(fused)
                logger.info(f"Decision: AVOID (risk veto, conf={rd.confidence:.2f})")
                return fused

        # Step 2: Weighted voting
        action_scores: dict[str, float] = {}
        action_reasons: dict[str, list[str]] = {}

        for decision in decisions:
            head = next((h for h in self._heads if h.name == decision.head_name), None)
            weight = head.weight if head else 1.0
            score = decision.confidence * weight

            action = decision.action
            action_scores[action] = action_scores.get(action, 0) + score

            if action not in action_reasons:
                action_reasons[action] = []
            action_reasons[action].append(f"{decision.head_name}: {decision.reasoning}")

        # Step 3: Pick highest scoring action
        if not action_scores:
            best_action = "hold"
            best_score = 0.0
        else:
            best_action = max(action_scores, key=action_scores.get)
            best_score = action_scores[best_action]

        # Normalize confidence
        total_weight = sum(h.weight for h in self._heads)
        normalized_conf = min(1.0, best_score / max(1.0, total_weight))

        reasoning_parts = action_reasons.get(best_action, ["No reasoning available"])
        combined_reasoning = " | ".join(reasoning_parts[:3])

        fused = FusedDecision(
            action=best_action,
            confidence=normalized_conf,
            reasoning=combined_reasoning,
            head_decisions=decisions,
            metadata={
                "votes": {k: round(v, 3) for k, v in action_scores.items()},
                "total_weight": total_weight,
            },
        )

        self._decision_log.append(fused)
        logger.info(
            f"Decision: {best_action.upper()} "
            f"(conf={normalized_conf:.2f}, votes={action_scores})"
        )
        return fused

    def get_head_stats(self) -> list[dict]:
        return [h.stats for h in self._heads]

    def get_decision_history(self, limit: int = 20) -> list[dict]:
        return [d.to_dict() for d in self._decision_log[-limit:]]

    @property
    def total_decisions(self) -> int:
        return len(self._decision_log)
