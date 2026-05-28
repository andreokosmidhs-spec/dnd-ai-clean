"""Scene thread service — builds the continuity context block for the DM.

Every scene must close one loop and open the next. This service packages:
  - Which hook the player just engaged (the loop closing)
  - The wound layer reveal the DM should deliver (surface → mechanism → structure)
  - Which hooks remain open (they carry forward into the next scene)
  - A closing window directive (every response must end with urgency)

When the player is traveling WITH PURPOSE to a known destination, the service
emits a FOCUSED OBJECTIVE block instead — suppressing random hooks and directing
the DM to surface only quest-relevant environmental evidence.

The output is injected into the DM system prompt so the DM knows exactly
what to reveal, what to plant, and what is still unresolved.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Movement / arrival detection
# ---------------------------------------------------------------------------

_MOVEMENT_RE = re.compile(
    r"\b(go\s+to|head\s+to|head\s+toward|walk\s+to|walk\s+toward|travel\s+to|"
    r"make\s+my\s+way|move\s+to|proceed\s+to|make\s+for|set\s+out|set\s+off|"
    r"go\s+there|head\s+there|enter|arrive|approach|return\s+to|go\s+back\s+to|"
    r"find\s+(?:the|a)\s+\w+|look\s+for|search\s+for)\b",
    re.IGNORECASE,
)


def _is_movement_to_objective(player_action: str) -> bool:
    """Return True when the player is clearly traveling toward a known destination."""
    return bool(_MOVEMENT_RE.search(player_action or ""))


def _get_active_quest(active_quest_cards: List[Dict]) -> Optional[Dict]:
    """Return the first active quest/lead card, or None."""
    for card in active_quest_cards:
        if (card.get("status") or "").lower() != "active":
            continue
        tags = card.get("tags") or []
        if any(t in tags for t in ("quest", "investigation", "lead", "opening", "active")):
            return card
    return None


# ---------------------------------------------------------------------------
# Wound layer detection
# ---------------------------------------------------------------------------

def _detect_revealed_layers(recent_narration: str, wound_layers: Dict) -> List[str]:
    """Cheap heuristic: check which wound layer keywords appear in recent narration."""
    revealed = []
    text = recent_narration.lower()

    surface = (wound_layers.get("surface") or "").lower()
    mechanism = (wound_layers.get("mechanism") or "").lower()

    surface_words = [w for w in surface.split() if len(w) > 4][:4]
    mechanism_words = [w for w in mechanism.split() if len(w) > 4][:4]

    if surface_words and sum(1 for w in surface_words if w in text) >= 2:
        revealed.append("surface")
    if mechanism_words and sum(1 for w in mechanism_words if w in text) >= 2:
        revealed.append("mechanism")

    return revealed


# ---------------------------------------------------------------------------
# Focused objective block
# ---------------------------------------------------------------------------

def _focused_objective_block(
    quest: Dict,
    wound_layers: Dict,
    unengaged_hooks: List[Dict],
) -> str:
    """Emit a FOCUSED OBJECTIVE block when the player is traveling with purpose.

    Suppresses random hook generation. Directs the DM to surface only
    quest-relevant environmental evidence at the destination.
    """
    quest_title = quest.get("title") or "Active Investigation"
    quest_desc = (quest.get("description") or "").strip()

    lines = [
        "=== FOCUSED OBJECTIVE ===",
        f"ACTIVE LEAD: {quest_title}",
    ]
    if quest_desc:
        lines.append(f"Context: {quest_desc[:160]}")

    lines += [
        "",
        "The player is arriving at this location WITH A PURPOSE. They are not exploring "
        "— they are investigating. The narration must serve that purpose.",
        "",
        "NARRATION RULES (these override the standard hook system for this turn):",
        "▸ DO NOT surface random unrelated hooks (a merchant's stall, a barking dog, "
        "  a notice board). Those belong in open-world exploration, not active investigation.",
        "▸ Every environmental detail you write must do ONE of these three things:",
        "  1. Confirm the target/objective is or was here (direct evidence)",
        "  2. Suggest what happened — absence, disorder, traces, witnesses reacting",
        "  3. Point forward — where does the evidence lead if the target isn't here",
        "▸ Allow 1-2 sensory/atmospheric details for texture — they should feel like "
        "  arriving at a crime scene, not a market stroll. Purposeful, not decorative.",
        "▸ If seeking a PERSON: describe physical evidence of their presence or absence "
        "  (their belongings, a witness's reaction, signs of their habits or a struggle). "
        "  If they are here, describe the person — don't delay the reveal.",
        "▸ If seeking a PLACE or ITEM: what does the space reveal about whether it has "
        "  been disturbed, used recently, or interfered with?",
        "▸ Plant ONE forward thread if the objective isn't directly met — a physical "
        "  detail that points to the next step. NOT a random hook. A purposeful lead.",
    ]

    # Surface wound layer clue if available
    surface = wound_layers.get("surface", "")
    if surface:
        lines.append(
            f"\nWOUND CLUE (embed naturally if not yet revealed): {surface[:120]}"
        )

    # Carry forward unengaged hooks only if directly related
    if unengaged_hooks:
        lines.append(
            "\nOPEN THREADS (reference ONLY if they connect to the objective — "
            "do not surface them as unrelated ambient detail):"
        )
        for h in unengaged_hooks[:2]:
            text = h.get("text") or h.get("topic") or ""
            if text:
                lines.append(f"  ▸ {text}")

    lines.append(
        "\nCLOSING WINDOW (mandatory): end with ONE thing that is about to change, "
        "disappear, or lock the player into a decision. Objective-relevant only — "
        "not ambient. 'The door at the end of the hall is closing.' not 'A crow calls.'"
    )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main block builder
# ---------------------------------------------------------------------------

def build_scene_thread_block(
    engaged_hook: Optional[Dict],
    unengaged_hooks: List[Dict],
    active_quest_cards: List[Dict],
    recent_narration: str = "",
    player_action: str = "",
) -> str:
    """Build the SCENE THREAD or FOCUSED OBJECTIVE block for the DM system prompt.

    Priority:
      1. engaged_hook  → SCENE THREAD (close the loop, reveal wound layer)
      2. movement + active quest → FOCUSED OBJECTIVE (suppress random hooks)
      3. neither → light continuity reminder
    """
    if not engaged_hook and not unengaged_hooks and not active_quest_cards:
        return ""

    # Resolve the active quest and its wound layers once
    wound_layers: Dict = {}
    quest_title = ""
    active_quest: Optional[Dict] = None
    for card in active_quest_cards:
        if card.get("status") != "active":
            continue
        tags = card.get("tags") or []
        if any(t in tags for t in ("quest", "investigation", "lead", "opening", "active")):
            meta = card.get("metadata") or {}
            wl = meta.get("wound_layers") or {}
            if wl:
                wound_layers = wl
            quest_title = card.get("title") or ""
            active_quest = card
            break

    # ----------------------------------------------------------------
    # Case 1: Player is actively investigating a specific hook
    # ----------------------------------------------------------------
    if engaged_hook:
        lines: List[str] = ["=== SCENE THREAD ==="]

        hook_text = engaged_hook.get("text") or engaged_hook.get("topic") or "the detail"
        lines.append(
            f"\nENGAGED HOOK: \"{hook_text}\"\n"
            "The player is investigating this. CLOSE THIS LOOP in your first sentence — "
            "give the reveal directly. Do not build up to it."
        )

        if wound_layers:
            revealed = _detect_revealed_layers(recent_narration, wound_layers)
            surface = wound_layers.get("surface", "")
            mechanism = wound_layers.get("mechanism", "")
            structure = wound_layers.get("structure", "")

            lines.append("\nWOUND REVEAL — deliver the next unrevealed layer:")

            if "surface" not in revealed and surface:
                lines.append(f"▸ DELIVER NOW (surface): {surface}")
                if mechanism:
                    lines.append(
                        f"▸ PLANT a detail that leads toward: {mechanism[:80]}... "
                        "(do not state this — embed a detail that points toward it)"
                    )
            elif "mechanism" not in revealed and mechanism:
                lines.append(f"▸ DELIVER NOW (mechanism — how the system works): {mechanism}")
                if structure:
                    lines.append(
                        f"▸ PLANT a detail that leads toward: {structure[:80]}... "
                        "(do not state this — embed a detail that points toward it)"
                    )
            elif structure:
                lines.append(f"▸ DELIVER NOW (structure — who benefits and why it persists): {structure}")
            else:
                lines.append("▸ Reveal what the player finds in concrete physical terms.")

        lines.append(
            "\nNEXT HOOK: plant one new unresolved detail before this scene ends. "
            "Embed it naturally — do NOT label it or call attention to it."
        )

        if unengaged_hooks:
            lines.append("\nOPEN LOOPS (still in the world — reference in passing when natural):")
            for h in unengaged_hooks[:3]:
                text = h.get("text") or h.get("topic") or ""
                if text:
                    lines.append(f"  ▸ {text}")

        lines.append(
            "\nCLOSING WINDOW (mandatory): "
            "your response must end with ONE thing that is about to change, disappear, or demand "
            "immediate response. A person reaching a corner. A door about to close. A soldier's "
            "hand moving. Something that makes the player act NOW or lose the moment. "
            "State it as a plain fact. No editorializing."
        )

        lines.append(
            "\nCONTINUITY: the scene is continuous — the camera does not cut. "
            "NPCs who were present before are still present unless the player left or time passed. "
            "Do NOT reset the scene. Do NOT introduce ambient filler that breaks the active thread."
        )

        return "\n".join(lines)

    # ----------------------------------------------------------------
    # Case 2: Player is traveling toward an objective with a purpose
    # ----------------------------------------------------------------
    if _is_movement_to_objective(player_action) and active_quest:
        return _focused_objective_block(active_quest, wound_layers, unengaged_hooks)

    # ----------------------------------------------------------------
    # Case 3: No hook engaged, no purposeful movement — light reminder
    # ----------------------------------------------------------------
    lines = [
        "=== SCENE THREAD ===",
        "\nNo hook directly engaged this turn. "
        "Keep the world moving — the scene is not frozen. "
        "Unresolved details from the previous scene still exist.",
    ]

    if unengaged_hooks:
        lines.append("\nOPEN LOOPS (still in the world — reference in passing when natural):")
        for h in unengaged_hooks[:3]:
            text = h.get("text") or h.get("topic") or ""
            if text:
                lines.append(f"  ▸ {text}")

    lines.append(
        "\nCLOSING WINDOW (mandatory): "
        "your response must end with ONE thing that is about to change, disappear, or demand "
        "immediate response. State it as a plain fact. No editorializing."
    )

    lines.append(
        "\nCONTINUITY: the scene is continuous — the camera does not cut. "
        "NPCs who were present before are still present unless the player left or time passed."
    )

    return "\n".join(lines)
