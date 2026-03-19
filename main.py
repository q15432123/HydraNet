"""
HydraNet — Self-Evolving Multi-Agent Intelligence System

Entry point: boots the coordinator, spawns initial agents,
starts the evolution engine, and exposes the API.
"""

import asyncio
import logging
import sys
import signal
import uvicorn

from config import LOG_LEVEL
from core.coordinator import Coordinator
from core.evaluator import EvolutionEngine
from core.agent_generator import AgentGenerator
from execution.action_executor import ActionExecutor
from database.db import init_database
from agents.base import BaseAgent
from agents.wallet_tracker import WalletTrackerAgent, create_wallet_tracker_dna
from agents.cluster_analyzer import ClusterAnalyzerAgent, create_cluster_analyzer_dna
from agents.pattern_detector import PatternDetectorAgent, create_pattern_detector_dna
from agents.trade_advisor import TradeAdvisorAgent, create_trade_advisor_dna

# ─── Logging ─────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("hydranet")


# ─── Bootstrap ───────────────────────────────────────

async def bootstrap():
    """Initialize the full HydraNet system."""
    logger.info("=" * 60)
    logger.info("  HydraNet — Self-Evolving Multi-Agent Intelligence")
    logger.info("=" * 60)

    # Database
    await init_database()

    # Core
    coordinator = Coordinator()
    await coordinator.start()

    evaluator = EvolutionEngine(coordinator)
    generator = AgentGenerator(coordinator)
    executor = ActionExecutor()

    # Spawn initial agents
    agents_config = [
        (WalletTrackerAgent, create_wallet_tracker_dna()),
        (ClusterAnalyzerAgent, create_cluster_analyzer_dna()),
        (PatternDetectorAgent, create_pattern_detector_dna()),
        (TradeAdvisorAgent, create_trade_advisor_dna()),
    ]

    for agent_cls, dna in agents_config:
        agent = agent_cls(
            dna=dna,
            bus=coordinator.bus,
            router=coordinator.router,
            stm=coordinator.stm,
            ltm=coordinator.ltm,
            history=coordinator.history,
        )
        await coordinator.register_agent(agent)

    # Start evolution engine
    await evaluator.start()

    # Print status
    status = coordinator.get_system_status()
    logger.info(f"System online: {status['active_agents']} agents active")
    for a in status["agents"]:
        logger.info(f"  → {a['name']} ({a['type']}) [{a['status']}]")

    return coordinator, evaluator, generator, executor


async def run_api(coordinator, evaluator, generator, executor):
    """Start the FastAPI server."""
    from api import app, set_components
    set_components(coordinator, evaluator, generator, executor)

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    coordinator, evaluator, generator, executor = await bootstrap()

    # Handle shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def _shutdown():
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            pass

    # Run API server
    api_task = asyncio.create_task(run_api(coordinator, evaluator, generator, executor))

    logger.info("HydraNet is running. API at http://localhost:8000")
    logger.info("Endpoints: /status, /agents, /evolution/leaderboard, /trades, /alerts")

    try:
        await shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        await evaluator.stop()
        await coordinator.stop()
        api_task.cancel()
        logger.info("HydraNet stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
