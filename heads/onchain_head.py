"""
On-Chain Intelligence Head — analyzes blockchain-specific data.

INPUT:  Wallet clusters, token holder data, LP movements
OUTPUT: On-chain insights, whale alerts, rug pull warnings

Answers: "What does the chain tell us?"
"""

from __future__ import annotations

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from heads.base_head import BaseHead, HeadDecision

ONCHAIN_PROMPT = """You are an on-chain intelligence head in a multi-agent system.

Analyze blockchain data for actionable insights.

Output ONLY valid JSON:
{
  "insight_type": "whale_move|rug_warning|accumulation|distribution|smart_money",
  "severity": "info|warning|critical",
  "tokens_affected": ["token1", "token2"],
  "wallets_involved": 0,
  "action": "buy|sell|alert|avoid",
  "confidence": 0.0-1.0,
  "evidence": ["evidence1", "evidence2"],
  "reasoning": "brief explanation"
}"""


class OnChainHead(BaseHead):
    """Analyzes on-chain data for intelligence."""

    def __init__(self, weight: float = 1.2):
        super().__init__("OnChainIntel", weight)
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def decide(self, input_data: dict) -> HeadDecision:
        import json
        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": ONCHAIN_PROMPT},
                    {"role": "user", "content": json.dumps(input_data)},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)

            return HeadDecision(
                head_name=self.name,
                decision_type="signal",
                action=result.get("action", "alert"),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", ""),
                data=result,
            )
        except Exception as e:
            return HeadDecision(
                head_name=self.name,
                decision_type="signal",
                action="alert",
                confidence=0.0,
                reasoning=f"Error: {e}",
            )
