"""
Evaluation & Evolution Engine — Darwinian selection for agents.

Continuously scores agents and applies evolutionary pressure:
- Kill underperformers
- Replicate top performers
- Mutate prompts to explore improvements
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import TYPE_CHECKING

from openai import AsyncOpenAI

from config import (
    OPENAI_API_KEY,
    MIN_SCORE_THRESHOLD,
    REPLICATION_SCORE_THRESHOLD,
    MUTATION_RATE,
    EVOLUTION_INTERVAL,
)
from core.agent_dna import AgentDNA, AgentStatus

if TYPE_CHECKING:
    from core.coordinator import Coordinator

logger = logging.getLogger("hydranet.evaluator")

MUTATION_PROMPT = """You are an AI prompt engineer evolving agent prompts.

Given the current agent prompt and its performance metrics, generate a MUTATED version.

Rules:
- Keep the core purpose intact
- Modify analysis criteria, weighting, or approach
- Add or remove specific detection heuristics
- Adjust output format for better actionability
- Make the prompt more specific or more general based on performance

Current prompt:
{current_prompt}

Performance:
- Accuracy: {accuracy}
- Success rate: {success_rate}
- Composite score: {score}

Generate ONLY the new prompt text, nothing else.
"""


class EvolutionEngine:
    """Evaluates agents and drives evolutionary cycles."""

    def __init__(self, coordinator: Coordinator):
        self.coordinator = coordinator
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._running = False
        self._task: asyncio.Task | None = None
        self._generation = 0

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._evolution_loop())
        logger.info("Evolution engine started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _evolution_loop(self):
        """Run evolution cycles at configured intervals."""
        while self._running:
            try:
                await asyncio.sleep(EVOLUTION_INTERVAL)
                await self.run_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution cycle error: {e}")

    async def run_cycle(self):
        """Execute one evolution cycle."""
        self._generation += 1
        logger.info(f"=== Evolution Cycle {self._generation} ===")

        all_dna = self.coordinator.get_all_dna()
        active = [d for d in all_dna if d.status == AgentStatus.RUNNING]

        if not active:
            logger.info("No active agents to evaluate")
            return

        # Score and sort
        scored = [(dna, dna.metrics.composite_score) for dna in active]
        scored.sort(key=lambda x: x[1], reverse=True)

        report = {
            "generation": self._generation,
            "agents_evaluated": len(scored),
            "killed": [],
            "replicated": [],
            "mutated": [],
        }

        # Kill underperformers (only if they've had enough runs)
        for dna, score in scored:
            if dna.metrics.total_runs >= 10 and score < MIN_SCORE_THRESHOLD:
                await self.coordinator.kill_agent(dna.agent_id)
                report["killed"].append({"id": dna.agent_id, "name": dna.name, "score": score})
                logger.warning(f"Killed {dna.name} (score={score:.3f})")

        # Replicate top performers
        for dna, score in scored[:3]:
            if score >= REPLICATION_SCORE_THRESHOLD and dna.metrics.total_runs >= 5:
                new_dna = dna.clone(mutate=False)
                new_dna.name = f"{dna.name}_gen{self._generation}"
                report["replicated"].append({"parent": dna.agent_id, "child": new_dna.agent_id})
                logger.info(f"Replicated {dna.name} → {new_dna.name}")

        # Mutate random agents
        for dna, score in scored:
            if random.random() < MUTATION_RATE and dna.decision_prompt:
                mutated_prompt = await self._mutate_prompt(dna)
                if mutated_prompt:
                    new_dna = dna.clone(mutate=True)
                    new_dna.name = f"{dna.name}_mut{self._generation}"
                    new_dna.decision_prompt = mutated_prompt
                    report["mutated"].append({"parent": dna.agent_id, "child": new_dna.agent_id})
                    logger.info(f"Mutated {dna.name} → {new_dna.name}")

        # Log evolution report
        await self.coordinator.history.log(
            agent_id="evolution_engine",
            event_type="evolution_cycle",
            payload=report,
        )

        logger.info(
            f"Cycle {self._generation} complete: "
            f"killed={len(report['killed'])}, "
            f"replicated={len(report['replicated'])}, "
            f"mutated={len(report['mutated'])}"
        )

        return report

    async def _mutate_prompt(self, dna: AgentDNA) -> str | None:
        """Use LLM to mutate an agent's decision prompt."""
        try:
            prompt = MUTATION_PROMPT.format(
                current_prompt=dna.decision_prompt[:2000],
                accuracy=f"{dna.metrics.accuracy:.3f}",
                success_rate=f"{dna.metrics.success_rate:.3f}",
                score=f"{dna.metrics.composite_score:.3f}",
            )

            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Mutation failed for {dna.name}: {e}")
            return None

    def get_leaderboard(self) -> list[dict]:
        """Get agents ranked by composite score."""
        all_dna = self.coordinator.get_all_dna()
        ranked = sorted(all_dna, key=lambda d: d.metrics.composite_score, reverse=True)
        return [
            {
                "rank": i + 1,
                "name": d.name,
                "id": d.agent_id,
                "score": round(d.metrics.composite_score, 3),
                "generation": d.generation,
                "runs": d.metrics.total_runs,
                "status": d.status.value,
            }
            for i, d in enumerate(ranked)
        ]
