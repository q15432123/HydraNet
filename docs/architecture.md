# HydraNet Architecture

## How I Built a Self-Evolving AI Agent System

HydraNet is an autonomous multi-agent system that generates, evaluates, and evolves its own AI agents to find alpha opportunities on the Solana blockchain.

## System Overview

```
Scanner → Cluster → Alpha → Execution → Evaluation → Mutation
```

### The Pipeline

1. **Scanner Agents** monitor on-chain wallet activity in real-time
2. **Cluster Agents** group related wallets into entities (funds, bots, insiders)
3. **Alpha Agents** detect profitable patterns from cluster behavior
4. **Execution Layer** triggers alerts and simulated trades
5. **Evolution Engine** scores all agents, kills underperformers, replicates winners

## Agent DNA

Every agent in HydraNet carries a "DNA" — a self-contained blueprint:

```python
AgentDNA(
    name="WalletTracker",
    purpose="Monitor wallet activity for alpha signals",
    agent_type="scanner",
    input_sources=["wallet_events"],
    decision_prompt="You are a Solana wallet analyst...",
    output_actions=["emit_event", "store_memory"],
    parameters={"scan_interval": 30, "min_tx_value": 1.0},
    metrics=PerformanceMetrics(accuracy=0.85, success_rate=0.78),
)
```

Agents are **storable**, **cloneable**, and **mutable**.

## Evolution Cycle

Every 5 minutes, the Evolution Engine:

1. **Scores** all active agents (accuracy × profitability × success rate × latency)
2. **Kills** agents scoring below 0.3 (after 10+ runs)
3. **Replicates** agents scoring above 0.8
4. **Mutates** random agents by rewriting their prompts via LLM

This creates Darwinian selection pressure — only the best strategies survive.

## Self-Spawning

The Agent Generator uses meta-reasoning:
- "What capability is missing?"
- "What agent would improve system ROI?"

It analyzes system gaps, generates new agent definitions, validates them, and deploys — all autonomously.

## Memory Architecture

| Layer | Purpose | Storage |
|-------|---------|---------|
| Short-term | Task context, active tracking | In-memory TTL cache |
| Long-term | Wallet knowledge, pattern history | ChromaDB vectors |
| Historical | Audit trail, debugging | SQLite |

## On-Chain Intelligence

Applied to Solana wallet intelligence:

- Track 1000+ wallets for transaction patterns
- Cluster related wallets (same entity, coordinated trading)
- Detect smart money entries before price moves
- Flag rug pulls and scam tokens
- Generate trade signals with risk management

## Tech Stack

- **Python 3.11+** — async-first architecture
- **FastAPI** — monitoring & control API
- **OpenAI GPT-4o-mini** — agent reasoning & prompt mutation
- **ChromaDB** — vector-based long-term memory
- **SQLite** — agent storage & history
- **Solana RPC + Helius** — on-chain data
- **DexScreener** — token pricing

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/status` | GET | System status snapshot |
| `/agents` | GET | List all agents |
| `/agents/{id}` | DELETE | Kill an agent |
| `/evolution/leaderboard` | GET | Agent rankings |
| `/evolution/cycle` | POST | Trigger evolution |
| `/evolution/generate` | POST | Spawn new agent |
| `/trades` | GET | Simulated trade history |
| `/alerts` | GET | Recent alerts |
