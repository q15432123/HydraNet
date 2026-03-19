"""
Training Loop — trains and improves agent decision models.

This is NOT traditional ML training with gradient descent.
HydraNet uses LLM-based agents — "training" means:
  1. Evaluate agent prompts against labeled data
  2. Score prompt effectiveness
  3. Mutate/improve prompts based on error analysis
  4. Repeat (evolutionary prompt optimization)

I/O:
  INPUT:  Labeled dataset + current agent prompts
  OUTPUT: Improved prompts + evaluation report

This is essentially "prompt evolution through empirical testing."
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from pipeline.dataset import LabeledSample

logger = logging.getLogger("hydranet.pipeline.training")

ERROR_ANALYSIS_PROMPT = """You are analyzing errors in an AI agent's decision-making.

Agent purpose: {purpose}
Agent prompt: {prompt}

The agent made these INCORRECT predictions:
{errors}

The agent made these CORRECT predictions:
{correct}

Analyze:
1. What patterns does the agent miss?
2. What false positives does it generate?
3. What specific changes to the prompt would improve accuracy?

Output JSON:
{{
  "error_patterns": ["pattern1", "pattern2"],
  "false_positive_causes": ["cause1", "cause2"],
  "suggested_prompt_changes": ["change1", "change2"],
  "improved_prompt": "the full improved prompt text"
}}
"""


class TrainingLoop:
    """Evolutionary training loop for LLM-based agents."""

    def __init__(self):
        self.llm = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._training_history: list[dict] = []

    async def evaluate_agent(
        self,
        agent_prompt: str,
        test_samples: list[LabeledSample],
        purpose: str = "",
    ) -> dict:
        """
        Run agent prompt against labeled test data and measure accuracy.

        Returns:
          {accuracy, precision, recall, f1, correct, incorrect, latency_avg_ms}
        """
        correct = []
        incorrect = []
        total_latency = 0.0

        for sample in test_samples:
            start = time.time()
            try:
                response = await self.llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": agent_prompt},
                        {"role": "user", "content": json.dumps(sample.features)},
                    ],
                    temperature=0.1,
                    max_tokens=200,
                )
                prediction = response.choices[0].message.content.strip().lower()
                elapsed = (time.time() - start) * 1000

                total_latency += elapsed

                # Check if prediction matches label
                is_correct = sample.label.lower() in prediction
                entry = {
                    "sample_id": sample.sample_id,
                    "features": sample.features,
                    "label": sample.label,
                    "prediction": prediction,
                    "latency_ms": elapsed,
                }

                if is_correct:
                    correct.append(entry)
                else:
                    incorrect.append(entry)

            except Exception as e:
                logger.error(f"Eval error for {sample.sample_id}: {e}")
                incorrect.append({
                    "sample_id": sample.sample_id,
                    "label": sample.label,
                    "error": str(e),
                })

        total = len(correct) + len(incorrect)
        accuracy = len(correct) / max(1, total)
        avg_latency = total_latency / max(1, total)

        result = {
            "accuracy": round(accuracy, 4),
            "total_samples": total,
            "correct_count": len(correct),
            "incorrect_count": len(incorrect),
            "avg_latency_ms": round(avg_latency, 1),
            "correct_samples": correct[:5],  # top 5 for analysis
            "incorrect_samples": incorrect[:5],
        }

        self._training_history.append({
            "timestamp": time.time(),
            "result": result,
        })

        logger.info(
            f"Evaluation: accuracy={accuracy:.1%} "
            f"({len(correct)}/{total}) "
            f"avg_latency={avg_latency:.0f}ms"
        )
        return result

    async def improve_prompt(
        self,
        current_prompt: str,
        eval_result: dict,
        purpose: str = "",
    ) -> str | None:
        """
        Analyze errors and generate an improved prompt.

        This is the "training step" — instead of updating weights,
        we update the prompt text based on empirical error analysis.
        """
        errors = json.dumps(eval_result.get("incorrect_samples", [])[:10], indent=2)
        correct = json.dumps(eval_result.get("correct_samples", [])[:5], indent=2)

        prompt = ERROR_ANALYSIS_PROMPT.format(
            purpose=purpose,
            prompt=current_prompt[:2000],
            errors=errors,
            correct=correct,
        )

        try:
            response = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=3000,
            )
            content = response.choices[0].message.content

            # Parse JSON response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            analysis = json.loads(content)

            improved = analysis.get("improved_prompt")
            if improved:
                logger.info(f"Prompt improved. Changes: {analysis.get('suggested_prompt_changes', [])}")
                return improved

        except Exception as e:
            logger.error(f"Prompt improvement failed: {e}")

        return None

    async def train_cycle(
        self,
        agent_prompt: str,
        train_data: list[LabeledSample],
        test_data: list[LabeledSample],
        purpose: str = "",
        max_iterations: int = 3,
    ) -> dict:
        """
        Full training cycle: evaluate → analyze errors → improve → repeat.

        Returns final evaluation results and the improved prompt.
        """
        current_prompt = agent_prompt
        best_accuracy = 0.0
        best_prompt = agent_prompt

        for i in range(max_iterations):
            logger.info(f"Training iteration {i+1}/{max_iterations}")

            # Evaluate on test set
            result = await self.evaluate_agent(current_prompt, test_data, purpose)

            if result["accuracy"] > best_accuracy:
                best_accuracy = result["accuracy"]
                best_prompt = current_prompt

            # If accuracy is high enough, stop early
            if result["accuracy"] >= 0.9:
                logger.info(f"Early stop: accuracy {result['accuracy']:.1%} >= 90%")
                break

            # Improve prompt based on errors
            improved = await self.improve_prompt(current_prompt, result, purpose)
            if improved:
                current_prompt = improved
            else:
                break

        return {
            "final_accuracy": best_accuracy,
            "iterations": i + 1,
            "best_prompt": best_prompt,
            "history": self._training_history[-max_iterations:],
        }

    @property
    def cost_estimate(self) -> dict:
        """Rough cost estimate based on training history."""
        total_samples = sum(
            h["result"]["total_samples"] for h in self._training_history
        )
        # gpt-4o-mini ~$0.15/1M input tokens, rough estimate 500 tokens/sample
        estimated_cost = total_samples * 500 * 0.15 / 1_000_000
        return {
            "total_evaluations": len(self._training_history),
            "total_samples_processed": total_samples,
            "estimated_cost_usd": round(estimated_cost, 4),
        }
