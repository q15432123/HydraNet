"""
Market Analysis Head — analyzes market conditions and sentiment.

INPUT:  Token price data, volume, liquidity metrics
OUTPUT: Market regime classification + opportunity scoring

Answers: "What is the market doing right now?"
"""

from __future__ import annotations

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from heads.base_head import BaseHead, HeadDecision

MARKET_PROMPT = """You are a crypto market analyst head in a multi-agent decision system.

Analyze the provided market data and classify the current regime.

Output ONLY valid JSON:
{
  "regime": "bull|bear|sideways|volatile",
  "trend_strength": 0.0-1.0,
  "opportunity_score": 0.0-1.0,
  "key_signals": ["signal1", "signal2"],
  "recommendation": "aggressive|moderate|defensive",
  "reasoning": "brief explanation"
}"""


class MarketHead(BaseHead):
    """Classifies market regime and scores opportunities."""

    def __init__(self, weight: float = 1.0):
        super().__init__("MarketAnalysis", weight)
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def decide(self, input_data: dict) -> HeadDecision:
        import json
        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": MARKET_PROMPT},
                    {"role": "user", "content": json.dumps(input_data)},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)

            action_map = {
                "aggressive": "buy",
                "moderate": "hold",
                "defensive": "avoid",
            }

            return HeadDecision(
                head_name=self.name,
                decision_type="insight",
                action=action_map.get(result.get("recommendation", ""), "hold"),
                confidence=float(result.get("opportunity_score", 0.5)),
                reasoning=result.get("reasoning", ""),
                data=result,
            )
        except Exception as e:
            return HeadDecision(
                head_name=self.name,
                decision_type="insight",
                action="hold",
                confidence=0.0,
                reasoning=f"Error: {e}",
            )
