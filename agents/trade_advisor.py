"""
Trade Advisor Agent — generates trade suggestions and simulations.

Takes alpha signals and converts them into actionable trade plans
with risk management parameters.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import BaseAgent

logger = logging.getLogger("hydranet.agent.advisor")

ADVISOR_PROMPT = """You are a crypto trading strategist specializing in Solana meme coins and DeFi.

Given alpha signals and pattern analysis, generate actionable trade plans.

For each opportunity, provide:
1. Entry Strategy:
   - Token address and current price
   - Suggested entry price range
   - Position size (% of portfolio)
   - Entry timing (immediate / wait for dip / DCA)

2. Risk Management:
   - Stop loss level
   - Take profit targets (partial exits)
   - Maximum holding period
   - Risk/reward ratio

3. Conviction Assessment:
   - Signal strength (1-10)
   - Number of confirming indicators
   - Historical success rate of similar setups
   - Counterarguments / bear case

Output structured JSON:
- trades: list of {
    token, direction: "long"|"short"|"avoid",
    entry_price, size_pct, stop_loss, take_profits: [],
    conviction: 1-10, reasoning, risk_reward_ratio,
    time_horizon: "scalp"|"swing"|"hold"
  }
- portfolio_summary: {total_risk_pct, correlation_risk, diversification_score}
- market_context: brief assessment of current market conditions
"""


class TradeAdvisorAgent(BaseAgent):
    """Generates trade plans from alpha signals."""

    async def _process(self, payload: dict) -> Any:
        action = payload.get("action", "advise")

        if action == "advise":
            return await self._generate_advice(payload)
        elif action == "simulate":
            return await self._simulate_trade(payload)
        elif action == "backtest":
            return await self._backtest_signal(payload)

        return {"error": f"Unknown action: {action}"}

    async def _generate_advice(self, payload: dict) -> Any:
        """Generate trade recommendations from signals."""
        signals = payload.get("signals", [])
        portfolio = payload.get("current_portfolio", {})

        # Recall past performance
        past_trades = await self.recall("trade advice outcome", n=10)

        analysis_payload = {
            "active_signals": signals,
            "current_portfolio": portfolio,
            "past_performance": [t["content"][:300] for t in past_trades],
        }

        result = await super().execute_task(analysis_payload)

        # Store advice
        await self.remember(
            f"advice:{int(time.time())}",
            str(result),
            metadata={"type": "trade_advice", "signal_count": len(signals)},
        )

        # Emit to execution layer
        await self.emit_event("trade_signals", {
            "type": "trade_advice",
            "agent_id": self.agent_id,
            "timestamp": time.time(),
        })

        return result

    async def _simulate_trade(self, payload: dict) -> dict:
        """Simulate a trade with given parameters."""
        entry = payload.get("entry_price", 0)
        exit_price = payload.get("exit_price", 0)
        size_sol = payload.get("size_sol", 1.0)

        if entry <= 0:
            return {"error": "invalid entry_price"}

        pnl = (exit_price - entry) / entry * size_sol
        return {
            "simulated": True,
            "entry": entry,
            "exit": exit_price,
            "size_sol": size_sol,
            "pnl_sol": round(pnl, 4),
            "pnl_pct": round((exit_price - entry) / entry * 100, 2),
        }

    async def _backtest_signal(self, payload: dict) -> Any:
        """Backtest a signal type against historical data."""
        return await super().execute_task({
            "task": "backtest",
            "signal_type": payload.get("signal_type"),
            "historical_data": payload.get("data", []),
        })


def create_trade_advisor_dna():
    from core.agent_dna import AgentDNA
    return AgentDNA(
        name="TradeAdvisor",
        purpose="Generate actionable trade plans from alpha signals with risk management",
        agent_type="advisor",
        input_sources=["alpha_signals", "trade_signals"],
        decision_prompt=ADVISOR_PROMPT,
        output_actions=["emit_event", "store_memory"],
        tags=["advisor", "trading", "risk"],
        parameters={
            "max_position_pct": 10.0,
            "default_stop_loss_pct": 15.0,
            "min_conviction": 6,
        },
    )
