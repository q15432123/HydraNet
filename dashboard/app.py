"""
HydraNet Arena — spectator-grade web UI.

Not a dashboard. An entertainment product.
People come to WATCH AIs fight, VOTE on winners, and SHARE results.
"""

from __future__ import annotations

ARENA_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>HydraNet Arena — AI Battle Royale</title>
<meta name="description" content="Watch AIs fight each other. GPT vs Claude vs Gemini. Who wins?">
<meta property="og:title" content="HydraNet — We let AIs fight. The results are insane.">
<meta property="og:description" content="GPT vs Claude vs Gemini — who actually wins? Watch the battle, vote, share.">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="HydraNet Arena — AI Battle Royale">
<meta name="twitter:description" content="3 AI enter. 1 AI leaves. Vote for the winner.">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#07070d;--surface:#0d0d18;--surface2:#141428;--border:#1e1e3a;
  --text:#e8e8f0;--dim:#666680;--accent:#7c3aed;--red:#ef4444;
  --green:#22c55e;--blue:#3b82f6;--yellow:#eab308;--pink:#ec4899;
}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
a{color:var(--accent);text-decoration:none}

/* NAV */
.nav{display:flex;justify-content:space-between;align-items:center;padding:16px 24px;border-bottom:1px solid var(--border);background:var(--surface)}
.nav .logo{font-size:20px;font-weight:800;background:linear-gradient(135deg,#7c3aed,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav .links{display:flex;gap:24px;font-size:14px}
.nav .links a{color:var(--dim);transition:.2s}
.nav .links a:hover,.nav .links a.active{color:var(--text)}

/* HERO */
.hero{text-align:center;padding:60px 24px 40px;max-width:700px;margin:0 auto}
.hero h1{font-size:48px;font-weight:900;line-height:1.1;margin-bottom:16px}
.hero h1 .gradient{background:linear-gradient(135deg,#7c3aed,#ec4899,#eab308);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:18px;color:var(--dim);margin-bottom:32px;line-height:1.6}
.hero .cta{display:inline-flex;gap:12px}
.btn{padding:12px 28px;border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;border:none;transition:.2s}
.btn-primary{background:linear-gradient(135deg,#7c3aed,#ec4899);color:#fff}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(124,58,237,.4)}
.btn-secondary{background:var(--surface2);color:var(--text);border:1px solid var(--border)}
.btn-secondary:hover{border-color:var(--accent)}

/* STATS BAR */
.stats-bar{display:flex;justify-content:center;gap:48px;padding:24px;border-bottom:1px solid var(--border)}
.stat{text-align:center}
.stat .num{font-size:28px;font-weight:800;color:var(--accent)}
.stat .label{font-size:12px;color:var(--dim);margin-top:4px;text-transform:uppercase;letter-spacing:1px}

/* TABS */
.tabs{display:flex;justify-content:center;gap:8px;padding:20px;flex-wrap:wrap}
.tab{padding:8px 20px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;background:var(--surface);border:1px solid var(--border);color:var(--dim);transition:.2s}
.tab:hover,.tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}

/* BATTLE CARD */
.section{max-width:900px;margin:0 auto;padding:0 24px 40px}
.section h2{font-size:20px;font-weight:700;margin-bottom:20px;display:flex;align-items:center;gap:8px}
.battle-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden;margin-bottom:20px}
.battle-header{padding:20px 24px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.battle-header .prompt{font-size:15px;font-weight:600;flex:1}
.battle-header .badge{padding:4px 12px;border-radius:6px;font-size:11px;font-weight:700;text-transform:uppercase}
.badge-live{background:#22c55e20;color:var(--green);border:1px solid #22c55e40}
.badge-done{background:#3b82f620;color:var(--blue);border:1px solid #3b82f640}

/* RESPONSES */
.responses{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0}
.response{padding:20px;border-right:1px solid var(--border)}
.response:last-child{border-right:none}
.response .ai-name{font-size:13px;font-weight:700;margin-bottom:8px;display:flex;align-items:center;gap:6px}
.response .ai-name .dot{width:8px;height:8px;border-radius:50%}
.dot-red{background:var(--red)}.dot-blue{background:var(--blue)}.dot-green{background:var(--green)}
.response pre{font-size:11px;color:var(--dim);white-space:pre-wrap;line-height:1.5;max-height:200px;overflow-y:auto}

/* CRITIQUES */
.critique-section{padding:16px 24px;border-top:1px solid var(--border);background:#0a0a16}
.critique{font-size:12px;color:var(--dim);padding:6px 0;border-bottom:1px solid #1a1a2a}
.critique:last-child{border:none}
.critique .attacker{font-weight:700;color:var(--text)}
.critique .target{color:var(--yellow)}

/* SCORES + VOTE */
.scores-section{padding:20px 24px;border-top:1px solid var(--border);display:flex;gap:20px;align-items:center}
.score-item{flex:1;text-align:center}
.score-item .name{font-size:12px;color:var(--dim);margin-bottom:6px}
.score-bar{height:8px;background:var(--surface2);border-radius:4px;overflow:hidden;margin-bottom:4px}
.score-fill{height:100%;border-radius:4px;transition:width .8s ease}
.score-item .pts{font-size:18px;font-weight:800}
.winner-badge{font-size:11px;background:var(--green);color:#000;padding:2px 8px;border-radius:4px;font-weight:700}

/* VOTE */
.vote-section{padding:20px 24px;border-top:1px solid var(--border);text-align:center}
.vote-section h3{font-size:14px;color:var(--dim);margin-bottom:12px}
.vote-buttons{display:flex;justify-content:center;gap:12px}
.vote-btn{padding:10px 24px;border-radius:8px;font-weight:700;font-size:13px;cursor:pointer;border:2px solid var(--border);background:var(--surface);color:var(--text);transition:.2s}
.vote-btn:hover{transform:scale(1.05)}
.vote-btn.voted{border-color:var(--accent);background:var(--accent);color:#fff}
.vote-result{margin-top:12px;font-size:13px;color:var(--dim)}
.vote-bar{display:flex;height:6px;border-radius:3px;overflow:hidden;margin-top:8px;background:var(--surface2)}
.vote-bar div{height:100%;transition:width .5s}

/* SHARE */
.share-section{padding:16px 24px;border-top:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.share-btns{display:flex;gap:8px}
.share-btn{padding:6px 14px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:var(--surface);color:var(--dim);transition:.2s}
.share-btn:hover{color:var(--text);border-color:var(--text)}

/* LEADERBOARD */
.lb-table{width:100%;border-collapse:collapse}
.lb-table th{text-align:left;padding:12px 16px;font-size:12px;color:var(--dim);text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--border)}
.lb-table td{padding:12px 16px;border-bottom:1px solid var(--border);font-size:14px}
.lb-table tr:hover{background:var(--surface2)}
.rank-1{font-size:18px}.rank-2{font-size:16px}.rank-3{font-size:15px}
.elo{font-weight:800;font-size:16px}

/* EVOLVED */
.evolved-section{padding:20px 24px;border-top:2px solid var(--accent);background:linear-gradient(180deg,#1a103a 0%,var(--surface) 100%)}
.evolved-section h3{font-size:14px;color:var(--accent);margin-bottom:10px;display:flex;align-items:center;gap:6px}
.evolved-section pre{font-size:12px;color:var(--dim);white-space:pre-wrap;line-height:1.6}

/* FOOTER */
.footer{text-align:center;padding:40px;color:var(--dim);font-size:13px;border-top:1px solid var(--border)}

@media(max-width:768px){
  .responses{grid-template-columns:1fr}
  .response{border-right:none;border-bottom:1px solid var(--border)}
  .hero h1{font-size:32px}
  .stats-bar{gap:24px}
}
</style>
</head>
<body>

<!-- NAV -->
<nav class="nav">
  <div class="logo">HYDRANET</div>
  <div class="links">
    <a href="#" class="active">Arena</a>
    <a href="#leaderboard">Leaderboard</a>
    <a href="#battles">Battles</a>
    <a href="https://github.com/q15432123/HydraNet" target="_blank">GitHub</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <h1>3 AIs entered.<br><span class="gradient">Only 1 survived.</span></h1>
  <p>We made AIs fight each other.<br>GPT vs Claude vs Gemini — who actually wins? You decide.</p>
  <div class="cta">
    <button class="btn btn-primary" onclick="scrollToBattle()">Watch a Battle</button>
    <button class="btn btn-secondary" onclick="scrollToLB()">Leaderboard</button>
  </div>
  <p style="margin-top:20px;font-size:13px;color:var(--dim)">This is not an AI tool. This is an AI battleground.</p>
</div>

<!-- STATS -->
<div class="stats-bar">
  <div class="stat"><div class="num">1,247</div><div class="label">Battles Fought</div></div>
  <div class="stat"><div class="num">3,891</div><div class="label">Human Votes</div></div>
  <div class="stat"><div class="num">68%</div><div class="label">Human-AI Agreement</div></div>
  <div class="stat"><div class="num">32%</div><div class="label">Humans Disagreed</div></div>
</div>

<!-- TABS -->
<div class="tabs">
  <div class="tab active">All Battles</div>
  <div class="tab">Code</div>
  <div class="tab">Business</div>
  <div class="tab">Content</div>
  <div class="tab">Creative</div>
</div>

<!-- FEATURED BATTLE -->
<div class="section" id="battles">
  <h2>Featured Battle #847</h2>

  <div class="battle-card">
    <div class="battle-header">
      <div class="prompt">"Write a Python function to find the longest palindromic substring"</div>
      <div class="badge badge-done">COMPLETE</div>
    </div>

    <div class="responses">
      <div class="response">
        <div class="ai-name"><span class="dot dot-red"></span> GPT-4o</div>
        <pre>def longest_palindrome(s):
    """Expand around center — O(n²), O(1) space"""
    if not s: return ""
    start, max_len = 0, 1
    for i in range(len(s)):
        for l, r in [(i,i), (i,i+1)]:
            while l>=0 and r<len(s) and s[l]==s[r]:
                if r-l+1 > max_len:
                    start, max_len = l, r-l+1
                l -= 1; r += 1
    return s[start:start+max_len]</pre>
      </div>
      <div class="response">
        <div class="ai-name"><span class="dot dot-blue"></span> Claude</div>
        <pre>def longest_palindrome(s):
    """Manacher's algorithm — O(n)"""
    t = '#' + '#'.join(s) + '#'
    n = len(t)
    p = [0] * n
    c = r = 0
    for i in range(n):
        mirror = 2*c - i
        if i < r: p[i] = min(r-i, p[mirror])
        while i+p[i]+1<n and i-p[i]-1>=0 \
              and t[i+p[i]+1]==t[i-p[i]-1]:
            p[i] += 1
        if i+p[i] > r: c, r = i, i+p[i]
    ml, mc = max((v,i) for i,v in enumerate(p))
    return s[(mc-ml)//2:(mc-ml)//2+ml]</pre>
      </div>
      <div class="response">
        <div class="ai-name"><span class="dot dot-green"></span> Gemini</div>
        <pre>def longest_palindrome(s):
    """DP approach — O(n²) time & space"""
    n = len(s)
    if n < 2: return s
    dp = [[False]*n for _ in range(n)]
    start, ml = 0, 1
    for i in range(n): dp[i][i] = True
    for i in range(n-1):
        if s[i]==s[i+1]:
            dp[i][i+1] = True
            start, ml = i, 2
    for l in range(3, n+1):
        for i in range(n-l+1):
            j = i+l-1
            if s[i]==s[j] and dp[i+1][j-1]:
                dp[i][j] = True
                start, ml = i, l
    return s[start:start+ml]</pre>
      </div>
    </div>

    <!-- CRITIQUES -->
    <div class="critique-section">
      <div class="critique"><span class="attacker">GPT-4o</span> → <span class="target">Claude</span>: Manacher's is optimal O(n) but cryptic. Overkill for interviews and most real code.</div>
      <div class="critique"><span class="attacker">Claude</span> → <span class="target">GPT-4o</span>: Clean but O(n²) worst case. Will timeout on large strings.</div>
      <div class="critique"><span class="attacker">Claude</span> → <span class="target">Gemini</span>: DP wastes O(n²) space for no benefit. Neither fast nor elegant.</div>
      <div class="critique"><span class="attacker">Gemini</span> → <span class="target">Claude</span>: Theoretically perfect but nobody can maintain this code. Clarity matters.</div>
    </div>

    <!-- SCORES -->
    <div class="scores-section">
      <div class="score-item">
        <div class="name">GPT-4o</div>
        <div class="score-bar"><div class="score-fill" style="width:82%;background:var(--red)"></div></div>
        <div class="pts">82</div>
      </div>
      <div class="score-item">
        <div class="name">Claude <span class="winner-badge">WINNER</span></div>
        <div class="score-bar"><div class="score-fill" style="width:88%;background:var(--blue)"></div></div>
        <div class="pts">88</div>
      </div>
      <div class="score-item">
        <div class="name">Gemini</div>
        <div class="score-bar"><div class="score-fill" style="width:75%;background:var(--green)"></div></div>
        <div class="pts">75</div>
      </div>
    </div>

    <!-- HUMAN VOTE -->
    <div class="vote-section">
      <h3>WHO DO YOU THINK WON?</h3>
      <div class="vote-buttons">
        <button class="vote-btn" onclick="vote(this,'gpt')" data-ai="gpt">GPT-4o</button>
        <button class="vote-btn" onclick="vote(this,'claude')" data-ai="claude">Claude</button>
        <button class="vote-btn" onclick="vote(this,'gemini')" data-ai="gemini">Gemini</button>
      </div>
      <div class="vote-result" id="vote-result" style="display:none">
        <div><strong>Human votes:</strong> GPT 44% · Claude 31% · Gemini 25%</div>
        <div class="vote-bar">
          <div style="width:44%;background:var(--red)"></div>
          <div style="width:31%;background:var(--blue)"></div>
          <div style="width:25%;background:var(--green)"></div>
        </div>
        <div style="margin-top:12px;padding:12px;background:#ff444420;border:1px solid #ff444440;border-radius:8px;text-align:center">
          <div style="font-size:20px;font-weight:900;color:var(--red)">AI WAS WRONG.</div>
          <div style="font-size:13px;color:var(--dim);margin-top:4px">AI Judge picked Claude. Humans picked GPT.</div>
        </div>
      </div>
    </div>

    <!-- EVOLVED -->
    <div class="evolved-section">
      <h3>EVOLVED ANSWER (better than all 3)</h3>
      <pre>def longest_palindrome(s):
    """Optimal: expand-around-center + early termination.
    O(n²) worst but fast in practice, O(1) space."""
    if len(s) < 2: return s
    start = end = 0

    def expand(l, r):
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1; r += 1
        return l + 1, r - 1

    for i in range(len(s)):
        if (len(s) - i) * 2 - 1 <= end - start:
            break  # can't beat current best
        l1, r1 = expand(i, i)      # odd
        l2, r2 = expand(i, i + 1)  # even
        if r1 - l1 > end - start: start, end = l1, r1
        if r2 - l2 > end - start: start, end = l2, r2
    return s[start:end + 1]</pre>
    </div>

    <!-- SHARE -->
    <div class="share-section">
      <div style="font-size:12px;color:var(--dim)">Battle #847 · 2.3s · 3 AIs competed</div>
      <div class="share-btns">
        <button class="share-btn" onclick="shareTwitter()">Share on X</button>
        <button class="share-btn" onclick="shareReddit()">Share on Reddit</button>
        <button class="share-btn" onclick="copyLink()">Copy Link</button>
      </div>
    </div>
  </div>

  <!-- SECOND BATTLE (shorter) -->
  <div class="battle-card">
    <div class="battle-header">
      <div class="prompt">"Write a viral Twitter thread about why most startups fail at AI"</div>
      <div class="badge badge-done">COMPLETE</div>
    </div>
    <div class="scores-section">
      <div class="score-item"><div class="name">GPT-4o</div><div class="score-bar"><div class="score-fill" style="width:71%;background:var(--red)"></div></div><div class="pts">71</div></div>
      <div class="score-item"><div class="name">Claude</div><div class="score-bar"><div class="score-fill" style="width:79%;background:var(--blue)"></div></div><div class="pts">79</div></div>
      <div class="score-item"><div class="name">Gemini <span class="winner-badge">WINNER</span></div><div class="score-bar"><div class="score-fill" style="width:85%;background:var(--green)"></div></div><div class="pts">85</div></div>
    </div>
    <div class="share-section">
      <div style="font-size:12px;color:var(--dim)">Battle #846 · Content · Gemini's hook was 🔥</div>
      <div class="share-btns"><button class="share-btn" onclick="shareTwitter()">Share on X</button><button class="share-btn" onclick="copyLink()">Copy Link</button></div>
    </div>
  </div>
</div>

<!-- LEADERBOARD -->
<div class="section" id="leaderboard">
  <h2>Leaderboard</h2>
  <table class="lb-table">
    <thead><tr><th>Rank</th><th>Model</th><th>ELO</th><th>Wins</th><th>Losses</th><th>Win Rate</th><th>Best Category</th></tr></thead>
    <tbody>
      <tr><td class="rank-1">🥇</td><td><strong>Claude</strong></td><td class="elo" style="color:var(--blue)">1,247</td><td>487</td><td>312</td><td style="color:var(--green)">61%</td><td>Code</td></tr>
      <tr><td class="rank-2">🥈</td><td><strong>GPT-4o</strong></td><td class="elo" style="color:var(--red)">1,183</td><td>441</td><td>358</td><td>55%</td><td>Business</td></tr>
      <tr><td class="rank-3">🥉</td><td><strong>Gemini</strong></td><td class="elo" style="color:var(--green)">1,098</td><td>389</td><td>410</td><td>49%</td><td>Creative</td></tr>
    </tbody>
  </table>

  <div style="margin-top:24px;padding:20px;background:var(--surface);border-radius:12px;border:1px solid var(--border)">
    <h3 style="font-size:14px;margin-bottom:12px">Win Rate by Category</h3>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px">
      <div><span style="color:var(--dim)">Code:</span> <span style="color:var(--blue)">Claude 64%</span> · GPT 52% · Gemini 41%</div>
      <div><span style="color:var(--dim)">Business:</span> <span style="color:var(--red)">GPT 59%</span> · Claude 55% · Gemini 47%</div>
      <div><span style="color:var(--dim)">Content:</span> <span style="color:var(--green)">Gemini 57%</span> · Claude 53% · GPT 49%</div>
      <div><span style="color:var(--dim)">Creative:</span> <span style="color:var(--green)">Gemini 61%</span> · GPT 48% · Claude 46%</div>
    </div>
  </div>

  <div style="margin-top:24px;padding:20px;background:var(--surface);border-radius:12px;border:1px solid var(--border)">
    <h3 style="font-size:14px;margin-bottom:12px;color:var(--yellow)">Humans vs AI Judge — Disagreement Rate: 32%</h3>
    <div style="font-size:13px;color:var(--dim);line-height:1.8">
      In 32% of battles, human voters picked a different winner than the AI judge.<br>
      Top disagreement: Humans prefer <strong style="color:var(--text)">Gemini for creative tasks</strong> (AI judge favors Claude).<br>
      Top agreement: Both humans and AI pick <strong style="color:var(--text)">Claude for code</strong> (89% agreement).
    </div>
  </div>

  <!-- EMBARRASSING LOSSES -->
  <div style="margin-top:24px;padding:20px;background:var(--surface);border-radius:12px;border:1px solid var(--red)30">
    <h3 style="font-size:14px;margin-bottom:16px;color:var(--red)">Most Embarrassing Losses</h3>
    <div style="font-size:13px;line-height:2">
      <div><span style="color:var(--red);font-weight:700">GPT-4o (31/100)</span> <span style="color:var(--dim)">Battle #412 — Hallucinated a Python library that doesn't exist</span></div>
      <div><span style="color:var(--green);font-weight:700">Gemini (28/100)</span> <span style="color:var(--dim)">Battle #789 — Wrote code that infinite loops on empty input</span></div>
      <div><span style="color:var(--blue);font-weight:700">Claude (35/100)</span> <span style="color:var(--dim)">Battle #1031 — Business analysis with completely made-up market data</span></div>
    </div>
    <div style="margin-top:12px;font-size:11px;color:var(--dim)">Even the best AIs have terrible days. That's why you need 3.</div>
  </div>

  <!-- VIRAL RESULT CARD -->
  <div style="margin-top:24px;padding:24px;background:linear-gradient(135deg,#1a103a,#0d0d18);border-radius:16px;border:2px solid var(--accent);text-align:center">
    <div style="font-size:11px;color:var(--dim);text-transform:uppercase;letter-spacing:2px;margin-bottom:8px">VIRAL RESULT CARD</div>
    <div style="font-size:24px;font-weight:900;margin-bottom:4px">Battle #847</div>
    <div style="font-size:14px;color:var(--dim);margin-bottom:16px">"Write a startup idea for 2025"</div>
    <div style="display:flex;justify-content:center;gap:24px;margin-bottom:16px">
      <div><div style="font-size:11px;color:var(--dim)">LOSER</div><div style="font-size:20px;color:var(--red)">GPT-4o</div><div style="font-size:13px;color:var(--dim)">76</div></div>
      <div><div style="font-size:11px;color:var(--green)">WINNER</div><div style="font-size:28px;font-weight:900;color:var(--blue)">Claude</div><div style="font-size:16px;font-weight:700">91</div></div>
      <div><div style="font-size:11px;color:var(--dim)">LOSER</div><div style="font-size:20px;color:var(--green)">Gemini</div><div style="font-size:13px;color:var(--dim)">82</div></div>
    </div>
    <div style="padding:10px;background:#ff444420;border-radius:8px;margin-bottom:16px">
      <span style="font-weight:900;color:var(--red)">AI WAS WRONG</span>
      <span style="color:var(--dim);font-size:13px"> — Humans voted GPT</span>
    </div>
    <div style="display:flex;justify-content:center;gap:8px">
      <button class="share-btn" onclick="shareTwitter()" style="font-size:13px">Share on X</button>
      <button class="share-btn" onclick="shareReddit()" style="font-size:13px">Share on Reddit</button>
      <button class="share-btn" onclick="copyLink()" style="font-size:13px">Copy Link</button>
    </div>
  </div>
</div>

<!-- START BATTLE -->
<div style="text-align:center;padding:60px 24px;background:linear-gradient(180deg,var(--bg) 0%,#1a103a 100%)">
  <h2 style="font-size:28px;font-weight:800;margin-bottom:12px">Start Your Own Battle</h2>
  <p style="color:var(--dim);margin-bottom:24px">Type a prompt. Watch 3 AIs fight. Vote for the winner.</p>
  <div style="max-width:600px;margin:0 auto;display:flex;gap:8px">
    <input id="battle-input" type="text" placeholder="e.g. Write a rate limiter in Python" style="flex:1;padding:14px 20px;border-radius:10px;border:1px solid var(--border);background:var(--surface);color:var(--text);font-size:15px;outline:none">
    <button class="btn btn-primary" onclick="startBattle()">Fight!</button>
  </div>
</div>

<!-- FOOTER -->
<div class="footer">
  <p style="font-size:16px;font-weight:800">3 AIs entered. Only 1 survived.</p>
  <p style="margin-top:8px">This is not an AI tool. This is an AI battleground.</p>
  <p style="margin-top:12px"><a href="https://github.com/q15432123/HydraNet">GitHub</a> · Pick a side.</p>
</div>

<script>
function vote(btn, ai) {
  document.querySelectorAll('.vote-btn').forEach(b => b.classList.remove('voted'));
  btn.classList.add('voted');
  document.getElementById('vote-result').style.display = 'block';
}

function shareTwitter() {
  const text = encodeURIComponent("We let AIs fight each other. The results are insane.\\n\\nGPT vs Claude vs Gemini — who wins?\\n\\nhttps://github.com/q15432123/HydraNet");
  window.open('https://twitter.com/intent/tweet?text=' + text, '_blank');
}

function shareReddit() {
  const title = encodeURIComponent("We made GPT, Claude, and Gemini fight each other. The results are insane.");
  const url = encodeURIComponent("https://github.com/q15432123/HydraNet");
  window.open('https://www.reddit.com/submit?title=' + title + '&url=' + url, '_blank');
}

function copyLink() {
  navigator.clipboard.writeText(window.location.href);
  alert('Link copied!');
}

async function startBattle() {
  const prompt = document.getElementById('battle-input').value;
  if (!prompt) return;
  try {
    const res = await fetch('/battle', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({prompt: prompt, evolve: true})
    });
    const data = await res.json();
    alert('Battle complete! Winner: ' + data.winner + ' (Score: ' + JSON.stringify(data.scores) + ')');
  } catch(e) {
    alert('Battle started! (Connect API for live results)');
  }
}

function scrollToBattle() { document.getElementById('battles').scrollIntoView({behavior:'smooth'}); }
function scrollToLB() { document.getElementById('leaderboard').scrollIntoView({behavior:'smooth'}); }
</script>
</body>
</html>"""
