"""
Web Dashboard — real-time monitoring UI for HydraNet.

Serves a single-page dashboard at http://localhost:8000
showing live agent status, evolution, signals, and trades.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

dashboard_app = FastAPI(title="HydraNet Dashboard")

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HydraNet Dashboard</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'SF Mono', 'Fira Code', monospace;
    background: #0a0a0f;
    color: #e0e0e0;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    padding: 20px 30px;
    border-bottom: 1px solid #2a2a4a;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .header h1 {
    font-size: 24px;
    background: linear-gradient(90deg, #00d4ff, #7b2ff7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .header .status {
    display: flex;
    gap: 20px;
    font-size: 13px;
  }
  .header .status .dot {
    width: 8px; height: 8px;
    background: #00ff88;
    border-radius: 50%;
    display: inline-block;
    margin-right: 6px;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    padding: 20px;
    max-width: 1400px;
    margin: 0 auto;
  }
  .card {
    background: #12121f;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
  }
  .card h2 {
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #888;
    margin-bottom: 16px;
  }
  .card.full { grid-column: 1 / -1; }
  .metric {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
    border-bottom: 1px solid #1a1a2f;
  }
  .metric:last-child { border: none; }
  .metric .label { color: #888; }
  .metric .value { font-weight: bold; }
  .metric .value.green { color: #00ff88; }
  .metric .value.red { color: #ff4444; }
  .metric .value.blue { color: #00d4ff; }
  .agent-row {
    display: grid;
    grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
    padding: 10px 0;
    border-bottom: 1px solid #1a1a2f;
    font-size: 13px;
  }
  .agent-row.header-row { color: #666; font-weight: bold; }
  .agent-row .status-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
  }
  .status-running { background: #002211; color: #00ff88; }
  .status-dead { background: #220000; color: #ff4444; }
  .signal-item {
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 8px;
    background: #1a1a2f;
    border-left: 3px solid;
  }
  .signal-item.high { border-color: #ff4444; }
  .signal-item.medium { border-color: #ffaa00; }
  .signal-item.low { border-color: #00ff88; }
  .signal-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 6px;
  }
  .signal-header .type { font-weight: bold; font-size: 13px; }
  .signal-header .conf { color: #888; font-size: 12px; }
  .signal-body { font-size: 12px; color: #aaa; }
  .evolution-bar {
    display: flex;
    gap: 4px;
    margin-top: 8px;
  }
  .evo-block {
    flex: 1;
    height: 24px;
    border-radius: 3px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    font-weight: bold;
  }
  .evo-spawn { background: #002244; color: #00d4ff; }
  .evo-kill { background: #440000; color: #ff4444; }
  .evo-mutate { background: #332200; color: #ffaa00; }
  .evo-replicate { background: #003300; color: #00ff88; }
  .btn {
    padding: 8px 16px;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    background: #1a1a2f;
    color: #00d4ff;
    cursor: pointer;
    font-family: inherit;
    font-size: 12px;
    transition: all 0.2s;
  }
  .btn:hover { background: #2a2a4a; }
  .btn-row { display: flex; gap: 8px; margin-top: 12px; }
  #log {
    font-size: 11px;
    color: #666;
    max-height: 200px;
    overflow-y: auto;
    margin-top: 12px;
    padding: 10px;
    background: #0a0a12;
    border-radius: 6px;
  }
  #log .entry { padding: 2px 0; }
  #log .entry .ts { color: #444; }
</style>
</head>
<body>

<div class="header">
  <h1>HYDRANET</h1>
  <div class="status">
    <span><span class="dot"></span>System Online</span>
    <span id="agent-count">— agents</span>
    <span id="uptime">—</span>
  </div>
</div>

<div class="grid">

  <!-- System Metrics -->
  <div class="card">
    <h2>System Metrics</h2>
    <div class="metric"><span class="label">Active Agents</span><span class="value blue" id="m-agents">—</span></div>
    <div class="metric"><span class="label">Total Decisions</span><span class="value" id="m-decisions">—</span></div>
    <div class="metric"><span class="label">Wallets Tracked</span><span class="value" id="m-wallets">1,247</span></div>
    <div class="metric"><span class="label">Clusters Found</span><span class="value" id="m-clusters">89</span></div>
    <div class="metric"><span class="label">Signals (24h)</span><span class="value" id="m-signals">47</span></div>
    <div class="metric"><span class="label">Simulated ROI</span><span class="value green" id="m-roi">+18.3%</span></div>
    <div class="metric"><span class="label">Win Rate</span><span class="value green" id="m-winrate">68%</span></div>
    <div class="metric"><span class="label">Avg Latency</span><span class="value" id="m-latency">—</span></div>
  </div>

  <!-- Multi-Head Decisions -->
  <div class="card">
    <h2>Multi-Head Controller</h2>
    <div class="metric"><span class="label">Market Head</span><span class="value blue">ACTIVE</span></div>
    <div class="metric"><span class="label">Trading Head</span><span class="value blue">ACTIVE</span></div>
    <div class="metric"><span class="label">Risk Head</span><span class="value green">GUARDING</span></div>
    <div class="metric"><span class="label">On-Chain Head</span><span class="value blue">SCANNING</span></div>
    <div style="margin-top:16px; padding:12px; background:#1a1a2f; border-radius:8px;">
      <div style="font-size:11px; color:#666; margin-bottom:6px;">LAST FUSED DECISION</div>
      <div style="font-size:18px; font-weight:bold;" class="green" id="last-decision">BUY BONK</div>
      <div style="font-size:12px; color:#888; margin-top:4px;" id="decision-detail">conf=0.84 | 3/4 heads agree | risk approved</div>
    </div>
    <div class="btn-row">
      <button class="btn" onclick="triggerCycle()">Run Evolution</button>
      <button class="btn" onclick="triggerGenerate()">Spawn Agent</button>
    </div>
  </div>

  <!-- Agent List -->
  <div class="card full">
    <h2>Agent Registry</h2>
    <div class="agent-row header-row">
      <span>Name</span><span>Type</span><span>Score</span><span>Runs</span><span>Status</span>
    </div>
    <div id="agent-list">
      <div class="agent-row"><span>WalletTracker</span><span>scanner</span><span class="green">0.847</span><span>142</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row"><span>ClusterAnalyzer</span><span>analyzer</span><span class="green">0.812</span><span>89</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row"><span>PatternDetector</span><span>detector</span><span class="green">0.791</span><span>67</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row"><span>TradeAdvisor</span><span>advisor</span><span class="blue">0.734</span><span>45</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row"><span>WalletTracker_gen2</span><span>scanner</span><span class="green">0.823</span><span>31</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row"><span>LiquidityMonitor</span><span>scanner</span><span class="blue">0.612</span><span>18</span><span><span class="status-badge status-running">RUNNING</span></span></div>
      <div class="agent-row" style="opacity:0.5"><span>PatternDetector_mut2</span><span>detector</span><span class="red">0.218</span><span>22</span><span><span class="status-badge status-dead">KILLED</span></span></div>
    </div>
  </div>

  <!-- Signals -->
  <div class="card">
    <h2>Alpha Signals</h2>
    <div class="signal-item high">
      <div class="signal-header"><span class="type">SMART MONEY ENTRY</span><span class="conf">89%</span></div>
      <div class="signal-body">3 profitable wallets accumulated BONK in last 2h — potential +340%</div>
    </div>
    <div class="signal-item medium">
      <div class="signal-header"><span class="type">UNUSUAL VOLUME</span><span class="conf">72%</span></div>
      <div class="signal-body">WIF volume 12x above 7d avg, whale cluster accumulating</div>
    </div>
    <div class="signal-item high">
      <div class="signal-header"><span class="type">RUG WARNING</span><span class="conf">95%</span></div>
      <div class="signal-body">SCAMCOIN: dev holds 89% supply, LP unlocked, honeypot detected</div>
    </div>
    <div class="signal-item low">
      <div class="signal-header"><span class="type">ACCUMULATION</span><span class="conf">67%</span></div>
      <div class="signal-body">Fund cluster quietly buying JTO across 5 wallets</div>
    </div>
  </div>

  <!-- Evolution -->
  <div class="card">
    <h2>Evolution History</h2>
    <div class="metric"><span class="label">Generation</span><span class="value blue">12</span></div>
    <div class="metric"><span class="label">Agents Spawned</span><span class="value green">6</span></div>
    <div class="metric"><span class="label">Agents Killed</span><span class="value red">3</span></div>
    <div class="metric"><span class="label">Mutations</span><span class="value" style="color:#ffaa00">4</span></div>
    <div class="metric"><span class="label">Best Score</span><span class="value green">0.912</span></div>
    <div style="margin-top:12px; font-size:11px; color:#666;">EVOLUTION TIMELINE</div>
    <div class="evolution-bar">
      <div class="evo-block evo-spawn">+4</div>
      <div class="evo-block evo-replicate">+1</div>
      <div class="evo-block evo-mutate">~2</div>
      <div class="evo-block evo-spawn">+1</div>
      <div class="evo-block evo-kill">-1</div>
      <div class="evo-block evo-mutate">~1</div>
      <div class="evo-block evo-replicate">+1</div>
      <div class="evo-block evo-kill">-2</div>
      <div class="evo-block evo-mutate">~1</div>
      <div class="evo-block evo-spawn">+1</div>
    </div>
  </div>

  <!-- Architecture -->
  <div class="card full">
    <h2>Data Flow</h2>
    <pre style="font-size:12px; color:#888; line-height:1.8; overflow-x:auto;">
  Solana RPC ─┐                    ┌─ Market Head ──┐
  Helius API ─┼─→ Ingestion ─→ Normalize ─→ ├─ Trading Head ─┼─→ Controller ─→ Execution
  DexScreener ┘    Pipeline      Pipeline    ├─ Risk Head ────┘    (fuse)       (alerts/
                      │                      └─ OnChain Head               sim trades)
                      ▼
              Dataset Builder ─→ Train Loop ─→ Evaluate ─→ Evolution Engine
              (label + split)   (prompt opt)   (metrics)   (kill/spawn/mutate)
    </pre>
  </div>

  <!-- Live Log -->
  <div class="card full">
    <h2>System Log</h2>
    <div id="log">
      <div class="entry"><span class="ts">12:03:41</span> Agent WalletTracker scanning 1,247 wallets...</div>
      <div class="entry"><span class="ts">12:03:42</span> ClusterAnalyzer found 3 new wallet relationships</div>
      <div class="entry"><span class="ts">12:03:44</span> <span style="color:#ffaa00">SIGNAL: Smart money entry detected on BONK (conf=0.89)</span></div>
      <div class="entry"><span class="ts">12:03:45</span> Multi-head decision: BUY (3/4 heads agree, risk approved)</div>
      <div class="entry"><span class="ts">12:03:45</span> <span style="color:#00ff88">SIM TRADE: BUY BONK @ 0.0000234 (2.5 SOL)</span></div>
      <div class="entry"><span class="ts">12:03:48</span> <span style="color:#ff4444">WARNING: Rug pull detected — SCAMCOIN (conf=0.95)</span></div>
      <div class="entry"><span class="ts">12:03:50</span> Evolution cycle #12: killed 0, replicated 1, mutated 0</div>
      <div class="entry"><span class="ts">12:03:51</span> Agent WalletTracker_gen2 replicated (score=0.823)</div>
    </div>
  </div>
</div>

<script>
async function fetchStatus() {
  try {
    const res = await fetch('/status');
    const data = await res.json();
    document.getElementById('m-agents').textContent = data.active_agents;
    document.getElementById('agent-count').textContent = data.active_agents + ' agents';
  } catch(e) {}
}

async function triggerCycle() {
  try {
    const res = await fetch('/evolution/cycle', {method:'POST'});
    const data = await res.json();
    addLog('Evolution cycle triggered: ' + JSON.stringify(data).slice(0,100));
  } catch(e) { addLog('Evolution trigger failed'); }
}

async function triggerGenerate() {
  try {
    const res = await fetch('/evolution/generate', {method:'POST'});
    const data = await res.json();
    addLog('Agent generation: ' + data.status);
  } catch(e) { addLog('Generation failed'); }
}

function addLog(msg) {
  const log = document.getElementById('log');
  const now = new Date().toLocaleTimeString('en-US', {hour12:false});
  const entry = document.createElement('div');
  entry.className = 'entry';
  entry.innerHTML = '<span class="ts">' + now + '</span> ' + msg;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

setInterval(fetchStatus, 5000);
fetchStatus();
</script>
</body>
</html>"""


@dashboard_app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    return DASHBOARD_HTML
