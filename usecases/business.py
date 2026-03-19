"""
Use Case 2: Business Analysis Battle — 3 AIs analyze your market.

Before HydraNet: One AI's opinion. Might be hallucinated.
After HydraNet:  3 perspectives, cross-validated, evolved insight.
"""

BUSINESS_BATTLES = [
    {
        "prompt": "Analyze the TAM/SAM/SOM for an AI-powered crypto trading bot targeting retail traders",
        "difficulty": "Strategic",
        "tags": ["market-sizing", "crypto", "fintech"],
    },
    {
        "prompt": "Compare the business models of Notion, Obsidian, and Linear. Which model is most defensible?",
        "difficulty": "Analytical",
        "tags": ["saas", "business-model", "competitive-analysis"],
    },
    {
        "prompt": "Design a go-to-market strategy for a developer tool that helps debug production issues using AI",
        "difficulty": "Strategic",
        "tags": ["gtm", "devtools", "ai"],
    },
]

BEFORE_AFTER = """
┌─────────────────────────────────────────────────────────────┐
│                 BUSINESS ANALYSIS BATTLE                    │
├────────────────────────┬────────────────────────────────────┤
│     BEFORE HydraNet    │        AFTER HydraNet              │
├────────────────────────┼────────────────────────────────────┤
│ Ask one AI for analysis│ 3 AIs analyze independently        │
│ Get one perspective    │ Each challenges the others' logic  │
│ Blind spots galore     │ Blind spots get exposed            │
│ Hallucinated numbers   │ Cross-validated data points        │
│ No devil's advocate    │ Built-in contrarian thinking       │
│                        │                                    │
│ Confidence: "trust me" │ Confidence: validated by 3 models  │
│ Depth: surface level   │ Depth: multi-angle deep dive       │
└────────────────────────┴────────────────────────────────────┘
"""
