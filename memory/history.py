"""
History Logger — structured event logs for reasoning and debugging.

Stores timestamped records of agent actions, decisions, and outcomes
in SQLite for queryable audit trails.
"""

from __future__ import annotations

import json
import time
import logging
from typing import Any

import aiosqlite

from config import DATABASE_PATH

logger = logging.getLogger("hydranet.history")

CREATE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS history_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    channel TEXT,
    payload TEXT,
    result TEXT,
    duration_ms REAL
)
"""

CREATE_HISTORY_INDEX = """
CREATE INDEX IF NOT EXISTS idx_history_agent ON history_log(agent_id, timestamp)
"""


class HistoryLogger:
    """Async history logger backed by SQLite."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self._db_path = db_path
        self._initialized = False

    async def init(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(CREATE_HISTORY_TABLE)
            await db.execute(CREATE_HISTORY_INDEX)
            await db.commit()
        self._initialized = True

    async def log(
        self,
        agent_id: str,
        event_type: str,
        channel: str | None = None,
        payload: Any = None,
        result: Any = None,
        duration_ms: float | None = None,
    ):
        if not self._initialized:
            await self.init()

        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """INSERT INTO history_log
                   (timestamp, agent_id, event_type, channel, payload, result, duration_ms)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(),
                    agent_id,
                    event_type,
                    channel,
                    json.dumps(payload) if payload else None,
                    json.dumps(result) if result else None,
                    duration_ms,
                ),
            )
            await db.commit()

    async def query(
        self,
        agent_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        since: float | None = None,
    ) -> list[dict]:
        if not self._initialized:
            await self.init()

        conditions = []
        params: list[Any] = []

        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if since:
            conditions.append("timestamp > ?")
            params.append(since)

        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"SELECT * FROM history_log {where} ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "id": r["id"],
                        "timestamp": r["timestamp"],
                        "agent_id": r["agent_id"],
                        "event_type": r["event_type"],
                        "channel": r["channel"],
                        "payload": json.loads(r["payload"]) if r["payload"] else None,
                        "result": json.loads(r["result"]) if r["result"] else None,
                        "duration_ms": r["duration_ms"],
                    }
                    for r in rows
                ]
