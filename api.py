"""
FastAPI dashboard — HTTP API for monitoring and controlling HydraNet.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("hydranet.api")

app = FastAPI(
    title="HydraNet API",
    description="Multi-LLM Battle System — 3 AI enter, 1 AI leaves",
    version="0.2.0",
)

# These get injected at startup from main.py
_coordinator = None
_evaluator = None
_generator = None
_executor = None
_arena = None
_evolver = None


def set_components(coordinator, evaluator, generator, executor, arena=None, evolver=None):
    global _coordinator, _evaluator, _generator, _executor, _arena, _evolver
    _coordinator = coordinator
    _evaluator = evaluator
    _generator = generator
    _executor = executor
    _arena = arena
    _evolver = evolver


# ─── Status ──────────────────────────────────────────

@app.get("/status")
async def system_status():
    if not _coordinator:
        raise HTTPException(503, "System not initialized")
    return _coordinator.get_system_status()


@app.get("/agents")
async def list_agents():
    if not _coordinator:
        raise HTTPException(503, "System not initialized")
    return [dna.to_dict() for dna in _coordinator.get_all_dna()]


@app.get("/agents/{agent_id}")
async def get_agent(agent_id: str):
    if not _coordinator:
        raise HTTPException(503, "System not initialized")
    dna_list = _coordinator.get_all_dna()
    for dna in dna_list:
        if dna.agent_id == agent_id:
            return dna.to_dict()
    raise HTTPException(404, "Agent not found")


@app.delete("/agents/{agent_id}")
async def kill_agent(agent_id: str):
    if not _coordinator:
        raise HTTPException(503, "System not initialized")
    await _coordinator.kill_agent(agent_id)
    return {"status": "killed", "agent_id": agent_id}


# ─── Evolution ───────────────────────────────────────

@app.get("/evolution/leaderboard")
async def leaderboard():
    if not _evaluator:
        raise HTTPException(503, "System not initialized")
    return _evaluator.get_leaderboard()


@app.post("/evolution/cycle")
async def trigger_evolution():
    if not _evaluator:
        raise HTTPException(503, "System not initialized")
    report = await _evaluator.run_cycle()
    return report


@app.post("/evolution/generate")
async def generate_agent():
    if not _generator:
        raise HTTPException(503, "System not initialized")
    dna = await _generator.generate()
    if dna:
        return {"status": "generated", "agent": dna.to_dict()}
    return {"status": "no_agent_needed"}


# ─── Tasks ───────────────────────────────────────────

class TaskRequest(BaseModel):
    task_type: str
    payload: dict[str, Any] = {}
    capabilities: list[str] = []


@app.post("/tasks")
async def submit_task(req: TaskRequest):
    if not _coordinator:
        raise HTTPException(503, "System not initialized")
    task_id = await _coordinator.submit_task(
        task_type=req.task_type,
        payload=req.payload,
        capabilities=req.capabilities,
    )
    return {"task_id": task_id}


# ─── Execution ───────────────────────────────────────

@app.get("/trades")
async def get_trades():
    if not _executor:
        raise HTTPException(503, "System not initialized")
    return {
        "open": _executor.get_open_trades(),
        "history": _executor.get_trade_history(),
        "total_pnl": _executor.get_total_pnl(),
    }


@app.get("/alerts")
async def get_alerts():
    if not _executor:
        raise HTTPException(503, "System not initialized")
    return _executor.get_alerts()


# ─── Battle Arena ───────────────────────────────────

class BattleRequest(BaseModel):
    prompt: str
    evolve: bool = True


@app.post("/battle")
async def start_battle(req: BattleRequest):
    if not _arena:
        raise HTTPException(503, "Battle arena not initialized")
    result = await _arena.battle(req.prompt, evolve=req.evolve)
    return result.to_dict()


@app.get("/leaderboard")
async def ai_leaderboard():
    if not _arena:
        raise HTTPException(503, "Battle arena not initialized")
    return _arena.leaderboard


@app.get("/history")
async def battle_history():
    if not _arena:
        raise HTTPException(503, "Battle arena not initialized")
    return _arena.history


class EvolveRequest(BaseModel):
    seed_prompt: str
    task_description: str
    rounds: int = 3


@app.post("/evolve")
async def evolve_prompt(req: EvolveRequest):
    if not _evolver:
        raise HTTPException(503, "Evolver not initialized")
    result = await _evolver.evolve(req.seed_prompt, req.task_description, req.rounds)
    return result
