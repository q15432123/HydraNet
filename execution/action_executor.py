"""
Action Executor — triggers real-world actions from agent decisions.

Handles alerts, simulated trades, and external API calls
with safety checks and rate limiting.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any
from dataclasses import dataclass, field

logger = logging.getLogger("hydranet.executor")


@dataclass
class TradeSimulation:
    trade_id: str
    token: str
    direction: str  # "buy" | "sell"
    entry_price: float
    size_sol: float
    timestamp: float = field(default_factory=time.time)
    exit_price: float | None = None
    closed_at: float | None = None
    pnl_sol: float = 0.0
    status: str = "open"  # "open" | "closed" | "stopped"


class ActionExecutor:
    """Executes actions from agent outputs with safety controls."""

    def __init__(self):
        self._simulated_trades: dict[str, TradeSimulation] = {}
        self._alerts: list[dict] = []
        self._action_log: list[dict] = []
        self._rate_limit: dict[str, float] = {}
        self._min_interval = 5.0  # seconds between same action type

    def _check_rate_limit(self, action_type: str) -> bool:
        last = self._rate_limit.get(action_type, 0)
        if time.time() - last < self._min_interval:
            return False
        self._rate_limit[action_type] = time.time()
        return True

    async def execute(self, action: dict) -> dict:
        """Route an action to the appropriate handler."""
        action_type = action.get("type", "unknown")

        if not self._check_rate_limit(action_type):
            return {"status": "rate_limited", "type": action_type}

        self._action_log.append({
            "type": action_type,
            "timestamp": time.time(),
            "payload": action,
        })

        handlers = {
            "alert": self._handle_alert,
            "simulate_trade": self._handle_simulated_trade,
            "close_trade": self._handle_close_trade,
            "log": self._handle_log,
        }

        handler = handlers.get(action_type)
        if not handler:
            return {"status": "unknown_action", "type": action_type}

        return await handler(action)

    async def _handle_alert(self, action: dict) -> dict:
        """Process an alert action."""
        alert = {
            "title": action.get("title", "Alert"),
            "message": action.get("message", ""),
            "severity": action.get("severity", "info"),
            "token": action.get("token"),
            "timestamp": time.time(),
        }
        self._alerts.append(alert)
        logger.info(f"ALERT [{alert['severity']}]: {alert['title']} — {alert['message']}")
        return {"status": "alert_sent", "alert": alert}

    async def _handle_simulated_trade(self, action: dict) -> dict:
        """Open a simulated trade."""
        import uuid
        trade_id = str(uuid.uuid4())[:8]
        trade = TradeSimulation(
            trade_id=trade_id,
            token=action.get("token", "unknown"),
            direction=action.get("direction", "buy"),
            entry_price=action.get("entry_price", 0),
            size_sol=action.get("size_sol", 1.0),
        )
        self._simulated_trades[trade_id] = trade
        logger.info(
            f"SIM TRADE: {trade.direction} {trade.token} "
            f"@ {trade.entry_price} ({trade.size_sol} SOL)"
        )
        return {"status": "trade_opened", "trade_id": trade_id}

    async def _handle_close_trade(self, action: dict) -> dict:
        """Close a simulated trade."""
        trade_id = action.get("trade_id")
        exit_price = action.get("exit_price", 0)

        trade = self._simulated_trades.get(trade_id)
        if not trade:
            return {"status": "trade_not_found"}

        trade.exit_price = exit_price
        trade.closed_at = time.time()
        trade.status = "closed"

        if trade.entry_price > 0:
            if trade.direction == "buy":
                trade.pnl_sol = (exit_price - trade.entry_price) / trade.entry_price * trade.size_sol
            else:
                trade.pnl_sol = (trade.entry_price - exit_price) / trade.entry_price * trade.size_sol

        logger.info(f"SIM CLOSE: {trade_id} PnL={trade.pnl_sol:.4f} SOL")
        return {"status": "trade_closed", "pnl_sol": trade.pnl_sol}

    async def _handle_log(self, action: dict) -> dict:
        logger.info(f"ACTION LOG: {action.get('message', '')}")
        return {"status": "logged"}

    def get_open_trades(self) -> list[dict]:
        return [
            {
                "trade_id": t.trade_id,
                "token": t.token,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "size_sol": t.size_sol,
                "timestamp": t.timestamp,
            }
            for t in self._simulated_trades.values()
            if t.status == "open"
        ]

    def get_trade_history(self) -> list[dict]:
        return [
            {
                "trade_id": t.trade_id,
                "token": t.token,
                "direction": t.direction,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl_sol": round(t.pnl_sol, 4),
                "status": t.status,
            }
            for t in self._simulated_trades.values()
        ]

    def get_alerts(self, limit: int = 20) -> list[dict]:
        return self._alerts[-limit:]

    def get_total_pnl(self) -> float:
        return sum(t.pnl_sol for t in self._simulated_trades.values() if t.status == "closed")
