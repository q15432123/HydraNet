"""
Judge System — AI scores AI.

Multiple judge strategies for evaluating LLM outputs:
- Criteria-based scoring
- Pairwise comparison
- Consensus voting
"""

from __future__ import annotations

import json
import logging
from typing import Any

from openai import AsyncOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger("hydranet.judge")


class Judge:
    """AI judge that scores other AI outputs."""

    def __init__(self, strategy: str = "criteria"):
        self._llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.strategy = strategy  # "criteria" | "pairwise" | "consensus"

    async def score(self, task: str, responses: dict[str, str]) -> dict:
        """Score responses using the configured strategy."""
        if self.strategy == "criteria":
            return await self._criteria_score(task, responses)
        elif self.strategy == "pairwise":
            return await self._pairwise_score(task, responses)
        elif self.strategy == "consensus":
            return await self._consensus_score(task, responses)
        return {}

    async def _criteria_score(self, task: str, responses: dict[str, str]) -> dict:
        """Score each response on multiple criteria."""
        resp_text = "\n\n".join(f"[{name}]:\n{resp}" for name, resp in responses.items())

        prompt = (
            f"Score each AI response on a 0-100 scale.\n\n"
            f"Task: {task}\n\nResponses:\n{resp_text}\n\n"
            f"Criteria:\n"
            f"- Correctness (0-100)\n"
            f"- Completeness (0-100)\n"
            f"- Clarity (0-100)\n"
            f"- Creativity (0-100)\n"
            f"- Overall (weighted average)\n\n"
            f"Output JSON: {{\"name\": {{\"correctness\": n, \"completeness\": n, "
            f"\"clarity\": n, \"creativity\": n, \"overall\": n}}, ...}}"
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=800,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            return json.loads(content)
        except Exception as e:
            return {"error": str(e)}

    async def _pairwise_score(self, task: str, responses: dict[str, str]) -> dict:
        """Compare responses in pairs."""
        names = list(responses.keys())
        wins = {name: 0 for name in names}

        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                a, b = names[i], names[j]
                prompt = (
                    f"Task: {task}\n\n"
                    f"Response A ({a}):\n{responses[a]}\n\n"
                    f"Response B ({b}):\n{responses[b]}\n\n"
                    f"Which is better? Output JSON: {{\"winner\": \"A\" or \"B\", \"reason\": \"...\"}}"
                )
                try:
                    resp = await self._llm.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=200,
                    )
                    content = resp.choices[0].message.content
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    result = json.loads(content)
                    winner = a if result.get("winner") == "A" else b
                    wins[winner] += 1
                except Exception:
                    pass

        return {"pairwise_wins": wins, "winner": max(wins, key=wins.get)}

    async def _consensus_score(self, task: str, responses: dict[str, str]) -> dict:
        """Run 3 independent judges and take consensus."""
        import asyncio
        judges = [self._criteria_score(task, responses) for _ in range(3)]
        results = await asyncio.gather(*judges, return_exceptions=True)

        valid = [r for r in results if isinstance(r, dict) and "error" not in r]
        if not valid:
            return {"error": "All judges failed"}

        # Average scores across judges
        final = {}
        for result in valid:
            for name, scores in result.items():
                if isinstance(scores, dict) and "overall" in scores:
                    if name not in final:
                        final[name] = []
                    final[name].append(scores["overall"])

        averaged = {name: sum(scores) / len(scores) for name, scores in final.items()}
        winner = max(averaged, key=averaged.get) if averaged else ""

        return {
            "consensus_scores": averaged,
            "winner": winner,
            "judge_count": len(valid),
        }
