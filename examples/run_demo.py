"""
HydraNet Demo — shows the system in action without live data.

Run: python examples/run_demo.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.mock_data import (
    MOCK_WALLETS, MOCK_CLUSTERS, MOCK_SIGNALS,
    MOCK_EVOLUTION_LOG, MOCK_TRADE_RESULTS,
)


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}")


def print_section(text: str):
    print(f"\n--- {text} ---")


async def demo():
    print_header("HydraNet — Self-Evolving Multi-Agent Intelligence")
    print("On-chain wallet intelligence & alpha detection system\n")

    # 1. Wallet tracking
    print_section("WALLET SCANNER")
    print(f"Tracking {len(MOCK_WALLETS)} high-value wallets:\n")
    for w in MOCK_WALLETS:
        print(f"  [{w['alpha_score']:3d}] {w['address'][:16]}... | {w['label']}")
        print(f"        Balance: {w['balance_sol']} SOL | Win rate: {w['win_rate']*100:.0f}% | Avg ROI: {w['avg_roi']}x")

    # 2. Cluster analysis
    print_section("CLUSTER ANALYSIS")
    print(f"Identified {len(MOCK_CLUSTERS)} wallet clusters:\n")
    for c in MOCK_CLUSTERS:
        print(f"  Cluster: {c['cluster_id']} | Type: {c['entity_type']} | Confidence: {c['confidence']:.0%}")
        print(f"  Wallets: {len(c['wallets'])} | Total: {c['total_sol']} SOL | Shared: {', '.join(c['shared_tokens'])}")
        print()

    # 3. Alpha signals
    print_section("ALPHA SIGNALS")
    for s in MOCK_SIGNALS:
        icon = "🟢" if s['risk_level'] in ('low', 'medium') else "🔴"
        print(f"  {icon} [{s['signal_type']}] {s['token_name']}")
        print(f"     Confidence: {s['confidence']:.0%} | Potential: {s['potential_roi']} | Risk: {s['risk_level']}")
        print(f"     {s['reasoning']}")
        print()

    # 4. Evolution log
    print_section("EVOLUTION LOG")
    for e in MOCK_EVOLUTION_LOG:
        gen = e['generation']
        event = e['event']
        if event == "system_boot":
            print(f"  Gen {gen}: BOOT — Spawned {', '.join(e['agents_spawned'])}")
        elif event == "evolution_cycle":
            print(f"  Gen {gen}: EVOLVE — Killed: {len(e['killed'])} | Replicated: {len(e['replicated'])} | Best: {e['best_score']:.3f}")
        elif event == "agent_spawned":
            print(f"  Gen {gen}: SPAWN — {e['new_agent']} ({e['reasoning']})")

    # 5. Performance summary
    print_section("PERFORMANCE SUMMARY (24h)")
    r = MOCK_TRADE_RESULTS
    print(f"""
  Wallets tracked:      {r['wallets_tracked']:,}
  Clusters identified:  {r['clusters_identified']}
  Signals generated:    {r['total_signals']}
  Trades simulated:     {r['trades_executed']}
  Win rate:             {r['win_rate']*100:.0f}%
  Simulated ROI:        +{r['total_pnl_pct']:.1f}%
  Total PnL:            {r['total_pnl_sol']:.1f} SOL

  Active agents:        {r['active_agents']}
  Agents spawned:       {r['agents_spawned']}
  Agents killed:        {r['agents_killed']}
  Generations:          {r['total_generations']}

  Best trade:  {r['best_trade']['token']} {r['best_trade']['roi']} ({r['best_trade']['hold_time']})
  Worst trade: {r['worst_trade']['token']} {r['worst_trade']['roi']} ({r['worst_trade']['hold_time']})
""")

    print_header("System Architecture")
    print("""
  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
  │ Scanner │───→│ Cluster │───→│  Alpha  │───→│ Execution│
  │  Agent  │    │  Agent  │    │  Agent  │    │  Layer   │
  └────┬────┘    └────┬────┘    └────┬────┘    └─────┬────┘
       │              │              │               │
       └──────────────┴──────────────┴───────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Evolution Engine  │
                    │  Kill · Replicate  │
                    │  Mutate · Spawn    │
                    └───────────────────┘
""")


if __name__ == "__main__":
    asyncio.run(demo())
