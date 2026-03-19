"""
Trading Decision Head — generates trade entries and exits.

INPUT:  Alpha signals + market regime + portfolio state
OUTPUT: Trade plan with entry/exit/size

Answers: "Should we trade this, and how?"
"""

from __future__ import annotations

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from heads.base_head import BaseHead, HeadDecision

TRADING_PROMPT = """You are a trading decision head in a multi-agent system.

Given alpha signals and market context, decide on trade execution.

Output ONLY valid JSON:
{
  "action": "buy|sell|hold|skip",
  "token": "token_address_or_symbol",
  "entry_price": 0.0,
  "size_pct": 0.0,
  "take_profit_pct": 0.0,
  "stop_loss_pct": 0.0,
  "time_horizon": "scalp|swing|hold",
  "conviction": 0.0-1.0,
  "reasoning": "brief explanation"
}"""


class TradingHead(BaseHead):
    """Generates actionable trade plans."""

    def __init__(self, weight: float = 1.5):
        super().__init__("TradingDecision", weight)
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def decide(self, input_data: dict) -> HeadDecision:
        import json
        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": TRADING_PROMPT},
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
                decision_type="trade_plan",
                action=result.get("action", "hold"),
                confidence=float(result.get("conviction", 0.5)),
                reasoning=result.get("reasoning", ""),
                data=result,
            )
        except Exception as e:
            return HeadDecision(
                head_name=self.name,
                decision_type="trade_plan",
                action="hold",
                confidence=0.0,
                reasoning=f"Error: {e}",
            )
