"""
Battle Arena — the core engine where LLMs fight.

3 AI enter. 1 AI leaves.

Flow:
  1. User submits a prompt
  2. 3 LLMs generate answers independently
  3. Each LLM critiques the other two
  4. Judge AI scores all answers
  5. Winner is selected
  6. (Optional) Evolution: winner's approach is used to generate an even better answer
"""

from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Any

from openai import AsyncOpenAI

from config import OPENAI_API_KEY

logger = logging.getLogger("hydranet.battle")


@dataclass
class Combatant:
    """An LLM fighter in the arena."""
    name: str
    model: str
    provider: str  # "openai" | "anthropic" | "google"
    system_prompt: str = "You are a helpful assistant."
    temperature: float = 0.7
    wins: int = 0
    losses: int = 0
    total_battles: int = 0
    elo: float = 1000.0

    @property
    def win_rate(self) -> float:
        if self.total_battles == 0:
            return 0.0
        return self.wins / self.total_battles

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "provider": self.provider,
            "wins": self.wins,
            "losses": self.losses,
            "total_battles": self.total_battles,
            "win_rate": round(self.win_rate, 3),
            "elo": round(self.elo, 1),
        }


@dataclass
class BattleResult:
    """Result of a single battle round."""
    battle_id: str
    prompt: str
    responses: dict[str, str]          # combatant_name -> response
    critiques: dict[str, dict[str, str]]  # combatant_name -> {target: critique}
    scores: dict[str, float]           # combatant_name -> score
    winner: str
    reasoning: str
    evolved_answer: str | None = None
    timestamp: float = field(default_factory=time.time)
    duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "battle_id": self.battle_id,
            "prompt": self.prompt,
            "responses": self.responses,
            "scores": self.scores,
            "winner": self.winner,
            "reasoning": self.reasoning,
            "evolved_answer": self.evolved_answer,
            "duration_ms": round(self.duration_ms, 1),
        }


