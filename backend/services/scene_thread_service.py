"""Scene thread service — builds the continuity context block for the DM.

Every scene must close one loop and open the next. This service packages:
  - Which hook the player just engaged (the loop closing)
  - The wound layer reveal the DM should deliver (surface → mechanism → structure)
  - Which hooks remain open (they carry forward into the next scene)
  - A closing window directive (every response must end with urgency)

The output is injected into the DM system prompt so the DM knows exactly
what to reveal, what to plant, and what is still unresolved.
"""
from __future__ import annotations

from typing import Dict, List, Optional


def _detect_revealed_layers(recent_narration: str, wound_layers: Dict) -> List[str]:
    """Cheap heuristic: check which wound layer keywords appear in recent narration.
    Returns list of layers already revealed: ['surface'], ['surface','mechanism'], etc.
    """
    revealed = []
    text = recent_narration.lower()

    surface = (wound_layers.get("surface") or "").lower()
    mechanism = (wound_layers.get("mechanism") or "").lower()

    # Extract key nouns from each layer and check for presence in narration
    surface_words = [w for w in surface.split() if len(w) > 4][:4]
    mechanism_words = [w for w in mechanism.split() if len(w) > 4][:4]

    if surface_words and sum(1 for w in surface_words if w in text) >= 2:
        revealed.append("surface")
    if mechanism_words and sum(1 for w in mechanism_words if w in text) >= 2:
        revealed.append("mechanism")

    return revealed


def build_scene_thread_block(
    engaged_hook: Optional[Dict],
    unengaged_hooks: List[Dict],
    active_quest_cards: List[Dict],
    recent_narration: str = "",
) -> str:
    """Build the SCENE THREAD block for the DM system prompt.

    Args:
        engaged_hook: The hook the player just engaged, or None.
        unengaged_hooks: Hooks from recent scenes not yet investigated.
        active_quest_cards: Quest/lead cards from the campaign deck.
        recent_narration: Recent DM narration text (last 1-2 turns).

    Returns:
        A formatted string block injected into the DM prompt.
    """
    if not engaged_hook and not unengaged_hooks and not active_quest_cards:
        return ""

    lines: List[str] = ["=== SCENE THREAD ==="]

    # Find the active opening quest with wound_layers
    wound_layers: Dict = {}
    quest_title = ""
    for card in active_quest_cards:
        if card.get("status") != "active":
            continue
        tags = card.get("tags") or []
        if "opening" in tags or "quest" in tags:
            meta = card.get("metadata") or {}
            wl = meta.get("wound_layers") or {}
            if wl:
                wound_layers = wl
                quest_title = card.get("title") or ""
                break

    # Section 1: Engaged hook — what to close and what to reveal
    if engaged_hook:
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
    else:
        # No hook engaged — remind DM to keep existing loops visible
        lines.append(
            "\nNo hook directly engaged this turn. "
            "Keep the world moving — the scene is not frozen. "
            "Unresolved details from the previous scene still exist."
        )

    # Section 2: Open loops still in the scene
    if unengaged_hooks:
        lines.append("\nOPEN LOOPS (still in the world — reference in passing when natural):")
        for h in unengaged_hooks[:3]:
            text = h.get("text") or h.get("topic") or ""
            if text:
                lines.append(f"  ▸ {text}")

    # Section 3: Closing window — mandatory urgency at the end
    lines.append(
        "\nCLOSING WINDOW (mandatory): "
        "your response must end with ONE thing that is about to change, disappear, or demand "
        "immediate response. A person reaching a corner. A door about to close. A soldier's "
        "hand moving. Something that makes the player act NOW or lose the moment. "
        "State it as a plain fact. No editorializing."
    )

    # Section 4: Continuity rule
    lines.append(
        "\nCONTINUITY: the scene is continuous — the camera does not cut. "
        "NPCs who were present before are still present unless the player left or time passed. "
        "Do NOT reset the scene. Do NOT introduce ambient filler that breaks the active thread."
    )

    return "\n".join(lines)
