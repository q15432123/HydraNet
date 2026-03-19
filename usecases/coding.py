"""
Use Case 1: Code Battle — 3 AIs write code, best solution wins.

Before HydraNet: You get ONE answer. Hope it's good.
After HydraNet:  You get 3 answers + critiques + evolved solution.
"""

CODING_BATTLES = [
    {
        "prompt": "Write a Python function to find the longest palindromic substring",
        "difficulty": "Medium",
        "tags": ["string", "dynamic-programming"],
    },
    {
        "prompt": "Implement a rate limiter using the token bucket algorithm",
        "difficulty": "Hard",
        "tags": ["system-design", "concurrency"],
    },
    {
        "prompt": "Build a minimal JSON parser from scratch (no libraries)",
        "difficulty": "Hard",
        "tags": ["parsing", "recursion"],
    },
    {
        "prompt": "Write a function that detects cycles in a directed graph",
        "difficulty": "Medium",
        "tags": ["graph", "dfs"],
    },
    {
        "prompt": "Implement an LRU cache with O(1) get and put operations",
        "difficulty": "Medium",
        "tags": ["data-structure", "linked-list"],
    },
]

BEFORE_AFTER = """
┌─────────────────────────────────────────────────────────────┐
│                     CODE BATTLE                             │
├────────────────────────┬────────────────────────────────────┤
│     BEFORE HydraNet    │        AFTER HydraNet              │
├────────────────────────┼────────────────────────────────────┤
│ Ask ChatGPT            │ 3 AIs compete simultaneously       │
│ Get 1 answer           │ Each critiques the others          │
│ Hope it's correct      │ Judge scores on 4 criteria         │
│ No error checking      │ Evolved answer combines best parts │
│ No alternatives        │ You get THE optimal solution       │
│                        │                                    │
│ Accuracy: ~70%         │ Accuracy: ~95%                     │
│ Time: 1 prompt         │ Time: 1 prompt (parallel)          │
└────────────────────────┴────────────────────────────────────┘
"""