class BattleArena:
    """
    The arena where LLMs compete.

    Usage:
        arena = BattleArena()
        arena.add_combatant(Combatant("GPT-4o", "gpt-4o", "openai"))
        arena.add_combatant(Combatant("Claude", "claude-3-5-sonnet", "anthropic"))
        arena.add_combatant(Combatant("Gemini", "gemini-pro", "google"))
        result = await arena.battle("Write a Python function to detect palindromes")
    """

    def __init__(self):
        self._combatants: list[Combatant] = []
        self._history: list[BattleResult] = []
        self._llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._battle_count = 0

    def add_combatant(self, combatant: Combatant):
        self._combatants.append(combatant)
        logger.info(f"Combatant registered: {combatant.name} ({combatant.model})")

    @property
    def leaderboard(self) -> list[dict]:
        ranked = sorted(self._combatants, key=lambda c: c.elo, reverse=True)
        return [
            {"rank": i + 1, **c.to_dict()}
            for i, c in enumerate(ranked)
        ]

    async def battle(self, prompt: str, evolve: bool = True) -> BattleResult:
        """
        Run a full battle:
          1. All combatants answer
          2. Cross-critique phase
          3. Judge scores
          4. (Optional) Evolution round
        """
        self._battle_count += 1
        battle_id = f"battle-{self._battle_count:04d}"
        start = time.time()

        logger.info(f"=== {battle_id} START ===")
        logger.info(f"Prompt: {prompt[:80]}...")

        # Phase 1: Generate responses
        responses = await self._generate_responses(prompt)
        logger.info(f"Phase 1 complete: {len(responses)} responses")

        # Phase 2: Cross-critique
        critiques = await self._cross_critique(prompt, responses)
        logger.info(f"Phase 2 complete: critiques generated")

        # Phase 3: Judge
        scores, winner, reasoning = await self._judge(prompt, responses, critiques)
        logger.info(f"Phase 3 complete: winner = {winner}")

        # Phase 4: Evolution (optional)
        evolved = None
        if evolve:
            evolved = await self._evolve(prompt, responses, critiques, winner)
            logger.info(f"Phase 4 complete: evolved answer generated")

        # Update stats
        elapsed = (time.time() - start) * 1000
        self._update_elo(scores, winner)

        result = BattleResult(
            battle_id=battle_id,
            prompt=prompt,
            responses=responses,
            critiques=critiques,
            scores=scores,
            winner=winner,
            reasoning=reasoning,
            evolved_answer=evolved,
            duration_ms=elapsed,
        )
        self._history.append(result)

        logger.info(f"=== {battle_id} END ({elapsed:.0f}ms) ===")
        return result

    async def _generate_responses(self, prompt: str) -> dict[str, str]:
        """Phase 1: Each combatant generates a response."""
        tasks = {}
        for c in self._combatants:
            tasks[c.name] = self._call_llm(c, prompt)

        results = {}
        task_items = list(tasks.items())
        responses = await asyncio.gather(*[t for _, t in task_items], return_exceptions=True)

        for (name, _), resp in zip(task_items, responses):
            if isinstance(resp, Exception):
                results[name] = f"[Error: {resp}]"
            else:
                results[name] = resp

        return results

    async def _cross_critique(self, prompt: str, responses: dict[str, str]) -> dict[str, dict[str, str]]:
        """Phase 2: Each combatant critiques the others."""
        critiques: dict[str, dict[str, str]] = {}
        tasks = []

        for critic in self._combatants:
            critiques[critic.name] = {}
            for target_name, target_response in responses.items():
                if target_name != critic.name:
                    critique_prompt = (
                        f"Original task: {prompt}\n\n"
                        f"Another AI ({target_name}) gave this answer:\n{target_response}\n\n"
                        f"Critique this answer. Be specific about:\n"
                        f"1. What's wrong or could be better\n"
                        f"2. What's good\n"
                        f"3. How you would improve it\n"
                        f"Be concise (max 200 words)."
                    )
                    tasks.append((critic.name, target_name, self._call_llm(critic, critique_prompt)))

        results = await asyncio.gather(*[t for _, _, t in tasks], return_exceptions=True)

        for (critic_name, target_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                critiques[critic_name][target_name] = f"[Error: {result}]"
            else:
                critiques[critic_name][target_name] = result

        return critiques

    async def _judge(
        self, prompt: str, responses: dict[str, str], critiques: dict[str, dict[str, str]]
    ) -> tuple[dict[str, float], str, str]:
        """Phase 3: Judge AI scores all responses."""
        # Build judge prompt
        response_text = ""
        for name, resp in responses.items():
            response_text += f"\n--- {name} ---\n{resp}\n"

        critique_text = ""
        for critic, targets in critiques.items():
            for target, critique in targets.items():
                critique_text += f"\n{critic} on {target}: {critique}\n"

        judge_prompt = (
            f"You are an impartial judge in an AI battle arena.\n\n"
            f"TASK: {prompt}\n\n"
            f"RESPONSES:{response_text}\n"
            f"CRITIQUES:{critique_text}\n\n"
            f"Score each response 0-100 based on:\n"
            f"- Correctness (40%)\n"
            f"- Completeness (25%)\n"
            f"- Clarity (20%)\n"
            f"- Creativity (15%)\n\n"
            f"Output ONLY valid JSON:\n"
            f'{{"scores": {{"name": score, ...}}, "winner": "name", "reasoning": "why"}}'
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]

            import json
            result = json.loads(content)
            scores = {k: float(v) for k, v in result.get("scores", {}).items()}
            winner = result.get("winner", "")
            reasoning = result.get("reasoning", "")
            return scores, winner, reasoning
        except Exception as e:
            logger.error(f"Judge error: {e}")
            # Fallback: first combatant wins
            scores = {c.name: 50.0 for c in self._combatants}
            return scores, self._combatants[0].name, f"Judge error: {e}"

    async def _evolve(
        self, prompt: str, responses: dict[str, str],
        critiques: dict[str, dict[str, str]], winner: str
    ) -> str:
        """Phase 4: Generate an evolved answer combining the best of all."""
        all_responses = "\n\n".join(
            f"[{name}]: {resp}" for name, resp in responses.items()
        )
        all_critiques = "\n".join(
            f"{critic} → {target}: {crit}"
            for critic, targets in critiques.items()
            for target, crit in targets.items()
        )

        evolve_prompt = (
            f"Three AIs competed on this task:\n{prompt}\n\n"
            f"Their responses:\n{all_responses}\n\n"
            f"Their critiques of each other:\n{all_critiques}\n\n"
            f"The winner was {winner}.\n\n"
            f"Now create the ULTIMATE answer by combining the best elements "
            f"from all responses and addressing all valid critiques. "
            f"This should be strictly better than any individual response."
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": evolve_prompt}],
                temperature=0.5,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Evolution error: {e}")
            return None

    async def _call_llm(self, combatant: Combatant, prompt: str) -> str:
        """Call an LLM. Currently routes everything through OpenAI API."""
        # In production, route to different providers based on combatant.provider
        # For MVP, simulate different models via different system prompts
        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": combatant.system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=combatant.temperature,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[Error: {e}]"

    def _update_elo(self, scores: dict[str, float], winner: str):
        """Update ELO ratings based on battle results."""
        K = 32
        for c in self._combatants:
            c.total_battles += 1
            if c.name == winner:
                c.wins += 1
                c.elo += K * (1 - c.win_rate)
            else:
                c.losses += 1
                c.elo -= K * c.win_rate * 0.5

    @property
    def history(self) -> list[dict]:
        return [r.to_dict() for r in self._history]

    @property
    def stats(self) -> dict:
        return {
            "total_battles": self._battle_count,
            "combatants": len(self._combatants),
            "leaderboard": self.leaderboard,
        }
