"""
Pattern Detector Agent — identifies profitable trading patterns.

Analyzes wallet clusters and transaction histories to find:
- Early token entries (smart money signals)
- Accumulation patterns before pumps
- DEX liquidity sniping
- Insider trading indicators
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import BaseAgent

logger = logging.getLogger("hydranet.agent.pattern")

PATTERN_PROMPT = """You are an on-chain alpha analyst. Your job is to detect profitable patterns.

Given wallet activity data and cluster analysis, identify:

1. Smart Money Signals:
   - Wallets that consistently buy tokens before 5x+ moves
   - Early DEX liquidity provision patterns
   - Token accumulation before major announcements

2. Alpha Patterns:
   - New token launches being bought by known profitable wallets
   - Unusual volume spikes in low-cap tokens
   - Cross-DEX arbitrage opportunities

3. Risk Patterns:
   - Rug pull indicators (LP removal, dev wallet selling)
   - Pump & dump coordination
   - Wash trading inflation

Output structured JSON:
- signals: list of {signal_type, token, confidence: 0-1, wallets_involved, potential_roi, risk_level}
- alpha_opportunities: list of {token, entry_reason, suggested_action, urgency: "low"|"medium"|"high"}
- warnings: list of {token, risk_type, severity, evidence}
"""


class PatternDetectorAgent(BaseAgent):
    """Detects profitable patterns and alpha opportunities."""

    async def _process(self, payload: dict) -> Any:
        action = payload.get("action", "detect")

        if action == "detect":
            return await self._detect_patterns(payload)
        elif action == "evaluate_token":
            return await self._evaluate_token(payload)

        return {"error": f"Unknown action: {action}"}

    async def _detect_patterns(self, payload: dict) -> Any:
        """Run pattern detection on provided data."""
        # Pull relevant memory
        recent_clusters = await self.recall("wallet cluster analysis", n=5)
        recent_signals = await self.recall("alpha signal", n=5)

        analysis_payload = {
            "wallet_data": payload.get("wallet_data", {}),
            "cluster_data": payload.get("cluster_data", {}),
            "historical_context": [c["content"][:500] for c in recent_clusters],
            "recent_signals": [s["content"][:500] for s in recent_signals],
        }

        result = await super().execute_task(analysis_payload)

        # Store signals
        await self.remember(
            f"signal:{int(time.time())}",
            str(result),
            metadata={"type": "alpha_signal"},
        )

        # Emit alpha events
        await self.emit_event("alpha_signals", {
            "type": "patterns_detected",
            "agent_id": self.agent_id,
            "timestamp": time.time(),
        })

        return result

    async def _evaluate_token(self, payload: dict) -> Any:
        """Evaluate a specific token for opportunities/risks."""
        token = payload.get("token_address")
        if not token:
            return {"error": "token_address required"}

        return await super().execute_task({
            "task": "evaluate_single_token",
            "token_address": token,
            "holder_data": payload.get("holder_data", []),
            "price_history": payload.get("price_history", []),
        })


def create_pattern_detector_dna():
    from core.agent_dna import AgentDNA
    return AgentDNA(
        name="PatternDetector",
        purpose="Identify profitable trading patterns and alpha opportunities on-chain",
        agent_type="detector",
        input_sources=["clusters", "wallet_events", "alpha_signals"],
        decision_prompt=PATTERN_PROMPT,
        output_actions=["emit_event", "store_memory", "delegate"],
        tags=["detector", "alpha", "patterns"],
        parameters={
            "min_confidence": 0.6,
            "lookback_hours": 24,
            "min_roi_threshold": 0.1,
        },
    )
