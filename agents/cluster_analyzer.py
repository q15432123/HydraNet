"""
Cluster Analyzer Agent — groups related wallets into clusters.

Detects wallet relationships through:
- Fund flow analysis (who sends to whom)
- Timing correlation (wallets that trade same tokens simultaneously)
- Token overlap (wallets holding similar portfolios)
"""

from __future__ import annotations

import logging
import time
from typing import Any

from agents.base import BaseAgent

logger = logging.getLogger("hydranet.agent.cluster")

CLUSTER_PROMPT = """You are a blockchain forensics analyst specializing in wallet clustering.

Given a set of wallet addresses and their transaction histories, identify:
1. Wallet clusters (groups likely controlled by same entity)
2. Fund flow patterns (source → destination chains)
3. Coordination signals (synchronized trading)
4. Entity classification (whale, bot, fund, retail, insider)

Clustering criteria:
- Direct fund transfers between wallets
- Trading same token within 60-second windows
- Similar portfolio composition (>70% overlap)
- Sequential transaction patterns

Output structured JSON:
- clusters: list of {cluster_id, wallets: [], confidence: 0-1, entity_type, notes}
- fund_flows: list of {from, to, total_sol, tx_count}
- coordination_score: 0-100
"""


class ClusterAnalyzerAgent(BaseAgent):
    """Groups related wallets and identifies entities."""

    async def _process(self, payload: dict) -> Any:
        action = payload.get("action", "cluster")

        if action == "cluster":
            return await self._cluster_wallets(payload)
        elif action == "check_relation":
            return await self._check_relation(payload)

        return {"error": f"Unknown action: {action}"}

    async def _cluster_wallets(self, payload: dict) -> Any:
        """Analyze wallet set and identify clusters."""
        wallets = payload.get("wallets", [])
        transactions = payload.get("transactions", [])

        if not wallets:
            return {"error": "wallets list required"}

        analysis_payload = {
            "wallet_count": len(wallets),
            "wallets": wallets[:100],
            "transaction_sample": transactions[:200],
        }

        result = await super().execute_task(analysis_payload)

        # Store cluster data
        cluster_id = f"cluster:{int(time.time())}"
        await self.remember(
            cluster_id,
            str(result),
            metadata={"type": "cluster", "wallet_count": len(wallets)},
        )

        # Notify pattern detector
        await self.emit_event("clusters", {
            "type": "cluster_found",
            "cluster_id": cluster_id,
            "wallet_count": len(wallets),
            "agent_id": self.agent_id,
        })

        return result

    async def _check_relation(self, payload: dict) -> Any:
        """Check if two wallets are related."""
        wallet_a = payload.get("wallet_a")
        wallet_b = payload.get("wallet_b")

        if not wallet_a or not wallet_b:
            return {"error": "wallet_a and wallet_b required"}

        analysis_payload = {
            "task": "check_relationship",
            "wallet_a": wallet_a,
            "wallet_b": wallet_b,
            "transactions_a": payload.get("transactions_a", []),
            "transactions_b": payload.get("transactions_b", []),
        }

        return await super().execute_task(analysis_payload)


def create_cluster_analyzer_dna():
    from core.agent_dna import AgentDNA
    return AgentDNA(
        name="ClusterAnalyzer",
        purpose="Group related wallets and identify coordinated entities",
        agent_type="analyzer",
        input_sources=["wallet_events", "discoveries"],
        decision_prompt=CLUSTER_PROMPT,
        output_actions=["emit_event", "store_memory"],
        tags=["analyzer", "cluster", "forensics"],
        parameters={
            "min_cluster_size": 2,
            "correlation_threshold": 0.7,
            "time_window_seconds": 60,
        },
    )
