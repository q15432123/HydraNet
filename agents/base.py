"""
Base Agent — abstract foundation for all specialized agents.

Provides the standard interface that all HydraNet agents implement.
"""

from __future__ import annotations

import logging
from typing import Any

from core.agent_runtime import AgentRuntime
from core.agent_dna import AgentDNA
from core.message_bus import MessageBus, Message, MessageType
from core.task_router import TaskRouter
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.history import HistoryLogger

logger = logging.getLogger("hydranet.agent")


class BaseAgent(AgentRuntime):
    """Base class for all specialized agents."""

    def __init__(
        self,
        dna: AgentDNA,
        bus: MessageBus,
        router: TaskRouter,
        stm: ShortTermMemory,
        ltm: LongTermMemory,
        history: HistoryLogger,
    ):
        super().__init__(dna, bus, router)
        self.stm = stm
        self.ltm = ltm
        self.history = history

    async def execute_task(self, payload: dict) -> Any:
        """Override in subclasses with specific logic."""
        await self.history.log(
            agent_id=self.agent_id,
            event_type="task_start",
            payload=payload,
        )
        result = await self._process(payload)
        await self.history.log(
            agent_id=self.agent_id,
            event_type="task_complete",
            payload=payload,
            result=result,
        )
        return result

    async def _process(self, payload: dict) -> Any:
        """Implement in subclasses."""
        raise NotImplementedError

    async def remember(self, key: str, content: str, metadata: dict | None = None):
        """Store in both short-term and long-term memory."""
        self.stm.set(f"{self.agent_id}:{key}", content)
        self.ltm.store(
            doc_id=f"{self.agent_id}:{key}",
            content=content,
            metadata={**(metadata or {}), "agent_id": self.agent_id},
        )

    async def recall(self, query: str, n: int = 5) -> list[dict]:
        """Semantic search over long-term memory."""
        return self.ltm.query(query, n_results=n)

    async def emit_event(self, channel: str, data: dict):
        """Publish an event to the message bus."""
        await self.bus.publish(Message(
            sender_id=self.agent_id,
            msg_type=MessageType.EVENT,
            channel=channel,
            payload=data,
        ))

    async def delegate(self, task_type: str, payload: dict, capabilities: list[str] | None = None):
        """Create a subtask and submit to the router."""
        from core.task_router import Task, TaskPriority
        import uuid
        task = Task(
            task_id=str(uuid.uuid4())[:12],
            task_type=task_type,
            payload=payload,
            required_capabilities=capabilities or [],
        )
        await self.router.submit_task(task)
        return task.task_id
