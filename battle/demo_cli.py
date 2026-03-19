"""
HydraNet Battle Demo — watch 3 AIs fight in your terminal.

Run: python battle/demo_cli.py

No API key needed — uses mock battles to show the full flow.
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Colors ──────────────────────────────────────────

R = "\033[91m"  # red
G = "\033[92m"  # green
B = "\033[94m"  # blue
Y = "\033[93m"  # yellow
C = "\033[96m"  # cyan
M = "\033[95m"  # magenta
W = "\033[97m"  # white
D = "\033[90m"  # dim
RESET = "\033[0m"
BOLD = "\033[1m"


def banner():
    print(f"""
{M}{BOLD}╔═══════════════════════════════════════════════════════╗
║                                                       ║
║     ██╗  ██╗██╗   ██╗██████╗ ██████╗  █████╗         ║
║     ██║  ██║╚██╗ ██╔╝██╔══██╗██╔══██╗██╔══██╗        ║
║     ███████║ ╚████╔╝ ██║  ██║██████╔╝███████║        ║
║     ██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══██║        ║
║     ██║  ██║   ██║   ██████╔╝██║  ██║██║  ██║        ║
║     ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝        ║
║                                                       ║
║          3 AI enter. 1 AI leaves.                     ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝{RESET}
""")


def phase(num, title):
    print(f"\n{Y}{BOLD}  PHASE {num}: {title}{RESET}")
    print(f"  {'─' * 48}")


def ai_says(name, color, text, delay=0.02):
    print(f"\n  {color}{BOLD}[{name}]{RESET}")
    for line in text.split("\n"):
        print(f"  {D}│{RESET} {line}")
        time.sleep(delay)


def score_bar(name, score, color):
    filled = int(score / 100 * 30)
    bar = f"{'█' * filled}{'░' * (30 - filled)}"
    print(f"  {color}{name:15s}{RESET} {bar} {BOLD}{score}{RESET}/100")


# ─── Mock Battle Data ────────────────────────────────

MOCK_PROMPT = "Write a Python function to find the longest palindromic substring."

MOCK_RESPONSES = {
    "GPT-4o": '''def longest_palindrome(s: str) -> str:
    """Expand around center approach — O(n²) time, O(1) space."""
    if not s:
        return ""
    start, max_len = 0, 1
    for i in range(len(s)):
        for l, r in [(i, i), (i, i+1)]:  # odd & even
            while l >= 0 and r < len(s) and s[l] == s[r]:
                if r - l + 1 > max_len:
                    start, max_len = l, r - l + 1
                l -= 1
                r += 1
    return s[start:start + max_len]''',

    "Claude": '''def longest_palindrome(s: str) -> str:
    """Manacher's algorithm — O(n) time."""
    t = '#' + '#'.join(s) + '#'
    n = len(t)
    p = [0] * n
    c = r = 0
    for i in range(n):
        mirror = 2 * c - i
        if i < r:
            p[i] = min(r - i, p[mirror])
        while i + p[i] + 1 < n and i - p[i] - 1 >= 0 and t[i+p[i]+1] == t[i-p[i]-1]:
            p[i] += 1
        if i + p[i] > r:
            c, r = i, i + p[i]
    max_len, center = max((v, i) for i, v in enumerate(p))
    start = (center - max_len) // 2
    return s[start:start + max_len]''',

    "Gemini": '''def longest_palindrome(s: str) -> str:
    """DP approach — O(n²) time and space."""
    n = len(s)
    if n < 2:
        return s
    dp = [[False] * n for _ in range(n)]
    start, max_len = 0, 1
    for i in range(n):
        dp[i][i] = True
    for i in range(n - 1):
        if s[i] == s[i+1]:
            dp[i][i+1] = True
            start, max_len = i, 2
    for length in range(3, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and dp[i+1][j-1]:
                dp[i][j] = True
                start, max_len = i, length
    return s[start:start + max_len]''',
}

MOCK_CRITIQUES = {
    "GPT-4o": {
        "Claude": "Manacher's is optimal O(n) but harder to read and maintain. Overkill for most use cases.",
        "Gemini": "DP approach wastes O(n²) space unnecessarily. The expand-around-center method is simpler and equally fast.",
    },
    "Claude": {
        "GPT-4o": "Clean and readable, but O(n²) worst case. For large strings, this will be slow.",
        "Gemini": "Standard DP — correct but wasteful memory. Neither optimal nor elegant.",
    },
    "Gemini": {
        "GPT-4o": "Good readability but the nested loop with two starting points is slightly tricky to follow.",
        "Claude": "Manacher's is theoretically optimal but the implementation is cryptic. Real-world code favors clarity.",
    },
}

MOCK_SCORES = {"GPT-4o": 82, "Claude": 88, "Gemini": 75}

MOCK_EVOLVED = '''def longest_palindrome(s: str) -> str:
    """
    Optimal solution combining clarity and performance.
    Expand-around-center with early termination.
    O(n²) worst case but fast in practice, O(1) space.
    """
    if len(s) < 2:
        return s

    start = end = 0

    def expand(l: int, r: int) -> tuple[int, int]:
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1
            r += 1
        return l + 1, r - 1

    for i in range(len(s)):
        # Early termination: can't beat current best
        if (len(s) - i) * 2 - 1 <= end - start:
            break

        # Check odd and even palindromes
        l1, r1 = expand(i, i)
        l2, r2 = expand(i, i + 1)

        if r1 - l1 > end - start:
            start, end = l1, r1
        if r2 - l2 > end - start:
            start, end = l2, r2

    return s[start:end + 1]'''


# ─── Demo Flow ───────────────────────────────────────

async def demo():
    banner()

    print(f"  {W}{BOLD}BATTLE PROMPT:{RESET}")
    print(f"  {C}\"{MOCK_PROMPT}\"{RESET}")
    await asyncio.sleep(1)

    # Phase 1
    phase(1, "GENERATE")
    print(f"  {D}3 AIs generating answers independently...{RESET}")
    await asyncio.sleep(0.5)

    ai_says("GPT-4o", R, MOCK_RESPONSES["GPT-4o"])
    await asyncio.sleep(0.3)
    ai_says("Claude", B, MOCK_RESPONSES["Claude"])
    await asyncio.sleep(0.3)
    ai_says("Gemini", G, MOCK_RESPONSES["Gemini"])

    # Phase 2
    phase(2, "CRITIQUE")
    print(f"  {D}Each AI attacks the others...{RESET}")
    await asyncio.sleep(0.5)

    for attacker, targets in MOCK_CRITIQUES.items():
        color = {"GPT-4o": R, "Claude": B, "Gemini": G}[attacker]
        for target, critique in targets.items():
            print(f"\n  {color}{attacker}{RESET} → {target}: {D}{critique}{RESET}")
            await asyncio.sleep(0.2)

    # Phase 3
    phase(3, "JUDGE")
    print(f"  {D}Impartial AI judge scoring all responses...{RESET}")
    await asyncio.sleep(0.8)
    print()

    for name in ["Gemini", "GPT-4o", "Claude"]:
        color = {"GPT-4o": R, "Claude": B, "Gemini": G}[name]
        score_bar(name, MOCK_SCORES[name], color)
        await asyncio.sleep(0.3)

    winner = max(MOCK_SCORES, key=MOCK_SCORES.get)
    print(f"\n  {Y}{BOLD}  WINNER: {winner} (score: {MOCK_SCORES[winner]}){RESET}")

    # Phase 4
    phase(4, "EVOLVE")
    print(f"  {D}Combining best elements from all 3 responses...{RESET}")
    await asyncio.sleep(0.5)
    ai_says("HydraNet (Evolved)", M, MOCK_EVOLVED)

    # Summary
    print(f"\n{M}{BOLD}╔═══════════════════════════════════════════════════════╗")
    print(f"║  BATTLE COMPLETE                                      ║")
    print(f"╠═══════════════════════════════════════════════════════╣")
    print(f"║  Winner:    Claude (88/100)                           ║")
    print(f"║  Runner-up: GPT-4o (82/100)                           ║")
    print(f"║  Evolved answer is strictly better than all 3         ║")
    print(f"║                                                       ║")
    print(f"║  The evolved answer adds:                             ║")
    print(f"║    + Early termination optimization                   ║")
    print(f"║    + Clean helper function (expand)                   ║")
    print(f"║    + O(1) space (from GPT approach)                   ║")
    print(f"║    + Practical speed (addresses Claude's critique)    ║")
    print(f"╚═══════════════════════════════════════════════════════╝{RESET}")

    print(f"\n  {D}This is HydraNet. 3 AI enter. 1 AI leaves.{RESET}")
    print(f"  {D}The evolved answer is always better.{RESET}\n")


if __name__ == "__main__":
    asyncio.run(demo())
