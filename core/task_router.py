"""
Task Router — routes tasks to appropriate agents with priority queuing.

Handles task assignment, load balancing, conflict resolution,
and dynamic group formation.
"""

from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("hydranet.router")


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    NORMAL = 5
    LOW = 8
    BACKGROUND = 10


@dataclass
class Task:
    task_id: str
    task_type: str
    payload: dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    assigned_to: str | None = None
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any = None
    error: str | None = None
    parent_task_id: str | None = None
    subtask_ids: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    timeout_seconds: float = 120.0


class TaskRouter:
    """Priority-based task routing with capability matching."""

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: dict[str, Task] = {}
        self._agent_capabilities: dict[str, list[str]] = {}
        self._agent_load: dict[str, int] = {}
        self._task_groups: dict[str, list[str]] = {}  # group_id -> [agent_ids]
        self._lock = asyncio.Lock()

    def register_agent(self, agent_id: str, capabilities: list[str]):
        self._agent_capabilities[agent_id] = capabilities
        self._agent_load[agent_id] = 0
        logger.info(f"Registered agent {agent_id} with capabilities: {capabilities}")

    def unregister_agent(self, agent_id: str):
        self._agent_capabilities.pop(agent_id, None)
        self._agent_load.pop(agent_id, None)

    async def submit_task(self, task: Task) -> str:
        async with self._lock:
            self._tasks[task.task_id] = task
            await self._queue.put((task.priority.value, task.created_at, task.task_id))
        logger.info(f"Task {task.task_id} submitted (type={task.task_type}, priority={task.priority.name})")
        return task.task_id

    def find_best_agent(self, task: Task) -> str | None:
        """Find the best agent for a task based on capabilities and load."""
        candidates = []
        for agent_id, caps in self._agent_capabilities.items():
            if not task.required_capabilities or all(
                c in caps for c in task.required_capabilities
            ):
                load = self._agent_load.get(agent_id, 0)
                candidates.append((load, agent_id))

        if not candidates:
            return None

        candidates.sort()
        return candidates[0][1]

    async def assign_next(self) -> tuple[Task, str] | None:
        """Pull next task from queue and assign to best agent."""
        if self._queue.empty():
            return None

        _, _, task_id = await self._queue.get()
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return None

        agent_id = self.find_best_agent(task)
        if not agent_id:
            # Re-queue if no agent available
            await self._queue.put((task.priority.value, task.created_at, task_id))
            return None

        task.status = TaskStatus.ASSIGNED
        task.assigned_to = agent_id
        task.started_at = time.time()
        self._agent_load[agent_id] = self._agent_load.get(agent_id, 0) + 1
        logger.info(f"Task {task_id} assigned to agent {agent_id}")
        return task, agent_id

    async def complete_task(self, task_id: str, result: Any = None, error: str | None = None):
        task = self._tasks.get(task_id)
        if not task:
            return

        if error:
            task.status = TaskStatus.FAILED
            task.error = error
        else:
            task.status = TaskStatus.COMPLETED
            task.result = result

        task.completed_at = time.time()

        if task.assigned_to:
            load = self._agent_load.get(task.assigned_to, 1)
            self._agent_load[task.assigned_to] = max(0, load - 1)

        logger.info(f"Task {task_id} {'completed' if not error else 'failed'}")

    def create_group(self, group_id: str, agent_ids: list[str]):
        self._task_groups[group_id] = agent_ids
        logger.info(f"Task group '{group_id}' created with agents: {agent_ids}")

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def get_pending_count(self) -> int:
        return self._queue.qsize()

    def get_agent_load(self) -> dict[str, int]:
        return dict(self._agent_load)
