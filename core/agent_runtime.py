"""
Agent Runtime — executes agent logic and manages lifecycle.

Each agent runs as an async task, processing messages and tasks
according to its DNA definition.
"""

from __future__ import annotations

import asyncio
import time
import logging
from typing import Any

from openai import AsyncOpenAI

from config import OPENAI_API_KEY
from core.agent_dna import AgentDNA, AgentStatus, PerformanceMetrics
from core.message_bus import MessageBus, Message, MessageType
from core.task_router import TaskRouter, Task

logger = logging.getLogger("hydranet.runtime")


class AgentRuntime:
    """Manages the execution lifecycle of an agent."""

    def __init__(
        self,
        dna: AgentDNA,
        bus: MessageBus,
        router: TaskRouter,
        llm_client: AsyncOpenAI | None = None,
    ):
        self.dna = dna
        self.bus = bus
        self.router = router
        self.llm = llm_client or AsyncOpenAI(api_key=OPENAI_API_KEY)
        self._task: asyncio.Task | None = None
        self._running = False
        self._context: dict[str, Any] = {}  # short-term memory

    @property
    def agent_id(self) -> str:
        return self.dna.agent_id

    async def start(self):
        if self._running:
            return
        self._running = True
        self.dna.status = AgentStatus.RUNNING
        self.bus.register_direct(self.agent_id, self._handle_message)
        for src in self.dna.input_sources:
            self.bus.subscribe(src, self.agent_id, self._handle_message)
        self.router.register_agent(self.agent_id, self.dna.tags)
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"Agent {self.dna.name} ({self.agent_id}) started")

    async def stop(self):
        self._running = False
        self.dna.status = AgentStatus.IDLE
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.bus.unregister_direct(self.agent_id)
        for src in self.dna.input_sources:
            self.bus.unsubscribe(src, self.agent_id)
        self.router.unregister_agent(self.agent_id)
        logger.info(f"Agent {self.dna.name} ({self.agent_id}) stopped")

    async def kill(self):
        await self.stop()
        self.dna.status = AgentStatus.DEAD
        logger.warning(f"Agent {self.dna.name} ({self.agent_id}) killed")

    async def _run_loop(self):
        """Main agent loop — process queued tasks periodically."""
        while self._running:
            try:
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break

    async def _handle_message(self, message: Message):
        """Process an incoming message."""
        start_time = time.time()
        self.dna.metrics.total_runs += 1
        self.dna.metrics.last_run_at = start_time

        try:
            if message.msg_type == MessageType.TASK:
                result = await self.execute_task(message.payload)
                self.dna.metrics.successful_runs += 1
                # Publish result
                await self.bus.publish(Message(
                    sender_id=self.agent_id,
                    msg_type=MessageType.RESULT,
                    channel=message.channel,
                    payload={"task_id": message.message_id, "result": result},
                    target_id=message.sender_id,
                ))
            elif message.msg_type == MessageType.EVENT:
                await self.handle_event(message.payload)
                self.dna.metrics.successful_runs += 1
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
        finally:
            elapsed = (time.time() - start_time) * 1000
            # Rolling average latency
            n = self.dna.metrics.total_runs
            prev = self.dna.metrics.latency_ms
            self.dna.metrics.latency_ms = prev + (elapsed - prev) / n

    async def execute_task(self, payload: dict) -> Any:
        """Override in subclasses. Default uses LLM with agent's decision prompt."""
        prompt = self.dna.decision_prompt
        if not prompt:
            return {"status": "no_decision_prompt"}

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": str(payload)},
        ]

        response = await self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.3,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    async def handle_event(self, payload: dict) -> None:
        """Override in subclasses for event-driven logic."""
        pass

    def update_accuracy(self, score: float):
        n = self.dna.metrics.total_runs or 1
        prev = self.dna.metrics.accuracy
        self.dna.metrics.accuracy = prev + (score - prev) / n

    def update_profitability(self, pnl: float):
        self.dna.metrics.profitability += pnl
