"""
Risk Management Head — evaluates and controls risk exposure.

INPUT:  Proposed trades + portfolio state + market regime
OUTPUT: Risk assessment, position limits, veto decisions

Answers: "Is this safe to do?"
"""

from __future__ import annotations

from openai import AsyncOpenAI
from config import OPENAI_API_KEY
from heads.base_head import BaseHead, HeadDecision

RISK_PROMPT = """You are a risk management head in a multi-agent trading system.

Your job is to PROTECT capital. Evaluate the proposed action for risk.

Output ONLY valid JSON:
{
  "risk_level": "low|medium|high|critical",
  "risk_score": 0.0-1.0,
  "approved": true/false,
  "max_position_pct": 0.0,
  "concerns": ["concern1", "concern2"],
  "adjustments": "any modifications to reduce risk",
  "reasoning": "brief explanation"
}

Be conservative. When in doubt, reduce size or reject."""


class RiskHead(BaseHead):
    """Evaluates risk and can veto dangerous trades."""

    def __init__(self, weight: float = 2.0):  # highest weight — safety first
        super().__init__("RiskManagement", weight)
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)

    async def decide(self, input_data: dict) -> HeadDecision:
        import json
        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": RISK_PROMPT},
                    {"role": "user", "content": json.dumps(input_data)},
                ],
                temperature=0.1,  # low temp for consistent risk assessment
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            result = json.loads(content)

            approved = result.get("approved", False)
            action = "buy" if approved else "avoid"

            return HeadDecision(
                head_name=self.name,
                decision_type="risk_alert",
                action=action,
                confidence=1.0 - float(result.get("risk_score", 0.5)),
                reasoning=result.get("reasoning", ""),
                data=result,
            )
        except Exception as e:
            # On error, default to conservative
            return HeadDecision(
                head_name=self.name,
                decision_type="risk_alert",
                action="avoid",
                confidence=0.0,
                reasoning=f"Risk assessment failed: {e}. Defaulting to reject.",
            )
