"""
Database — SQLite storage for agent DNA, evolution history, and system state.
"""

from __future__ import annotations

import json
import logging

import aiosqlite

from config import DATABASE_PATH
from core.agent_dna import AgentDNA

logger = logging.getLogger("hydranet.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    purpose TEXT,
    dna_json TEXT NOT NULL,
    status TEXT DEFAULT 'idle',
    generation INTEGER DEFAULT 0,
    parent_id TEXT,
    created_at REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS evolution_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation INTEGER NOT NULL,
    timestamp REAL NOT NULL,
    event_type TEXT NOT NULL,
    agent_id TEXT,
    details TEXT
);

CREATE TABLE IF NOT EXISTS tracked_wallets (
    address TEXT PRIMARY KEY,
    label TEXT,
    tags TEXT,
    added_at REAL,
    last_checked REAL,
    alpha_score REAL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_evo_gen ON evolution_log(generation);
CREATE INDEX IF NOT EXISTS idx_wallets_score ON tracked_wallets(alpha_score DESC);
"""


async def init_database(db_path: str = DATABASE_PATH):
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(SCHEMA)
        await db.commit()
    logger.info("Database initialized")


async def save_agent(dna: AgentDNA, db_path: str = DATABASE_PATH):
    import time
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT OR REPLACE INTO agents
               (agent_id, name, agent_type, purpose, dna_json, status, generation, parent_id, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                dna.agent_id,
                dna.name,
                dna.agent_type,
                dna.purpose,
                dna.to_json(),
                dna.status.value,
                dna.generation,
                dna.parent_id,
                dna.metrics.created_at,
                time.time(),
            ),
        )
        await db.commit()


async def load_agents(db_path: str = DATABASE_PATH) -> list[AgentDNA]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT dna_json FROM agents WHERE status != 'dead'") as cursor:
            rows = await cursor.fetchall()
            return [AgentDNA.from_json(row["dna_json"]) for row in rows]


async def log_evolution(generation: int, event_type: str, agent_id: str = None, details: dict = None, db_path: str = DATABASE_PATH):
    import time
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            "INSERT INTO evolution_log (generation, timestamp, event_type, agent_id, details) VALUES (?, ?, ?, ?, ?)",
            (generation, time.time(), event_type, agent_id, json.dumps(details) if details else None),
        )
        await db.commit()


async def save_wallet(address: str, label: str = None, tags: list[str] = None, alpha_score: float = 0, db_path: str = DATABASE_PATH):
    import time
    async with aiosqlite.connect(db_path) as db:
        await db.execute(
            """INSERT OR REPLACE INTO tracked_wallets (address, label, tags, added_at, last_checked, alpha_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (address, label, json.dumps(tags or []), time.time(), time.time(), alpha_score),
        )
        await db.commit()


async def get_tracked_wallets(limit: int = 100, db_path: str = DATABASE_PATH) -> list[dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tracked_wallets ORDER BY alpha_score DESC LIMIT ?", (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
