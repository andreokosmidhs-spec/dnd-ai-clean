"""
Intent classifier — fast keyword/regex pre-pass over the player's action
text. Catches the canonical "you should have asked for X check" cases the
DM has historically missed (lure-and-sneak, deceive, intimidate with a
weapon, etc.) before the DM gets to auto-resolve.

When this fires, the lean_dm endpoint injects a HARD DIRECTIVE into the DM
prompt forcing the DM to narrate the beat without resolving the outcome
and end with a prompt for the appropriate check.

The patterns mirror the DM Reasoning Chart shown in the frontend
DMFeedbackButton modal so the chart, the classifier, and the LLM judge
all agree by design.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple


# Each entry: (check_type, list of (regex_pattern, weight) tuples).
# Weights are summed; the highest-scoring check wins. We use weights so
# strong cues (an explicit "I sneak past" beats a passing "moves quietly").
_PATTERNS: Dict[str, List[Tuple[str, int]]] = {
    "Stealth": [
        (r"\b(?:i\s+)?(?:try\s+to\s+)?(?:sneak|snuck|sneaking|sneak\s+(?:up|past|behind|in|out))\b", 3),
        (r"\b(?:i\s+)?(?:hide|hiding|conceal\s+myself|stay\s+(?:hidden|out\s+of\s+sight))\b", 3),
        (r"\b(?:tip[- ]?toe|creep|creeping|skulk|slip\s+(?:past|behind|by)|slither)\b", 3),
        (r"\bmove\s+(?:unseen|silently|quietly|without\s+being\s+(?:seen|noticed))\b", 3),
        (r"\bpretend\s+(?:not\s+to\s+(?:see|notice|look)|i\s+don'?t\s+see)\b", 3),
        (r"\b(?:lure|luring)\s+(?:them|him|her|the)\b", 2),  # lure → often paired w/ surprise → stealth
        (r"\bsurprise\s+(?:them|him|her|attack)\b", 2),
        (r"\bcrouch\s+(?:behind|down)\b", 2),
        (r"\bshadow\s+(?:them|him|her)\b", 2),
        (r"\btail\s+(?:them|him|her)\b", 2),
        (r"\bblend\s+into\s+(?:the\s+)?(?:crowd|shadows)\b", 2),
    ],
    "Deception": [
        (r"\b(?:i\s+)?(?:lie|lying)\s+(?:to|about)\b", 3),
        (r"\bbluff(?:ing)?\b", 3),
        (r"\bpretend\s+(?:to\s+be|that\s+i'?m|i'?m)\b", 3),
        (r"\bpose\s+as\b", 3),
        (r"\bdisguise\s+(?:myself|my\s+(?:voice|appearance))\b", 3),
        (r"\b(?:tell|told)\s+(?:them|him|her)\s+(?:i'?m|i\s+am|that\s+i)\b", 3),  # impersonation
        (r"\bclaim\s+to\s+be\b", 3),
        (r"\bact\s+(?:as\s+(?:if|though)|like)\b", 2),
        (r"\bfake\s+(?:my|a|an|the)\b", 2),
        (r"\bspin\s+(?:them|him|her|a\s+tale)\b", 2),
        (r"\b(?:i\s+)?fib\b", 2),
        (r"\bcover\s+(?:the\s+truth|my\s+(?:tracks|trail))\b", 2),
        (r"\bplay\s+(?:dumb|innocent)\b", 2),
        (r"\bmake\s+up\s+(?:a\s+)?story\b", 2),
    ],
    "Performance": [
        (r"\bperform\s+(?:for|to)\b", 3),
        (r"\bput\s+on\s+(?:a\s+)?(?:show|act|performance)\b", 3),
        (r"\bplay\s+(?:the\s+)?(?:lute|fiddle|harp|drum|flute)\b", 3),
        (r"\bsing\s+(?:a\s+song|to|for)\b", 3),
        (r"\b(?:i\s+)?(?:sing|sang)\b", 2),
        (r"\bdance\s+(?:for|to\s+distract)\b", 3),
        (r"\bdistract\s+(?:them|the\s+crowd|the\s+guards?)\s+(?:with\s+)?(?:music|a\s+song|dance|juggling)\b", 3),
        (r"\bdistract\s+(?:them|the\s+crowd|the\s+guards?)\b", 2),
        (r"\bjuggle\b", 3),
    ],
    "Intimidation": [
        (r"\b(?:i\s+)?threaten(?:ing)?\b", 3),
        (r"\bintimidat(?:e|ing)\b", 3),
        (r"\bmenace\s+(?:them|him|her)\b", 3),
        (r"\bdraw\s+(?:my|the)\s+(?:weapon|blade|sword|dagger|knife)\b", 3),
        (r"\b(?:press|put|hold)\s+(?:my|the)\s+(?:dagger|blade|knife|sword)\s+(?:to|against)\b", 3),
        (r"\braise\s+(?:my|the)\s+(?:weapon|fist|blade)\b", 2),
        (r"\bgrowl\b", 2),
        (r"\bsnarl\b", 2),
        (r"\bloom\s+over\b", 2),
        (r"\b(?:cold|hard)\s+stare\b", 2),
        (r"\bgrab\s+(?:them|him|her)\s+by\s+the\s+(?:collar|throat|neck)\b", 3),
        (r"\bpin\s+(?:them|him|her)\s+(?:against|with|down)\b", 3),
        (r"\bcorner\s+(?:them|him|her)\b", 2),
        (r"\bmake\s+(?:them|him|her)\s+(?:talk|spill)\b", 2),
    ],
    "Persuasion": [
        (r"\b(?:i\s+)?convince\b", 3),
        (r"\b(?:i\s+)?persuade\b", 3),
        (r"\bplead\s+with\b", 3),
        (r"\btalk\s+(?:them|him|her)\s+(?:into|down|out\s+of)\b", 3),
        (r"\breason\s+with\b", 2),
        (r"\bappeal\s+to\s+(?:their|his|her)\b", 2),
        (r"\bsweet[- ]?talk\b", 2),
        (r"\bcharm\s+(?:them|him|her)\b", 2),
        (r"\bask\s+politely\b", 1),
        (r"\bnegotiate\s+(?:with|a\s+price)\b", 2),
        (r"\bwin\s+(?:them|him|her)\s+over\b", 2),
    ],
    "Insight": [
        (r"\bread\s+(?:their|his|her)\s+(?:face|body\s+language|expression|eyes|tells?)\b", 3),
        (r"\bsense\s+(?:if|whether)\s+(?:they|he|she)\s+(?:is|are|'?s)\s+lying\b", 3),
        (r"\bgauge\s+(?:their|his|her)\s+(?:mood|honesty|reaction)\b", 2),
        (r"\bsee\s+if\s+(?:they|he|she)\s+(?:is|are|'?s)\s+(?:telling\s+the\s+truth|hiding\s+something)\b", 3),
        (r"\bcatch\s+(?:them|him|her)\s+lying\b", 3),
        (r"\bstudy\s+(?:their|his|her)\s+reaction\b", 2),
    ],
    "Athletics": [
        (r"\bclimb(?:ing)?\b", 3),
        (r"\bleap\s+(?:over|across)\b", 3),
        (r"\bjump\s+(?:over|across|up\s+to)\b", 3),
        (r"\bswim\s+across\b", 3),
        (r"\bbreak\s+(?:free|the\s+grapple|out)\b", 3),
        (r"\bforce\s+(?:open\s+)?the\s+door\b", 2),
        (r"\bsmash\s+(?:through|down)\b", 2),
        (r"\bhoist\s+(?:myself|them|him|her)\b", 2),
        (r"\bhaul\s+myself\s+up\b", 3),
        (r"\bpull\s+myself\s+up\b", 2),
        (r"\bscale\s+(?:the\s+)?wall\b", 3),
    ],
    "Acrobatics": [
        (r"\broll\s+(?:to\s+(?:the\s+)?side|under)\b", 3),
        (r"\bbackflip\b", 3),
        (r"\btumble\b", 3),
        (r"\bbalance\s+on\b", 3),
        (r"\bsqueeze\s+through\b", 2),
    ],
    "Perception": [
        (r"\bscan\s+(?:the\s+)?(?:area|room|crowd|surroundings)\b", 2),
        (r"\blisten\s+(?:carefully|for\s+sounds|for\s+(?:them|him|her))\b", 3),
        # Eavesdropping — overhearing conversation. The player wants to
        # catch the actual words, not just "be in earshot". Strong cue.
        (r"\b(?:eavesdrop|overhear|listen\s+(?:in|to|at)|press\s+(?:an\s+)?ear|ear\s+to\s+the\s+(?:door|wall|keyhole))\b", 3),
        (r"\b(?:try\s+to\s+)?(?:catch|hear|make\s+out)\s+(?:what|their|the)\s+(?:words|conversation|talk|whisper)\b", 3),
        (r"\bkeep\s+watch\b", 2),
        (r"\bwatch\s+(?:the\s+)?(?:crowd|street|alley|window|door)\b", 2),
        (r"\b(?:spot|notice|catch\s+sight\s+of)\b", 2),
    ],
    "Investigation": [
        (r"\bsearch\s+(?:the|through|for)\b", 3),
        (r"\bexamine\s+(?:the|carefully)\b", 3),
        (r"\binvestigate\b", 3),
        (r"\bstudy\s+the\s+(?:tracks|marks|inscription|symbols)\b", 3),
        (r"\blook\s+for\s+clues\b", 3),
        (r"\bpiece\s+together\b", 2),
        (r"\bdecipher\b", 3),
        (r"\bdecode\b", 3),
    ],
    "Sleight of Hand": [
        (r"\bpick\s+the\s+lock\b", 3),
        (r"\bpickpocket\b", 3),
        (r"\blift\s+(?:from|off)\s+(?:them|him|her)\b", 2),
        (r"\bswap\s+(?:the|out)\b", 2),
        (r"\bpalm\s+(?:the|a)\b", 2),
        (r"\bslip\s+(?:my|a)\s+hand\s+(?:into|over)\b", 2),
        (r"\bcut\s+(?:the\s+)?purse\b", 3),
    ],
}


# Compile patterns once at import time.
_COMPILED: Dict[str, List[Tuple[re.Pattern, int]]] = {
    check: [(re.compile(p, re.IGNORECASE), w) for p, w in patterns]
    for check, patterns in _PATTERNS.items()
}


def classify_player_intent(text: str, *, threshold: int = 3) -> Optional[Dict]:
    """Score the player's action against every known check pattern. Return
    the winning check + matched cue + confidence band, or None if no
    pattern hits the threshold (default: a single 3-weight cue, or
    multiple 2-weight cues).

    Compound actions: when the player chains two distinct intents (e.g.
    "I hide and listen to them" = Stealth + Perception), the second
    highest-scoring check is returned under `secondary_check` so the DM
    can demand BOTH rolls instead of only the strongest one.

    Returns:
        {
          "check_type": str,                # primary, e.g. "Stealth"
          "matched": str,                   # the substring that fired the rule
          "score": int,
          "confidence": "low"|"medium"|"high",
          "secondary_check": str | None,    # second-strongest check (>= threshold)
          "secondary_matched": str | None,
        }
        or None.
    """
    if not text or not text.strip():
        return None
    norm = text.strip().lower()
    # Score every check that meets the threshold so we can surface compound intents.
    scored: List[Tuple[str, int, str]] = []  # (check_type, score, matched)
    for check_type, compiled in _COMPILED.items():
        score = 0
        matches: List[str] = []
        for rx, weight in compiled:
            m = rx.search(norm)
            if m:
                score += weight
                matches.append(m.group(0))
        if score >= threshold:
            scored.append((check_type, score, matches[0] if matches else ""))
    if not scored:
        return None
    scored.sort(key=lambda x: x[1], reverse=True)
    primary = scored[0]
    secondary = scored[1] if len(scored) > 1 else None
    score = primary[1]
    if score >= 6:
        confidence = "high"
    elif score >= 4:
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "check_type": primary[0],
        "matched": primary[2],
        "score": score,
        "confidence": confidence,
        "secondary_check": secondary[0] if secondary else None,
        "secondary_matched": secondary[2] if secondary else None,
    }


def build_intent_directive(intent: Dict) -> str:
    """Build the hard-rule directive that gets injected into the DM user
    message. Tells the DM to NARRATE THE BEAT but NOT resolve the outcome,
    ending with a natural prompt for the appropriate check(s).
    """
    if not intent:
        return ""
    check = intent.get("check_type", "")
    matched = intent.get("matched", "")
    secondary = intent.get("secondary_check")
    secondary_matched = intent.get("secondary_matched")
    secondary_block = (
        f" The player ALSO performed a {secondary} action (matched: "
        f"'{secondary_matched}') — the system will require BOTH a {check} "
        f"and a {secondary} check. Mention both naturally in your closing "
        f"prompt (e.g. 'staying out of sight is one thing — making out "
        f"their words is another')."
        if secondary else ""
    )
    return (
        f"\n[INTENT-CLASSIFIER ({intent.get('confidence','low')}): {check}"
        f"{f' + {secondary}' if secondary else ''}] "
        f"The player's action contains cues for a {check} check (matched: '{matched}'). "
        f"You MUST narrate ONLY the visible BEAT (cause-and-effect — what stirs in the scene, "
        f"what the target's body language gives away, what tension hangs in the air) and END "
        f"your reply by prompting the appropriate {check} check naturally — "
        f"e.g. 'this calls for stealth' or 'his eyes flick to the blade — what's your tone?'. "
        f"Do NOT auto-resolve the outcome (don't say the NPC instantly believes / sees you / "
        f"is intimidated / falls for it / is convinced). The system layer will roll the check "
        f"and you'll narrate the fallout next turn. This is a hard rule.{secondary_block}"
    )
