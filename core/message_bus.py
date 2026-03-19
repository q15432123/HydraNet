"""
Message Bus — inter-agent communication backbone.

Agents communicate through typed messages on named channels.
Supports pub/sub, direct messaging, and broadcast.
"""

from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Awaitable

logger = logging.getLogger("hydranet.bus")


class MessageType(str, Enum):
    TASK = "task"
    RESULT = "result"
    EVENT = "event"
    COMMAND = "command"
    HEARTBEAT = "heartbeat"


@dataclass
class Message:
    sender_id: str
    msg_type: MessageType
    channel: str
    payload: dict[str, Any]
    target_id: str | None = None  # None = broadcast on channel
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: f"msg-{int(time.time()*1000)}")
    priority: int = 5  # 1=highest, 10=lowest


MessageHandler = Callable[[Message], Awaitable[None]]


class MessageBus:
    """Async message bus with channel-based pub/sub."""

    def __init__(self):
        self._subscribers: dict[str, list[tuple[str, MessageHandler]]] = {}
        self._direct_handlers: dict[str, MessageHandler] = {}
        self._history: list[Message] = []
        self._max_history = 1000
        self._lock = asyncio.Lock()

    def subscribe(self, channel: str, agent_id: str, handler: MessageHandler):
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        self._subscribers[channel].append((agent_id, handler))
        logger.debug(f"Agent {agent_id} subscribed to [{channel}]")

    def unsubscribe(self, channel: str, agent_id: str):
        if channel in self._subscribers:
            self._subscribers[channel] = [
                (aid, h) for aid, h in self._subscribers[channel] if aid != agent_id
            ]

    def register_direct(self, agent_id: str, handler: MessageHandler):
        self._direct_handlers[agent_id] = handler

    def unregister_direct(self, agent_id: str):
        self._direct_handlers.pop(agent_id, None)

    async def publish(self, message: Message):
        async with self._lock:
            self._history.append(message)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        # Direct message
        if message.target_id and message.target_id in self._direct_handlers:
            try:
                await self._direct_handlers[message.target_id](message)
            except Exception as e:
                logger.error(f"Direct handler error for {message.target_id}: {e}")
            return

        # Channel broadcast
        handlers = self._subscribers.get(message.channel, [])
        tasks = []
        for agent_id, handler in handlers:
            if agent_id != message.sender_id:
                tasks.append(self._safe_call(handler, message, agent_id))
        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_call(self, handler: MessageHandler, msg: Message, agent_id: str):
        try:
            await handler(msg)
        except Exception as e:
            logger.error(f"Handler error for agent {agent_id}: {e}")

    def get_history(self, channel: str | None = None, limit: int = 50) -> list[Message]:
        msgs = self._history
        if channel:
            msgs = [m for m in msgs if m.channel == channel]
        return msgs[-limit:]
