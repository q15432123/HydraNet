"""
HydraNet — Self-Evolving Multi-Agent Intelligence System

Entry point: boots the coordinator, spawns initial agents,
initializes the multi-head controller, starts evolution engine,
and serves the dashboard + API.
"""

import asyncio
import logging
import signal
import uvicorn

from config import LOG_LEVEL
from core.coordinator import Coordinator
from core.evaluator import EvolutionEngine
from core.agent_generator import AgentGenerator
from execution.action_executor import ActionExecutor
from pipeline.ingestion import IngestionPipeline
from pipeline.evaluation import MetricsCollector
from heads.controller import HeadController
from heads.market_head import MarketHead
from heads.trading_head import TradingHead
from heads.risk_head import RiskHead
from heads.onchain_head import OnChainHead
from database.db import init_database
from agents.wallet_tracker import WalletTrackerAgent, create_wallet_tracker_dna
from agents.cluster_analyzer import ClusterAnalyzerAgent, create_cluster_analyzer_dna
from agents.pattern_detector import PatternDetectorAgent, create_pattern_detector_dna
from agents.trade_advisor import TradeAdvisorAgent, create_trade_advisor_dna
from battle.arena import BattleArena, Combatant
from battle.prompt_evolver import PromptEvolver

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

    # Core systems
    coordinator = Coordinator()
    await coordinator.start()

    evaluator = EvolutionEngine(coordinator)
    generator = AgentGenerator(coordinator)
    executor = ActionExecutor()
    metrics = MetricsCollector()

    # Battle Arena
    arena = BattleArena()
    arena.add_combatant(Combatant(
        name="GPT-4o", model="gpt-4o", provider="openai",
        system_prompt="You are GPT-4o, a highly capable AI. Give precise, well-structured answers.",
        temperature=0.7,
    ))
    arena.add_combatant(Combatant(
        name="Claude", model="claude-sonnet", provider="anthropic",
        system_prompt="You are Claude, an AI that values clarity and correctness. Think step by step.",
        temperature=0.5,
    ))
    arena.add_combatant(Combatant(
        name="Gemini", model="gemini-pro", provider="google",
        system_prompt="You are Gemini, a creative AI. Explore unconventional approaches.",
        temperature=0.9,
    ))
    evolver = PromptEvolver()
    logger.info("Battle Arena initialized (3 combatants)")

    # Data pipeline
    pipeline = IngestionPipeline()
    await pipeline.start()
    logger.info("Ingestion pipeline started")

    # Multi-head controller
    head_controller = HeadController()
    head_controller.register_head(MarketHead(weight=1.0))
    head_controller.register_head(TradingHead(weight=1.5))
    head_controller.register_head(RiskHead(weight=2.0))
    head_controller.register_head(OnChainHead(weight=1.2))
    logger.info("Multi-head controller initialized (4 heads)")

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
    logger.info(f"System online: {status['active_agents']} agents + 4 heads active")
    for a in status["agents"]:
        logger.info(f"  Agent: {a['name']} ({a['type']}) [{a['status']}]")
    for h in head_controller.get_head_stats():
        logger.info(f"  Head:  {h['name']} (weight={h['weight']})")

    return {
        "coordinator": coordinator,
        "evaluator": evaluator,
        "generator": generator,
        "executor": executor,
        "pipeline": pipeline,
        "head_controller": head_controller,
        "metrics": metrics,
        "arena": arena,
        "evolver": evolver,
    }


async def run_server(components: dict):
    """Start the combined API + Dashboard server."""
    from api import app, set_components
    from dashboard.app import DASHBOARD_HTML
    from fastapi.responses import HTMLResponse

    set_components(
        components["coordinator"],
        components["evaluator"],
        components["generator"],
        components["executor"],
        components["arena"],
        components["evolver"],
    )

    # Mount dashboard
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        return DASHBOARD_HTML

    # Head controller endpoints
    head_ctrl = components["head_controller"]
    pipeline = components["pipeline"]
    metrics = components["metrics"]

    @app.get("/heads")
    async def get_heads():
        return head_ctrl.get_head_stats()

    @app.get("/heads/decisions")
    async def get_head_decisions():
        return head_ctrl.get_decision_history()

    @app.get("/pipeline/stats")
    async def get_pipeline_stats():
        return pipeline.stats

    @app.get("/metrics")
    async def get_metrics():
        return metrics.full_report()

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main():
    components = await bootstrap()

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
            pass

    # Run server
    api_task = asyncio.create_task(run_server(components))

    logger.info("HydraNet is running — 3 AI enter, 1 AI leaves")
    logger.info("Dashboard:  http://localhost:8000")
    logger.info("Battle:     POST http://localhost:8000/battle")
    logger.info("Leaderboard: http://localhost:8000/leaderboard")
    logger.info("Evolve:     POST http://localhost:8000/evolve")
    logger.info("API:        http://localhost:8000/status")

    try:
        await shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Shutting down...")
        await components["evaluator"].stop()
        await components["coordinator"].stop()
        await components["pipeline"].stop()
        api_task.cancel()
        logger.info("HydraNet stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
