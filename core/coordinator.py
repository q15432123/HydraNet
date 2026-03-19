"""
Coordinator — orchestrates all agents, manages lifecycle and routing.

The brain of HydraNet: starts/stops agents, routes tasks,
handles agent groups, and triggers evolution cycles.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from core.agent_dna import AgentDNA, AgentStatus
from core.agent_runtime import AgentRuntime
from core.message_bus import MessageBus, Message, MessageType
from core.task_router import TaskRouter, Task, TaskPriority
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from memory.history import HistoryLogger

from config import MAX_AGENTS

logger = logging.getLogger("hydranet.coordinator")


class Coordinator:
    """Central coordinator for the HydraNet multi-agent system."""

    def __init__(self):
        self.bus = MessageBus()
        self.router = TaskRouter()
        self.stm = ShortTermMemory()
        self.ltm = LongTermMemory()
        self.history = HistoryLogger()

        self._agents: dict[str, AgentRuntime] = {}
        self._dna_registry: dict[str, AgentDNA] = {}
        self._running = False

    @property
    def agent_count(self) -> int:
        return len(self._agents)

    def get_agent(self, agent_id: str) -> AgentRuntime | None:
        return self._agents.get(agent_id)

    def get_all_dna(self) -> list[AgentDNA]:
        return list(self._dna_registry.values())

    def get_active_agents(self) -> list[AgentDNA]:
        return [
            dna for dna in self._dna_registry.values()
            if dna.status == AgentStatus.RUNNING
        ]

    async def register_agent(self, agent: AgentRuntime) -> str:
        """Register and start an agent."""
        if self.agent_count >= MAX_AGENTS:
            logger.warning(f"Max agents ({MAX_AGENTS}) reached, cannot register {agent.dna.name}")
            return ""

        self._agents[agent.agent_id] = agent
        self._dna_registry[agent.agent_id] = agent.dna
        await agent.start()

        await self.history.log(
            agent_id=agent.agent_id,
            event_type="agent_registered",
            payload={"name": agent.dna.name, "type": agent.dna.agent_type},
        )

        logger.info(f"Agent registered: {agent.dna.name} ({agent.agent_id})")
        return agent.agent_id

    async def kill_agent(self, agent_id: str):
        """Stop and remove an agent."""
        agent = self._agents.pop(agent_id, None)
        if agent:
            await agent.kill()
            dna = self._dna_registry.get(agent_id)
            if dna:
                dna.status = AgentStatus.DEAD

            await self.history.log(
                agent_id=agent_id,
                event_type="agent_killed",
            )
            logger.info(f"Agent killed: {agent_id}")

    async def submit_task(
        self,
        task_type: str,
        payload: dict,
        priority: TaskPriority = TaskPriority.NORMAL,
        capabilities: list[str] | None = None,
    ) -> str:
        """Submit a task to be routed to an appropriate agent."""
        import uuid
        task = Task(
            task_id=str(uuid.uuid4())[:12],
            task_type=task_type,
            payload=payload,
            priority=priority,
            required_capabilities=capabilities or [],
        )
        task_id = await self.router.submit_task(task)

        # Try to assign immediately
        result = await self.router.assign_next()
        if result:
            task, agent_id = result
            agent = self._agents.get(agent_id)
            if agent:
                await self.bus.publish(Message(
                    sender_id="coordinator",
                    msg_type=MessageType.TASK,
                    channel="task_dispatch",
                    payload=task.payload,
                    target_id=agent_id,
                ))

        return task_id

    async def broadcast(self, channel: str, payload: dict):
        """Broadcast a message to all agents on a channel."""
        await self.bus.publish(Message(
            sender_id="coordinator",
            msg_type=MessageType.EVENT,
            channel=channel,
            payload=payload,
        ))

    async def start(self):
        """Initialize the coordinator."""
        self._running = True
        await self.history.init()
        logger.info("Coordinator started")

    async def stop(self):
        """Stop all agents and shutdown."""
        self._running = False
        for agent_id in list(self._agents.keys()):
            agent = self._agents[agent_id]
            await agent.stop()
        self._agents.clear()
        logger.info("Coordinator stopped")

    def get_system_status(self) -> dict:
        """Get full system status snapshot."""
        agents_status = []
        for dna in self._dna_registry.values():
            agents_status.append({
                "id": dna.agent_id,
                "name": dna.name,
                "type": dna.agent_type,
                "status": dna.status.value,
                "generation": dna.generation,
                "score": round(dna.metrics.composite_score, 3),
                "runs": dna.metrics.total_runs,
                "success_rate": round(dna.metrics.success_rate, 3),
            })

        return {
            "total_agents": self.agent_count,
            "active_agents": len(self.get_active_agents()),
            "pending_tasks": self.router.get_pending_count(),
            "agents": agents_status,
            "memory_entries": self.ltm.count(),
        }
