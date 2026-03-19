"""
Prompt Evolver — self-improving prompt generation.

Takes a weak prompt, battles it through multiple rounds,
and outputs a dramatically improved version.

This is the "Evolution Mode" — prompts get stronger every round.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from openai import AsyncOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger("hydranet.evolver")


class PromptEvolver:
    """Evolves prompts through iterative battle and refinement."""

    def __init__(self):
        self._llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._history: list[dict] = []

    async def evolve(
        self,
        seed_prompt: str,
        task_description: str,
        rounds: int = 3,
    ) -> dict:
        """
        Evolve a prompt through multiple rounds of self-improvement.

        Each round:
          1. Generate 3 variations of the prompt
          2. Test each on the task
          3. Critique results
          4. Synthesize the best elements into next-gen prompt

        Returns the evolved prompt + full evolution history.
        """
        current = seed_prompt
        evolution_log = []

        for r in range(rounds):
            logger.info(f"Evolution round {r+1}/{rounds}")
            start = time.time()

            # Step 1: Generate variations
            variations = await self._generate_variations(current, task_description)

            # Step 2: Test all variations
            results = await self._test_variations(variations, task_description)

            # Step 3: Critique and rank
            ranked = await self._rank_variations(results, task_description)

            # Step 4: Synthesize best into next generation
            current = await self._synthesize(ranked, task_description)

            elapsed = (time.time() - start) * 1000
            round_log = {
                "round": r + 1,
                "variations_tested": len(variations),
                "best_score": ranked[0]["score"] if ranked else 0,
                "duration_ms": round(elapsed, 1),
                "prompt_preview": current[:200],
            }
            evolution_log.append(round_log)
            logger.info(f"Round {r+1}: best_score={round_log['best_score']}, {elapsed:.0f}ms")

        result = {
            "original_prompt": seed_prompt,
            "evolved_prompt": current,
            "rounds": rounds,
            "evolution_log": evolution_log,
        }
        self._history.append(result)
        return result

    async def _generate_variations(self, prompt: str, task: str) -> list[str]:
        """Generate 3 variations of a prompt."""
        variation_prompt = (
            f"You are a prompt engineering expert.\n\n"
            f"Task: {task}\n\n"
            f"Current prompt:\n{prompt}\n\n"
            f"Generate 3 DIFFERENT improved variations of this prompt. "
            f"Each should try a different strategy:\n"
            f"1. More specific and structured\n"
            f"2. More creative and open-ended\n"
            f"3. More concise and direct\n\n"
            f"Output each variation separated by ===VARIATION==="
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": variation_prompt}],
                temperature=0.8,
                max_tokens=3000,
            )
            text = response.choices[0].message.content
            parts = text.split("===VARIATION===")
            variations = [p.strip() for p in parts if p.strip()]
            return variations[:3] if len(variations) >= 3 else variations + [prompt]
        except Exception as e:
            logger.error(f"Variation generation error: {e}")
            return [prompt]

    async def _test_variations(self, variations: list[str], task: str) -> list[dict]:
        """Test each variation on the task."""
        import asyncio
        results = []

        async def test_one(idx: int, var: str) -> dict:
            try:
                response = await self._llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": var},
                        {"role": "user", "content": task},
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                )
                return {
                    "index": idx,
                    "prompt": var,
                    "output": response.choices[0].message.content,
                }
            except Exception as e:
                return {"index": idx, "prompt": var, "output": f"Error: {e}"}

        tasks = [test_one(i, v) for i, v in enumerate(variations)]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def _rank_variations(self, results: list[dict], task: str) -> list[dict]:
        """Rank variations by quality."""
        import json

        outputs = "\n\n".join(
            f"[Variation {r['index']+1}]:\n{r['output'][:500]}"
            for r in results
        )

        rank_prompt = (
            f"Task: {task}\n\n"
            f"Three prompt variations produced these outputs:\n{outputs}\n\n"
            f"Score each 0-100 for quality, accuracy, and usefulness.\n"
            f"Output JSON: {{\"scores\": [score1, score2, score3]}}"
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": rank_prompt}],
                temperature=0.1,
                max_tokens=200,
            )
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            data = json.loads(content)
            scores = data.get("scores", [50] * len(results))

            for i, r in enumerate(results):
                r["score"] = scores[i] if i < len(scores) else 50

            return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
        except Exception as e:
            for r in results:
                r["score"] = 50
            return results

    async def _synthesize(self, ranked: list[dict], task: str) -> str:
        """Combine best elements into next-gen prompt."""
        best_prompts = "\n\n---\n\n".join(
            f"[Score: {r.get('score', '?')}]\n{r['prompt'][:500]}"
            for r in ranked[:2]
        )

        synth_prompt = (
            f"You are evolving an AI prompt.\n\n"
            f"Task: {task}\n\n"
            f"Top performing prompts:\n{best_prompts}\n\n"
            f"Create a SINGLE improved prompt that combines the best strategies "
            f"from the top performers. Output ONLY the new prompt text."
        )

        try:
            response = await self._llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": synth_prompt}],
                temperature=0.4,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return ranked[0]["prompt"] if ranked else ""

    @property
    def history(self) -> list[dict]:
        return self._history
