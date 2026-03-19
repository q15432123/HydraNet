"""
Use Case 3: Content Battle — 3 AIs write copy, best version wins.

Before HydraNet: Generic AI slop.
After HydraNet:  Battle-tested, critique-hardened killer content.
"""

CONTENT_BATTLES = [
    {
        "prompt": "Write a viral Twitter thread about why most startups fail at AI integration",
        "difficulty": "Creative",
        "tags": ["twitter", "startup", "viral"],
    },
    {
        "prompt": "Write a cold email to a VP of Engineering pitching an AI code review tool. Max 150 words.",
        "difficulty": "Persuasive",
        "tags": ["email", "sales", "b2b"],
    },
    {
        "prompt": "Write a Product Hunt launch description for an AI-powered design tool that generates UI from screenshots",
        "difficulty": "Marketing",
        "tags": ["product-hunt", "launch", "ai"],
    },
]

BEFORE_AFTER = """
┌─────────────────────────────────────────────────────────────┐
│                   CONTENT BATTLE                            │
├────────────────────────┬────────────────────────────────────┤
│     BEFORE HydraNet    │        AFTER HydraNet              │
├────────────────────────┼────────────────────────────────────┤
│ One AI writes copy     │ 3 AIs compete on same brief        │
│ Sounds like AI         │ Each rips apart the others' hooks  │
│ Generic and safe       │ Judge picks the most compelling    │
│ No iteration           │ Evolved version is strictly better │
│ "AI slop"              │ Battle-hardened killer content      │
│                        │                                    │
│ Engagement: meh        │ Engagement: significantly higher   │
│ Uniqueness: 2/10       │ Uniqueness: 8/10                   │
└────────────────────────┴────────────────────────────────────┘
"""
