"""
Mock data for demos and testing.

Simulates wallet activity, cluster data, and alpha signals
so the system can run without live blockchain data.
"""

MOCK_WALLETS = [
    {
        "address": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
        "label": "Smart Money #1",
        "alpha_score": 92,
        "tags": ["whale", "early-buyer", "profitable"],
        "balance_sol": 1847.3,
        "token_count": 23,
        "win_rate": 0.78,
        "avg_roi": 4.2,
    },
    {
        "address": "DfKxkT4Z28QqRqpN3TvHs7iL9u4V9mMbr2efQvzXwZoL",
        "label": "DEX Sniper Bot",
        "alpha_score": 87,
        "tags": ["bot", "sniper", "high-frequency"],
        "balance_sol": 342.1,
        "token_count": 8,
        "win_rate": 0.65,
        "avg_roi": 2.8,
    },
    {
        "address": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "label": "Fund Wallet A",
        "alpha_score": 85,
        "tags": ["fund", "accumulator", "insider"],
        "balance_sol": 12450.0,
        "token_count": 45,
        "win_rate": 0.71,
        "avg_roi": 3.5,
    },
    {
        "address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "label": "Cluster Node #7",
        "alpha_score": 73,
        "tags": ["cluster-a", "coordinated"],
        "balance_sol": 89.4,
        "token_count": 12,
        "win_rate": 0.58,
        "avg_roi": 1.9,
    },
]

MOCK_CLUSTERS = [
    {
        "cluster_id": "cluster_001",
        "entity_type": "fund",
        "confidence": 0.94,
        "wallets": [
            "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "HN7cABqLq46Es1jh92dQQisAq662SmxELLLsHHe4YWrH",
        ],
        "total_sol": 15200,
        "shared_tokens": ["BONK", "WIF", "JTO"],
        "coordination_score": 88,
    },
    {
        "cluster_id": "cluster_002",
        "entity_type": "bot_network",
        "confidence": 0.81,
        "wallets": [
            "DfKxkT4Z28QqRqpN3TvHs7iL9u4V9mMbr2efQvzXwZoL",
            "3Kzh9qAqVWQhEsfQE7czCoeGenb2Grjdha4C7cEsBxpN",
        ],
        "total_sol": 580,
        "shared_tokens": ["POPCAT", "MEW"],
        "coordination_score": 76,
    },
]

MOCK_SIGNALS = [
    {
        "signal_type": "smart_money_entry",
        "token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "token_name": "BONK",
        "confidence": 0.89,
        "wallets_involved": 3,
        "potential_roi": "+340%",
        "risk_level": "medium",
        "urgency": "high",
        "reasoning": "3 historically profitable wallets accumulated BONK in last 2h",
    },
    {
        "signal_type": "unusual_volume",
        "token": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
        "token_name": "WIF",
        "confidence": 0.72,
        "wallets_involved": 7,
        "potential_roi": "+180%",
        "risk_level": "high",
        "urgency": "medium",
        "reasoning": "Volume spike 12x above 7-day average, whale cluster accumulating",
    },
    {
        "signal_type": "rug_warning",
        "token": "FAKE1111111111111111111111111111111111111111",
        "token_name": "SCAMCOIN",
        "confidence": 0.95,
        "wallets_involved": 1,
        "potential_roi": "-100%",
        "risk_level": "critical",
        "urgency": "high",
        "reasoning": "Dev wallet holds 89% supply, LP unlocked, honeypot contract detected",
    },
]

MOCK_EVOLUTION_LOG = [
    {
        "generation": 1,
        "event": "system_boot",
        "agents_spawned": ["WalletTracker", "ClusterAnalyzer", "PatternDetector", "TradeAdvisor"],
        "total_agents": 4,
    },
    {
        "generation": 2,
        "event": "evolution_cycle",
        "killed": [],
        "replicated": ["WalletTracker"],
        "mutated": ["PatternDetector"],
        "best_score": 0.847,
    },
    {
        "generation": 3,
        "event": "agent_spawned",
        "new_agent": "LiquidityMonitor",
        "reasoning": "System detected gap in LP tracking capability",
    },
    {
        "generation": 5,
        "event": "evolution_cycle",
        "killed": ["PatternDetector_mut2"],
        "replicated": ["WalletTracker_gen2"],
        "mutated": [],
        "best_score": 0.912,
    },
]

MOCK_TRADE_RESULTS = {
    "total_signals": 47,
    "trades_executed": 31,
    "win_rate": 0.68,
    "total_pnl_sol": 18.7,
    "total_pnl_pct": 18.3,
    "best_trade": {
        "token": "BONK",
        "roi": "+340%",
        "hold_time": "4h 23m",
    },
    "worst_trade": {
        "token": "DEGEN",
        "roi": "-42%",
        "hold_time": "1h 07m",
    },
    "wallets_tracked": 1247,
    "clusters_identified": 89,
    "active_agents": 7,
    "agents_killed": 3,
    "agents_spawned": 6,
    "total_generations": 12,
}
