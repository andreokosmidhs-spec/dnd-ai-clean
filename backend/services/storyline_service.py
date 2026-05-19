"""Storyline service — drafts a 3-5 beat investigation chain from a hook,
advances beats, computes the final reward.

Model:

  Storyline = {
    id, campaign_id, character_id,
    title,                    # short investigation title
    hook_text,                # the literal hook phrase
    hook_id,                  # ref into the originating message's hooks
    status,                   # 'active' | 'completed' | 'abandoned'
    current_beat,             # int index into beats[]
    beats: [Beat],
    total_dc,                 # sum of beat.dc — drives reward magnitude
    reward,                   # populated on completion
    quest_card_id,            # link to the KnowledgeCard the first beat seeded
    created_at, updated_at
  }

  Beat = {
    title,                    # 3-6 word beat name
    description,              # 1-2 sentences of DM narration the beat opens with
    task,                     # what the player must DO
    dc,                       # 10..18
    check_type,               # 'Investigation' | 'Perception' | 'Insight' | 'Persuasion' | 'Stealth' | 'Athletics'
    ability,                  # 'INT' | 'WIS' | 'CHA' | 'DEX' | 'STR' | 'CON'
    status,                   # 'pending' | 'active' | 'passed' | 'failed' | 'skipped'
    outcome_text              # populated when resolved
  }

The hook becomes the FIRST beat's task by definition (the player engaged with
the hook, so beat 1 is the literal first investigation step). Beats 2..N
deepen the storyline with linked twists (e.g. "the sick sister", "the unpaid
debt", "the deception"). Linear progression: cards must resolve in order.
"""
from __future__ import annotations

import json as _json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from services.mission_types import render_blueprint_for_prompt
from services.time_service import bucket_for_hour


def _intent_get(intent, key: str, default: str = ""):
    """Read a field from a CampaignIntent (Pydantic) OR plain dict."""
    if intent is None:
        return default
    if isinstance(intent, dict):
        return intent.get(key, default)
    return getattr(intent, key, default)

logger = logging.getLogger(__name__)


_VALID_CHECK_TYPES = {
    "Investigation": "INT",
    "Perception":    "WIS",
    "Insight":       "WIS",
    "Persuasion":    "CHA",
    "Deception":     "CHA",
    "Intimidation":  "CHA",
    "Stealth":       "DEX",
    "Sleight of Hand": "DEX",
    "Athletics":     "STR",
    "Arcana":        "INT",
    "History":       "INT",
    "Nature":        "WIS",
    "Survival":      "WIS",
}


_KNOWLEDGE_CHECKS = {"Investigation", "History", "Arcana", "Religion", "Nature", "Insight", "Perception"}


def _infer_reveal_type(check_type: str) -> str:
    """Default reveal type if the LLM didn't mark a beat: knowledge for pure
    information-gathering checks, action for the rest."""
    return "knowledge" if (check_type or "") in _KNOWLEDGE_CHECKS else "action"


def _normalize_targets(raw) -> List[Dict]:
    """Sanitize target list for knowledge beats. Each target is {type, name}.
    Drops malformed entries; max 4."""
    if not isinstance(raw, list):
        return []
    out: List[Dict] = []
    for r in raw[:4]:
        if not isinstance(r, dict):
            continue
        t = str(r.get("type") or "").strip().lower()
        n = str(r.get("name") or "").strip()
        if t not in {"npc", "faction", "location", "direction"} or not n:
            continue
        out.append({"type": t, "name": n[:60]})
    return out


def _finalize_beat(beat: Dict) -> Dict:
    """Ensure every beat has a sane reveal_type, prompt (for knowledge), targets,
    and ability. Used by both the LLM and template paths."""
    rt = (beat.get("reveal_type") or "").strip().lower()
    if rt not in {"action", "knowledge"}:
        rt = _infer_reveal_type(beat.get("check_type") or "")
    beat["reveal_type"] = rt
    # Targets are kept regardless of reveal_type — action beats with public
    # reveals (reading a sign, observing what's in plain sight) ALSO name
    # entities the deck should auto-mint as Knowledge Cards.
    beat["targets"] = beat.get("targets") or []
    if rt == "knowledge":
        # Default prompt if the LLM didn't supply one
        if not (beat.get("prompt") or "").strip():
            beat["prompt"] = f"Roll {beat.get('check_type','Investigation')} (DC {beat.get('dc',12)}) to reveal what you can piece together."
    else:
        # action beats don't need a roll prompt
        beat["prompt"] = ""
    return beat


def _world_facts_block(world: Dict, cards: Optional[List[Dict]] = None, limit: int = 8) -> str:
    """Compact reference block of grounded world facts for the LLM to draw on
    when inventing concrete story details (NPC names, locations, factions,
    item history, rewards). Pulls factions/rumors/locations from `world` and
    recent active knowledge cards. Cards are truthier than fresh inventions —
    we want the storyline to NAME existing entities when possible.
    """
    lines: List[str] = []
    world = world or {}

    # Realm + setting flavor
    core = world.get("world_core") or {}
    if core:
        bits = []
        if core.get("name"):
            bits.append(f"realm={core['name']}")
        if core.get("genre"):
            bits.append(f"genre={core['genre']}")
        if core.get("tech"):
            bits.append(f"tech={core['tech']}")
        if core.get("magic"):
            bits.append(f"magic={core['magic']}")
        if bits:
            lines.append("World: " + " · ".join(bits))

    # Starting town
    town = world.get("startingLocation") or world.get("starting_town") or {}
    if isinstance(town, dict) and town.get("name"):
        flavor = town.get("flavor") or town.get("description") or ""
        lines.append(f"Town: {town['name']}{' — ' + str(flavor)[:120] if flavor else ''}")

    # Factions (up to 3)
    factions = (world.get("setting") or {}).get("factions") or world.get("factions") or []
    if isinstance(factions, list):
        for f in factions[:3]:
            if not isinstance(f, dict):
                continue
            name = f.get("name") or f.get("title")
            if not name:
                continue
            mot = f.get("motive") or f.get("agenda") or f.get("description") or ""
            lines.append(f"Faction: {name}{' — ' + str(mot)[:90] if mot else ''}")

    # Notable NPCs already on the world (from world.npcs or starting_scene)
    npcs = world.get("npcs") or []
    if isinstance(npcs, list):
        for n in npcs[:3]:
            if not isinstance(n, dict):
                continue
            nm = n.get("name")
            if not nm:
                continue
            role = n.get("role") or n.get("description") or ""
            lines.append(f"NPC: {nm}{' — ' + str(role)[:90] if role else ''}")

    # Recent active knowledge cards (NPCs, locations, factions, leads).
    # We surface these so the storyline can REUSE established names instead
    # of inventing new ones every turn.
    if isinstance(cards, list) and cards:
        for c in cards[:limit]:
            if not isinstance(c, dict):
                continue
            t = c.get("type")
            if t not in {"character", "npc", "location", "faction", "lore", "rumor", "lead", "quest"}:
                continue
            title = (c.get("title") or "").strip()
            if not title:
                continue
            desc = (c.get("description") or "").strip()
            lines.append(f"Card[{t}]: {title}{' — ' + desc[:90] if desc else ''}")

    if not lines:
        return ""
    return "=== WORLD FACTS (use these names when possible — invent only if needed) ===\n" + "\n".join(lines)



def _tag_phase(
    beat: Dict,
    mission_type: Optional[Dict],
    phase_index_raw,
    default_index: int = 0,
) -> None:
    """Tag a beat with `phase_index` and `phase_name` derived from the
    mission-type blueprint. Mutates `beat` in place. No-op when no
    mission_type is bound to this storyline."""
    if not mission_type or not isinstance(mission_type, dict):
        return
    phases = mission_type.get("phases") or []
    if not phases:
        return
    try:
        idx = int(phase_index_raw) if phase_index_raw is not None else default_index
    except (TypeError, ValueError):
        idx = default_index
    idx = max(0, min(len(phases) - 1, idx))
    beat["phase_index"] = idx
    beat["phase_name"] = (phases[idx] or {}).get("name") or ""


def _mission_type_snapshot(mission_type: Optional[Dict]) -> Optional[Dict]:
    """Lightweight subset of a mission-type stored on the storyline doc so
    the frontend "Active Phase" badge can read phase names without an
    extra round-trip."""
    if not mission_type or not isinstance(mission_type, dict):
        return None
    return {
        "id": mission_type.get("id"),
        "slug": mission_type.get("slug"),
        "name": mission_type.get("name"),
        "icon": mission_type.get("icon"),
        "phases": [
            {"name": (p or {}).get("name", "")}
            for p in (mission_type.get("phases") or [])
        ],
    }




def _story_fact_rules() -> str:
    """Hard rules forcing POV-anchored, realistic exposition in every storyline
    beat. Reused by draft_initial_scene and generate_next_scene. The DM should
    think like a real DM running a session at the table — read signs aloud,
    name the people you talk to, give the player concrete directions to act on.
    """
    return (
        "=== POV EXPOSITION RULES (think like a real DM at the table) ===\n"
        "1) WRITE FROM THE PLAYER'S POV. Use second-person — 'you see', 'you read', "
        "   'you hear', 'you can make out'. Describe ONLY what the character can "
        "   perceive RIGHT NOW with their senses + any prior knowledge they actually "
        "   have. FORBIDDEN: 'a memory ignites within you', 'you somehow know', "
        "   'fate whispers', 'destiny stirs', 'a flash of insight reveals' — the "
        "   character is not psychic and does not have unearned knowledge.\n"
        "2) SOURCE EVERY FACT. Every concrete fact you reveal must come from an "
        "   IN-FICTION source the player can point to: the literal text on the sign, "
        "   an inscription on an item, a snatch of overheard conversation, a known "
        "   bystander's offhand remark, the maker's mark, the watermark on a letter, "
        "   a merchant's whisper, an existing knowledge card. Cite the source in the "
        "   prose ('the inscription reads…', 'the herbalist mutters…', 'the seal is "
        "   stamped with the crest of …').\n"
        "3) READ POSTED TEXT ALOUD. When the hook is a sign, notice, poster, scroll, "
        "   letter, ledger, inscription, or any written object — INCLUDE THE LITERAL "
        "   POSTED TEXT in quotes (block-quoted, with the speaker/poster named). Real "
        "   medieval signage style: brief, practical, names a contact and a place. "
        "   Example: 'The placard reads: \"REWARD — 50 gp for the safe return of a "
        "   silver locket, House Veillane crest. Inquiries to Hester Crane at the "
        "   Anvil & Cup, south gate, before sundown.\"'\n"
        "4) ANSWER THE 'HOW DO I CLAIM THIS?' QUESTION. If the scene involves a "
        "   bounty/quest/reward, the description MUST tell the player WHERE to go, "
        "   WHO to ask for, and WHEN — by name and address. Not 'somewhere in the "
        "   docks' but 'Hester Crane, posting clerk at the Anvil & Cup, by the south "
        "   gate, hours after midday'.\n"
        "5) END WITH A DIRECTIONAL CHOICE. The last sentence should plant a concrete "
        "   next move the player can act on right now (a person to find, a door to "
        "   open, a route to take), not vague urgency.\n"
        "6) DECIDE — IS A CHECK ACTUALLY NEEDED? Use a DC check ONLY when the player "
        "   is trying to extract HIDDEN information that requires effort, training, "
        "   or a careful read. DO NOT lock public, openly-posted, or plain-visible "
        "   information behind a roll.\n"
        "   • NO ROLL (set `reveal_type='action'`, `dc=0`, and put the full content "
        "     in `description` openly): reading a public sign or notice, observing "
        "     what's openly displayed, hearing what someone is openly saying, "
        "     looking at an open ledger, reading the menu of a tavern, walking up "
        "     to a stall and asking the merchant their price.\n"
        "   • CHECK NEEDED (`reveal_type='knowledge'`, dc 10-18, description is the "
        "     gated revelation): deciphering coded or foreign text, reading body "
        "     language for a tell (Insight), spotting a hidden compartment "
        "     (Investigation), recalling lore about a crest (History), catching a "
        "     whispered conversation (Perception against ambient noise), eavesdropping "
        "     unnoticed (Stealth), tracking marks on the cobblestones (Survival).\n"
        "   When in doubt, default to NO ROLL — making players roll for things they "
        "   could just READ kills momentum.\n\n"
        "=== STORY-FACT REQUIREMENTS (every beat must carry weight) ===\n"
        "Every scene description MUST plant AT LEAST 4 of these CONCRETE facts, all "
        "sourced per rule #2 above:\n"
        "  A. NAMED CONTACT to act on right now — first name + role + WHERE to find "
        "     them ('Hester Crane, posting clerk, at the Anvil & Cup tavern by the "
        "     south gate'). Reuse names from WORLD FACTS when possible.\n"
        "  B. NAMED PLACE — a specific street, shop, district, or building (not "
        "     'the docks' but 'Garrick's Pier' or 'the south gate market').\n"
        "  C. ITEM/SUBJECT DETAIL — what the item literally looks like, who made it, "
        "     the maker's mark, when it was lost/stolen, what the sign claims.\n"
        "  D. STAKES/REWARD — concrete numbers ('50 gp', 'a writ of safe passage'), "
        "     when applicable.\n"
        "  E. APPLICATION ROUTE — sentence telling the player exactly how to claim "
        "     the reward / take the job / get the next clue.\n"
        "  F. TENSION/RIVAL — someone else who is also watching or also looking, "
        "     anchored in observable cues (a hooded figure also reading the sign, "
        "     guards watching the queue).\n"
        "FORBIDDEN PHRASES: 'a fragment of thought', 'something more outside', "
        "'whispers in the wind', 'a strange feeling', 'fate', 'the gods', "
        "'destiny', 'a flash of memory', 'you somehow sense'. If you write "
        "atmospheric language, it MUST be sensory and tied to a named fact.\n"
    )


# -------------------- deterministic fallback --------------------

_FALLBACK_BEAT_TEMPLATES = [
    {
        "title": "First Sign",
        "description": "What looked simple opens into something stranger; "
                       "small details disagree with the surface story.",
        "task_tmpl": "Look closer at {topic}",
        "check_type": "Investigation",
        "dc": 12,
    },
    {
        "title": "A Witness",
        "description": "Someone nearby saw what happened. Their willingness "
                       "to talk depends on how you approach them.",
        "task_tmpl": "Get a witness to speak about {topic}",
        "check_type": "Persuasion",
        "dc": 13,
    },
    {
        "title": "The Hidden Stake",
        "description": "Beneath the obvious motive sits a smaller, more "
                       "human one. Someone is paying for something they cannot afford.",
        "task_tmpl": "Read between the lines around {topic}",
        "check_type": "Insight",
        "dc": 14,
    },
    {
        "title": "Confrontation",
        "description": "The thread leads back to a person who would rather "
                       "the truth stay buried. The room sharpens.",
        "task_tmpl": "Confront whoever is behind {topic}",
        "check_type": "Intimidation",
        "dc": 15,
    },
]


def _template_storyline(hook: Dict, intent_focus: str = "Mystery") -> Dict:
    topic = (hook.get("topic") or hook.get("text") or "this matter").strip()
    title = f"The {topic.title()[:36]}".rstrip()
    beats: List[Dict] = []
    for i, t in enumerate(_FALLBACK_BEAT_TEMPLATES):
        ability = _VALID_CHECK_TYPES.get(t["check_type"], "INT")
        beats.append(_finalize_beat({
            "title": t["title"],
            "description": t["description"],
            "task": t["task_tmpl"].format(topic=topic),
            "dc": int(t["dc"]),
            "check_type": t["check_type"],
            "ability": ability,
            "status": "active" if i == 0 else "pending",
            "outcome_text": None,
        }))
    total_dc = sum(b["dc"] for b in beats)
    return {
        "title": title,
        "beats": beats,
        "total_dc": total_dc,
    }


# -------------------- Scene-driven draft (Feb 2026) --------------------


async def draft_initial_scene(
    campaign: Dict,
    character: Dict,
    hook: Dict,
    narration_context: str = "",
    mission_type: Optional[Dict] = None,
) -> Dict:
    """Open-ended scene-driven flow.

    Drafts ONLY the FIRST scene card from the engaged hook. The card describes
    the SCENE the player has stepped into (a result of engaging the hook); a
    suggested check is included but presented as OPTIONAL — the player can
    roll, type a creative approach, or skip. Subsequent beats are generated
    dynamically by `generate_next_scene` based on what the player actually
    does.

    Args:
        campaign, character, hook, narration_context: see draft_storyline.
        mission_type: optional blueprint; when given, the FIRST scene is
            shaped to fit the FIRST PHASE of the arc (e.g. Heist→Discovery:
            knowledge reveal of the target via Investigation/Perception).

    Returns {title, beats:[scene1], total_dc: scene1.dc}.
    """
    # Time-of-day grounding for atmospheric scenes.
    from services.time_service import get_world_clock, time_context_block
    from services.dnd_rules import passive_perception_block
    clock_hour = get_world_clock(campaign)
    time_block = time_context_block(clock_hour)
    pp_block = passive_perception_block(character)

    fallback_beat = _finalize_beat({
        "title": (hook.get("topic") or "First Sign")[:40].title(),
        "description": (
            f"You step into the matter of {hook.get('topic') or 'the lead'}. "
            "What looked simple from a distance opens up — the obvious story "
            "and the real one have begun to disagree."
        ),
        "task": f"Take stock of {hook.get('topic') or 'the scene'}",
        "dc": 12,
        "check_type": "Investigation",
        "ability": "INT",
        "reveal_type": "action",
        "prompt": "",
        "targets": [],
        "status": "active",
        "outcome_text": None,
    })
    fallback_title = f"The {(hook.get('topic') or 'matter').title()[:36]}".rstrip()
    fallback = {"title": fallback_title, "beats": [fallback_beat], "total_dc": fallback_beat["dc"]}

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        from services.time_service import bucket_for_hour
        fallback["beats"][0]["time_of_day"] = bucket_for_hour(clock_hour)
        _tag_phase(fallback["beats"][0], mission_type, None, default_index=0)
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        intent = campaign.get("intent") or {}
        world = campaign.get("world") or {}
        starting = world.get("startingLocation") or {}
        identity = character.get("identity") or {}
        cls = character.get("class") or character.get("class_") or {}
        bg = character.get("background") or {}
        hero_name = identity.get("name") or "the hero"
        class_key = (cls.get("key") or "adventurer").lower()
        bg_key = (bg.get("key") or "wanderer").lower()
        location = starting.get("name") or (world.get("starting_town") or {}).get("name") or "the town"
        realm = (world.get("world_core") or {}).get("name") or "the realm"

        facts_block = _world_facts_block(world, cards=campaign.get("_recent_cards") or [], limit=8)
        story_rules = _story_fact_rules()

        prompt = (
            "Draft the OPENING SCENE CARD of an open-ended investigation. The player just "
            "engaged with a hook (e.g. 'I investigate the warehouse', 'I read the wooden "
            "sign about the lost heirloom'). This card is the SCENE the player has stepped "
            "into AS A DIRECT RESULT of engaging that specific hook. The card includes a "
            "SUGGESTED check (loose; the player can roll, propose a creative approach, or "
            "skip and just describe what they do). Subsequent beats will be drafted "
            "dynamically by another call as the scene unfolds; you draft only this first card.\n\n"
            "=== CAMPAIGN ===\n"
            f"Realm: {realm} | Location: {location}\n"
            f"Tone: {intent.get('tone','Balanced')} | Focus: {intent.get('focus','Mystery')} | "
            f"Danger: {intent.get('danger','Medium')}\n\n"
            f"{facts_block}\n\n"
            "=== HERO ===\n"
            f"{hero_name} ({class_key}, {bg_key} background)\n\n"
            "=== HOOK (the player just engaged with this — THE SCENE MUST CENTER ON IT) ===\n"
            f"text: {hook.get('text','')}\n"
            f"topic: {hook.get('topic','')}\n"
            f"suggested verb: {hook.get('verb_hint','examine')}\n\n"
            f"=== RECENT NARRATION CONTEXT (background — do NOT just re-paint ambient) ===\n{(narration_context or '')[:600]}\n\n"
            f"{time_block}\n\n"
            f"{pp_block}\n\n"
            f"{_campaign_theme_block(campaign)}"
            f"{render_blueprint_for_prompt(mission_type)}\n\n"
            f"{_plausibility_gate_block(campaign, hook)}"
            "=== HARD GROUNDING RULES (non-negotiable) ===\n"
            "- The 'title' MUST reference the hook subject (e.g. hook='wooden sign about a "
            "lost family heirloom' -> title 'The Heirloom Notice' or 'The Posted Sign', NOT "
            "'Curious Marketplace').\n"
            "- The 'description' FIRST SENTENCE MUST name the literal hook object/subject "
            "and place it in front of the player (e.g. 'The wooden sign hangs at eye level, "
            "ink still wet from the morning'). Do NOT open with generic surroundings, "
            "weather, or unrelated atmosphere.\n"
            "- The 'task' MUST be a verb phrase aimed at the hook subject (e.g. 'Read the "
            "sign', 'Examine the heirloom notice', 'Question the posting clerk'). NOT 'scan "
            "the area' or other vague directives.\n"
            "- Use ambient detail (sounds/smells/light) only AFTER the hook subject is "
            "introduced, and only as texture around it.\n"
            "- For knowledge beats, the 'description' is the secret revelation; for action "
            "beats it is the visible scene with the hook subject foregrounded. EITHER WAY, "
            "the description must satisfy the STORY-FACT REQUIREMENTS below.\n\n"
            f"{story_rules}\n"
            "=== TARGETS (REQUIRED — do not return [] for knowledge beats) ===\n"
            "Populate `targets` with the named NPCs / locations / factions you put in the "
            "description (1-3 entries). The player's deck will mint Lead cards from these.\n\n"
            "=== OUTPUT (strict JSON only, no code fence) ===\n"
            "{\n"
            "  \"title\": \"investigation title (3-6 words, references the hook subject)\",\n"
            "  \"beat\": {\n"
            "    \"title\": \"scene title (3-6 words, references the hook subject)\",\n"
            "    \"description\": \"4-7 sentence Mercer-cinematic SCENE in second person POV. FIRST sentence names the hook subject directly. If the hook is a sign/notice/letter, INCLUDE THE LITERAL POSTED TEXT in quotes. Plant ≥4 concrete story facts (named contact + named place + item detail + reward + APPLICATION ROUTE saying where to claim it / who to ask for / when). Static observer framing — no psychic memories.\",\n"
            "    \"task\": \"short imperative aimed at the hook subject (one phrase)\",\n"
            "    \"check_type\": \"Investigation|Perception|Insight|Persuasion|Deception|Intimidation|Stealth|Sleight of Hand|Athletics|Arcana|History|Nature|Survival|Religion\",\n"
            "    \"dc\": 0,  // 0 = no roll needed (public/visible info — rule #6); else 10-18\n"
            "    \"reveal_type\": \"action|knowledge\",  // 'action' for public reveals (description shown openly); 'knowledge' ONLY when description is gated behind the roll\n"
            "    \"prompt\": \"(knowledge beats only) public-facing tease shown before the roll, no spoilers\",\n"
            "    \"phase_index\": 0,  // (only when MISSION TYPE BLUEPRINT is provided) 0-based index of the phase this beat belongs to (the FIRST scene is almost always phase 0)\n"
            "    \"targets\": [{\"type\": \"npc|faction|location|direction\", \"name\": \"<actual named entity from your description>\"}]\n"
            "  }\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-scene1-{uuid4()}",
            system_message=(
                "You are a senior D&D Dungeon Master running a live session at the "
                "table. You write tight, sensory opening scenes anchored on the literal "
                "hook subject, FROM THE PLAYER'S POV. When the hook is a sign or notice, "
                "you READ THE LITERAL POSTED TEXT ALOUD in the description. You always "
                "tell the player exactly where to go, who to ask for, and when. Empty "
                "atmospheric phrases ('a fragment of thought', 'a flash of memory', "
                "'fate stirs') are forbidden — every fact must be sourced in-fiction. "
                "Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        title = (data.get("title") or "").strip() or fallback_title
        rb = data.get("beat") or {}
        if not isinstance(rb, dict):
            return fallback
        ct = (rb.get("check_type") or "Investigation").strip()
        if ct not in _VALID_CHECK_TYPES:
            ct = "Investigation"
        try:
            dc = int(rb.get("dc") or 0)
        except Exception:
            dc = 0
        # Allow dc=0 to mean "no roll required" (public/visible info). When a
        # roll IS suggested, clamp into the playable 8-20 range.
        if dc > 0:
            dc = max(8, min(20, dc))
        beat = _finalize_beat({
            "title": (rb.get("title") or "First Sign").strip()[:48],
            "description": (rb.get("description") or "").strip()[:1100],
            "task": (rb.get("task") or "Look closer").strip()[:160],
            "dc": dc,
            "check_type": ct,
            "ability": _VALID_CHECK_TYPES[ct],
            "reveal_type": (rb.get("reveal_type") or "").strip().lower(),
            "prompt": (rb.get("prompt") or "").strip()[:200],
            "targets": _normalize_targets(rb.get("targets")),
            "status": "active",
            "outcome_text": None,
        })
        if not beat["description"]:
            return fallback
        # If the LLM left dc=0, the roll is optional — UI renders an "OPEN" chip.
        beat["roll_optional"] = (dc == 0)
        # Tag the scene with the current time-of-day for the UI.
        from services.time_service import bucket_for_hour
        beat["time_of_day"] = bucket_for_hour(clock_hour)
        # Tag with mission-arc phase info (frontend "Active Phase" badge).
        _tag_phase(beat, mission_type, rb.get("phase_index"), default_index=0)
        return {"title": title[:60], "beats": [beat], "total_dc": dc}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Initial scene draft failed, using fallback: {exc}")
        from services.time_service import bucket_for_hour
        fallback["beats"][0]["time_of_day"] = bucket_for_hour(clock_hour)
        _tag_phase(fallback["beats"][0], mission_type, None, default_index=0)
        return fallback


async def infer_player_intent(
    storyline: Dict,
    latest_action: str,
) -> Optional[str]:
    """Fast haiku pass: read every beat's outcome text + the current action and
    infer what the player is *actually* pursuing — the goal beneath the task.
    Returns a short internal DM note (never shown to the player).
    Returns None on any failure so callers can degrade gracefully.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    beats = storyline.get("beats") or []
    if not beats:
        return None

    beat_log = "\n".join(
        f"  [{b.get('status','?')}] {b.get('title','')}: {(b.get('outcome_text') or b.get('description',''))[:180]}"
        for b in beats
    )
    prompt = (
        "You are the DM's private reasoning layer. Read the player's actions across "
        "this storyline and infer their ACTUAL goal — the motivation beneath the surface task. "
        "Go beyond 'they investigated' — name what they want emotionally and specifically: "
        "protection, exposure, revenge, alliance, rescue, ownership, closure, redemption, etc. "
        "Name who they want it from/for if the story made that clear. "
        "Note what reward would feel genuinely earned to them.\n\n"
        f"=== STORYLINE: {storyline.get('title','')} ===\n"
        f"Hook: {storyline.get('hook_text','')}\n\n"
        f"Beat history:\n{beat_log}\n\n"
        f"Latest player action:\n{latest_action[:400]}\n\n"
        "In 1-2 sentences, state the player's underlying goal and what would feel "
        "meaningful as a reward. Be specific. This note is private to the DM."
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=api_key,
            session_id=f"intent-{uuid4()}",
            system_message="You are an expert narrative designer. Respond with 1-2 sentences only.",
        )
        chat.with_model("openai", "gpt-4o-mini").with_params(temperature=0.3, max_tokens=120)
        result = await chat.send_message(UserMessage(text=prompt))
        return (result or "").strip() or None
    except Exception as exc:  # noqa: BLE001
        logger.debug(f"Intent inference failed (non-fatal): {exc}")
        return None


async def generate_next_scene(
    campaign: Dict,
    character: Dict,
    storyline: Dict,
    player_action_summary: str,
    player_intent: Optional[str] = None,
) -> Dict:
    """After the current beat has been resolved (rolled/creative/skipped), the
    DM decides whether the scene RESOLVES here or whether to draft the NEXT
    scene card based on what the player actually did.

    Returns one of:
      {"is_final": True,  "epilogue": "1-2 sentence Mercer epilogue lead-in"}
      {"is_final": False, "beat": <new_beat_dict>}

    The new beat narrates what just happened (player's action consequences)
    AND the new situation/tension. Suggested check is included only if it's
    natural — pure narrative beats can omit it.
    """
    # Time-of-day grounding for atmospheric scenes.
    from services.time_service import bucket_for_hour, get_world_clock, time_context_block
    from services.dnd_rules import passive_perception_block
    clock_hour = get_world_clock(campaign)
    time_block = time_context_block(clock_hour)
    pp_block = passive_perception_block(character)

    beats = storyline.get("beats") or []
    # Hard stop after 7 beats — keeps storylines from running away.
    too_long = len(beats) >= 7

    # Mission-type blueprint snapshot — when this storyline was drafted with
    # a chosen blueprint, every continuation beat should keep advancing the
    # phase arc instead of drifting off-mission.
    mission_type = storyline.get("mission_type")
    current_phase_idx = 0
    for b in reversed(beats):
        if isinstance(b, dict) and isinstance(b.get("phase_index"), int):
            current_phase_idx = b["phase_index"]
            break
    mission_block = ""
    if mission_type:
        try:
            phases = mission_type.get("phases") or []
            cur_name = (phases[current_phase_idx] or {}).get("name", "") if phases else ""
            nxt_name = (phases[current_phase_idx + 1] or {}).get("name", "") if current_phase_idx + 1 < len(phases) else ""
            mission_block = (
                f"=== MISSION TYPE CONTEXT ===\n"
                f"Type: {mission_type.get('icon','')} {mission_type.get('name','')}\n"
                f"Most-recent beat sits in PHASE {current_phase_idx + 1}"
                f"{(' (' + cur_name + ')') if cur_name else ''}.\n"
                f"{('The next natural phase is PHASE ' + str(current_phase_idx + 2) + (' (' + nxt_name + ')') if nxt_name else '') if nxt_name else 'No further phase — drive toward resolution.'}\n"
                f"{render_blueprint_for_prompt(mission_type)}\n\n"
                "When emitting the next beat, set `phase_index` to the 0-based "
                "phase this beat belongs to. Stay in the current phase if its "
                "goal isn't reached yet; advance to the next phase when it is.\n\n"
            )
        except Exception:  # noqa: BLE001
            mission_block = ""

    fallback_beat = _finalize_beat({
        "title": "The Path Forward",
        "description": (
            "The thread you pulled has tightened. What was simple a moment ago "
            "now opens onto a sharper choice — and someone, somewhere, has noticed."
        ),
        "task": "Decide your next move",
        "dc": 12,
        "check_type": "Insight",
        "ability": "WIS",
        "reveal_type": "action",
        "prompt": "",
        "targets": [],
        "status": "active",
        "outcome_text": None,
    })

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        if too_long:
            return {"is_final": True, "epilogue": "The trail goes quiet, and the matter resolves into something you can carry forward."}
        fallback_beat["time_of_day"] = bucket_for_hour(clock_hour)
        return {"is_final": False, "beat": fallback_beat}

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        intent = campaign.get("intent") or {}
        world = campaign.get("world") or {}
        starting = world.get("startingLocation") or {}
        identity = (character or {}).get("identity") or {}
        hero_name = identity.get("name") or "the hero"
        location = starting.get("name") or (world.get("starting_town") or {}).get("name") or "the town"
        realm = (world.get("world_core") or {}).get("name") or "the realm"

        facts_block = _world_facts_block(world, cards=campaign.get("_recent_cards") or [], limit=8)
        story_rules = _story_fact_rules()

        beats_summary = "\n".join(
            f"  Beat {i+1} [{b.get('status','?')}] {b.get('title','')}: "
            f"{(b.get('outcome_text') or b.get('description',''))[:200]}"
            for i, b in enumerate(beats)
        )

        prompt = (
            "Continue an open-ended investigation scene. The player JUST resolved the "
            "current beat (rolled, used a creative approach, or skipped). Your job: decide "
            "whether the scene RESOLVES here, OR draft the NEXT scene card based on what "
            "the player did.\n\n"
            "Resolve when: the player has reached a natural stopping point (uncovered the "
            "truth, escaped, made the deal, walked away with what they came for, OR utterly "
            "failed to make progress). Otherwise, write the NEXT card.\n\n"
            "If you draft the next card, it must NARRATE the consequence of what the player "
            "just did AND the new situation — never restart the scene. Then suggest an "
            "OPTIONAL check natural to this moment (or omit if pure narrative). The player "
            "can roll, propose a creative approach, or skip.\n\n"
            "=== CAMPAIGN ===\n"
            f"Realm: {realm} | Location: {location}\n"
            f"Tone: {intent.get('tone','Balanced')} | Focus: {intent.get('focus','Mystery')} | "
            f"Danger: {intent.get('danger','Medium')}\n\n"
            f"{facts_block}\n\n"
            f"=== HERO ===\n{hero_name}\n\n"
            "=== STORYLINE ===\n"
            f"Title: {storyline.get('title','')}\n"
            f"Hook: {storyline.get('hook_text','')}\n"
            f"Beats so far ({len(beats)}):\n{beats_summary}\n\n"
            "=== PLAYER'S MOST RECENT ACTION ===\n"
            f"{(player_action_summary or '')[:500]}\n\n"
            + (
                f"=== DM'S READ ON THE PLAYER (private — never quote this directly) ===\n"
                f"{player_intent}\n"
                "Weight your next beat toward this goal. The player should feel the story is "
                "listening — not through meta-commentary, but through what the world offers them next.\n\n"
                if player_intent else ""
            )
            + f"{time_block}\n\n"
            f"{pp_block}\n\n"
            f"{mission_block}"
            "=== RULES ===\n"
            f"- Storyline has been running {len(beats)} beat(s). "
            f"{'You SHOULD resolve here unless absolutely critical to continue.' if too_long else 'Aim for 3-5 beats total; resolve only when narratively earned.'}\n"
            "- If next card: 3-5 sentences, Mercer-cinematic, second person, present tense, "
            "  static observer framing. NARRATE the just-played action's consequence + the "
            "  new situation in the SAME breath. NAME the people, places, items, and stakes "
            "  involved — never gesture at them with phrases like 'something more' or "
            "  'a fragment of thought'. Reuse names from WORLD FACTS where possible; invent "
            "  grounded specifics when the world doesn't already have one.\n"
            "- Suggested check: include `check_type` and `dc` (10-18) ONLY when natural; set to "
            "  null for pure narrative transitions.\n"
            "- Knowledge vs action: knowledge beats hide the description as a secret revelation "
            "  until the player passes the check. Set `reveal_type` accordingly. The "
            "  description IS the revelation, so it MUST carry concrete facts the player "
            "  earned by passing the check (NPC name + location + item history + stakes).\n"
            "- ESCALATE — each beat must surface a NEW named entity OR a NEW concrete fact "
            "  the player didn't have before. No restating prior reveals.\n"
            "- QUOTE NPC SPEECH — NEVER SUMMARIZE IT. If any NPC speaks, whispers, prays, "
            "  sings, or is overheard in this beat, the actual words MUST appear in double "
            "  quotes inside the description. Examples — RIGHT: '\"…Evelyn. The old docks. "
            "  Before second bell,\" the cloaked figure mutters, breath fogging in the "
            "  lantern light.' / WRONG: 'they mention a name and a place'. Even partial "
            "  overhearing must be rendered as quoted fragments ('\"…the locket…\" — the "
            "  rest is lost to the wind'). Summarized speech ('she explains that...', 'he "
            "  tells you...', 'they discuss...') is BANNED. Spending 1-2 quoted lines on "
            "  important NPC dialogue is correct, not bloat.\n"
            "- TIME-OF-DAY IS A HARD CONSTRAINT (see TIME OF DAY block above). Every "
            "  beat — description, task, prompt, named targets, hooks — must be plausible "
            "  at the current period. At Night/Midnight: NO children in the streets, NO "
            "  merchants setting up, NO market crowds, NO dawn or morning light, NO fresh "
            "  bread, NO 'morning breeze'. At Midday: NO lanterns lit, NO twilight chill. "
            "  If a hook would be impossible at this hour, rewrite it to something that "
            "  fits (a lone watchman, a smuggler in shadow, a tavern's last patron, an "
            "  informant in a doorway). Treat time as a hard gate on what can happen.\n"
            "- NO clichés ('fate', 'the gods', 'the wind whispers', 'something stirs'). "
            "  NO recap of earlier beats verbatim.\n"
            "- Output strict JSON, no code fence.\n\n"
            f"{story_rules}\n"
            "=== TARGETS (REQUIRED — do not return [] for knowledge beats) ===\n"
            "Populate `targets` with the named NPCs / locations / factions you put in the "
            "description (1-3 entries). The player's deck mints Lead cards from these.\n\n"
            "=== OUTPUT (strict JSON only) ===\n"
            "{\n"
            "  \"is_final\": false,\n"
            "  \"epilogue\": \"only when is_final=true: 1-2 sentence Mercer epilogue with named entities\",\n"
            "  \"beat\": {\n"
            "    \"title\": \"...\",\n"
            "    \"description\": \"4-7 sentences in second person POV — what the player sees/hears/reads right now. Source every fact in-fiction (quoted posted text, named bystander remarks, observable maker's marks). Plant ≥4 concrete story facts including a NAMED CONTACT to act on + APPLICATION ROUTE (where/who/when to claim or follow up).\",\n"
            "    \"task\": \"short imperative for the moment\",\n"
            "    \"check_type\": \"Investigation|Perception|... or null\",\n"
            "    \"dc\": 0,  // 0 = no roll needed (rule #6); else 10-18\n"
            "    \"reveal_type\": \"action|knowledge\",  // 'action' = description shown openly; 'knowledge' ONLY when content is gated by the roll\n"
            "    \"prompt\": \"(knowledge only) public tease before the roll\",\n"
            "    \"phase_index\": 0,  // (only when MISSION TYPE CONTEXT is provided) 0-based phase index this beat belongs to\n"
            "    \"targets\": [{\"type\": \"npc|faction|location|direction\", \"name\": \"<actual named entity from your description>\"}]\n"
            "  }\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-next-{uuid4()}",
            system_message=(
                "You are a senior D&D Dungeon Master running a live session at the "
                "table. You write scene cards FROM THE PLAYER'S POV — second person, "
                "what they see/hear/read RIGHT NOW. You source every fact in-fiction "
                "(quoting posted text, citing the bystander who said it, naming the "
                "maker's mark on the item). You tell the player exactly where to go, "
                "who to find by name, and how to claim rewards. Empty phrases like "
                "'a fragment of thought', 'a flash of memory', or 'fate stirs' are "
                "forbidden — the character is not psychic. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        is_final = bool(data.get("is_final"))
        if is_final or too_long:
            ep = (data.get("epilogue") or "").strip()[:240]
            if not ep:
                ep = "The thread you were pulling resolves — for now. The shape of what you've done will travel ahead of you."
            return {"is_final": True, "epilogue": ep}

        rb = data.get("beat") or {}
        if not isinstance(rb, dict) or not (rb.get("description") or "").strip():
            return {"is_final": False, "beat": fallback_beat}
        ct_raw = (rb.get("check_type") or "").strip()
        if ct_raw and ct_raw in _VALID_CHECK_TYPES:
            ct = ct_raw
            ability = _VALID_CHECK_TYPES[ct]
        else:
            # Pure narrative beat — no check. Use a default ability for UI but
            # mark dc=0 as "no roll suggested".
            ct = "Insight"
            ability = "WIS"
        try:
            dc = int(rb.get("dc") or 0)
        except Exception:
            dc = 0
        if dc > 0:
            dc = max(8, min(20, dc))
        else:
            dc = 0
        beat = _finalize_beat({
            "title": (rb.get("title") or "Next Scene").strip()[:48],
            "description": (rb.get("description") or "").strip()[:1100],
            "task": (rb.get("task") or "Decide your next move").strip()[:160],
            "dc": dc,  # keep 0 when no roll is suggested — the UI renders "OPEN"
            "check_type": ct,
            "ability": ability,
            "reveal_type": (rb.get("reveal_type") or "").strip().lower(),
            "prompt": (rb.get("prompt") or "").strip()[:200],
            "targets": _normalize_targets(rb.get("targets")),
            "status": "active",
            "outcome_text": None,
        })
        # Mark whether a roll is actually suggested for this scene (UI hint)
        beat["roll_optional"] = (dc == 0)
        # Tag with time-of-day for the UI.
        beat["time_of_day"] = bucket_for_hour(clock_hour)
        # Tag with mission-arc phase. Default to the prior beat's phase so
        # the badge keeps a stable phase when the LLM omits it.
        _tag_phase(beat, mission_type, rb.get("phase_index"), default_index=current_phase_idx)
        return {"is_final": False, "beat": beat}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Next-scene generation failed, using fallback: {exc}")
        if too_long:
            return {"is_final": True, "epilogue": "The trail goes quiet, and what you've gathered is what you'll carry forward."}
        fallback_beat["time_of_day"] = bucket_for_hour(clock_hour)
        _tag_phase(fallback_beat, mission_type, None, default_index=current_phase_idx)
        return {"is_final": False, "beat": fallback_beat}


# -------------------- LLM-driven draft (legacy multi-beat) --------------------


def _campaign_theme_block(campaign: Dict) -> str:
    """Inject the player-defined campaign theme (free text) into the
    storyline prompt. The theme is a campaign-level vibe ('comedic caper',
    'gothic horror', 'high seas roguery') that biases every storyline.
    """
    theme = (campaign.get("theme") or "").strip()
    if not theme:
        return ""
    return (
        "=== CAMPAIGN THEME (player's high-level vibe — bias prose, tone, hooks toward this) ===\n"
        f"{theme[:600]}\n\n"
    )


def _plausibility_gate_block(campaign: Dict, hook: Dict) -> str:
    """Hard-rule block that prevents nonsense beats: morning scenarios at
    midnight, secret events in crowded scenes, races that don't live in
    the region appearing as NPCs. The DM must check every beat against
    this before emitting it.
    """
    world = campaign.get("world") or {}
    world_state = campaign.get("world_state") or {}
    clock_hour = int(world_state.get("clock_hour", 9))
    period = bucket_for_hour(clock_hour)

    # Crowd density inferred from time-of-day + hook topic. Hook topics like
    # 'tavern', 'market', 'square' are inherently crowded during daylight;
    # 'alley', 'docks at night', 'crypt', 'library' are inherently private.
    hook_text = (hook.get("text") or "").lower()
    hook_topic = (hook.get("topic") or "").lower()
    crowded_words = ("market", "tavern", "square", "festival", "parade", "crowd", "court", "fair")
    private_words = ("alley", "cellar", "crypt", "library", "back room", "wharf at night", "rooftop")
    crowd_density = "private"
    if any(w in hook_text or w in hook_topic for w in crowded_words):
        crowd_density = "crowded"
    elif any(w in hook_text or w in hook_topic for w in private_words):
        crowd_density = "private"
    # Time also drives density — midnight defaults to empty even at a market.
    if period["key"] in ("evening", "midnight", "night"):
        if crowd_density == "crowded":
            crowd_density = "thin"   # tavern after curfew, watchmen at the gate
        else:
            crowd_density = "empty"

    # Regional races — drawn from world_blueprint if present.
    region_races_raw = world.get("region_races") or world.get("primary_races") or []
    if isinstance(region_races_raw, list) and region_races_raw:
        region_races = ", ".join(str(r) for r in region_races_raw[:6])
    else:
        region_races = "Human (default); other races are RARE — name them only when justified."

    return (
        "=== PLAUSIBILITY GATE (HARD RULE — every beat must pass this) ===\n"
        f"Current time-of-day: {period['label']} ({period['icon']}, hour {period['hour']:02d}/24).\n"
        f"Scene crowd density: {crowd_density}.\n"
        f"Region demographics: {region_races}.\n\n"
        "Before emitting a beat, check ALL of these:\n"
        "  1) TIME-OF-DAY: NPC activities must fit the current period. At "
        "     night/midnight: no merchants 'setting up', no children, no "
        "     market crowds, no dawn light. At midday: no lanterns lit, no "
        "     twilight chill. Reread the TIME OF DAY block above.\n"
        f"  2) CROWD DENSITY ({crowd_density}): \n"
        "     - 'crowded'  → secret/private exchanges are IMPLAUSIBLE here; "
        "       use overheard fragments, signals, dead-drops, or move "
        "       the beat to a quieter sub-location.\n"
        "     - 'empty/thin' → public-spectacle hooks are IMPLAUSIBLE; "
        "       use a single witness, a lone watchman, or a deserted "
        "       stall instead of crowds.\n"
        "  3) REGION RACES: only feature NPC races that PLAUSIBLY live in "
        "     this region. If the region is Human-default, do NOT invent "
        "     Tiefling/Tabaxi/Drow walking the streets unless the campaign "
        "     theme explicitly permits it. Travellers and outliers are OK "
        "     but must be flagged as foreign or notable in the prose.\n"
        "  4) Hook fit: every beat must remain LOGICALLY connected to the "
        "     hook. Don't pivot to an unrelated topic just to vary it.\n\n"
        "If a phase's natural goal is impossible here (e.g. 'Scouting a "
        "crowded square at midnight'), REWRITE the beat into the right "
        "sub-location (the watchman's lantern-lit corner, the closed "
        "stall's back door) instead of breaking the rule.\n\n"
    )



async def draft_storyline(
    campaign: Dict,
    character: Dict,
    hook: Dict,
    narration_context: str = "",
    mission_type: Optional[Dict] = None,
) -> Dict:
    """Draft a 3-5 beat linear investigation chain rooted in `hook`.

    Args:
        campaign:           campaign doc (provides world, intent, theme,
                            world_clock, mission types selected by player)
        character:          character doc
        hook:               the player-clicked hook this storyline grows from
        narration_context:  optional recent-narration string
        mission_type:       optional mission-type blueprint — when given,
                            beats are shaped to follow the phase arc
                            (Heist: Discovery → Scouting → Tools → Strike).

    Returns a dict with `title`, `beats`, `total_dc`. Caller (router) wraps it
    with ids, status, timestamps before persisting.
    """
    fallback = _template_storyline(hook, (campaign.get("intent") or {}).get("focus", "Mystery"))

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        intent = campaign.get("intent") or {}
        world = campaign.get("world") or {}
        starting = world.get("startingLocation") or {}
        identity = character.get("identity") or {}
        cls = character.get("class") or character.get("class_") or {}
        bg = character.get("background") or {}

        hero_name = identity.get("name") or "the hero"
        class_key = (cls.get("key") or "adventurer").lower()
        bg_key = (bg.get("key") or "wanderer").lower()
        location = starting.get("name") or (world.get("starting_town") or {}).get("name") or "the town"
        realm = (world.get("world_core") or {}).get("name") or "the realm"

        prompt = (
            "Draft a SHORT INVESTIGATION CHAIN (3-5 linked beats) that grows out of a "
            "single point of interest the player just engaged with. The first beat IS "
            "the literal investigation of the hook; the remaining beats deepen the story "
            "with linked twists (e.g. for 'someone stealing from someone' → 'the sick "
            "sister', 'the unpaid debt', 'the deception'). Linear progression: each "
            "beat must be resolvable before the next is opened.\n\n"
            "=== CAMPAIGN ===\n"
            f"Realm: {realm} | Location: {location}\n"
            f"Tone: {intent.get('tone','Balanced')} | Focus: {intent.get('focus','Mystery')} | "
            f"Danger: {intent.get('danger','Medium')}\n\n"
            "=== HERO ===\n"
            f"{hero_name} ({class_key}, {bg_key} background)\n\n"
            "=== HOOK (the player just engaged with this) ===\n"
            f"{hook.get('text','')}\n"
            f"(topic: {hook.get('topic','')}, suggested verb: {hook.get('verb_hint','examine')})\n\n"
            f"=== RECENT NARRATION CONTEXT ===\n{(narration_context or '')[:600]}\n\n"
            f"{_campaign_theme_block(campaign)}"
            f"{render_blueprint_for_prompt(mission_type)}"
            f"{_plausibility_gate_block(campaign, hook)}"
            "=== REQUIREMENTS ===\n"
            "- 3-5 beats. Linear order. Each beat is a discrete TASK with a DC.\n"
            "- Beat 1 must be the literal first step of investigating the hook.\n"
            "- Each subsequent beat introduces a NEW small revelation that links back\n"
            "  (a relationship, a debt, a lie, a place, a witness) — not a copy of the previous.\n"
            "- Vary check types across beats. DC range: 10..18. At least one beat between 13-16.\n"
            "- Plausible at level 1-3.\n"
            "- Each beat MUST be marked with reveal_type:\n"
            "  • 'knowledge' if the player ROLLS to LEARN something — Investigation / History / Arcana /\n"
            "    Religion / Nature / Insight / Perception spotting a clue. The beat's `description` becomes\n"
            "    a SECRET revelation that the player only sees if they pass; you must also provide a `prompt`\n"
            "    field — a short public-facing line shown BEFORE the roll (e.g. 'Roll History to recognize the\n"
            "    crest stamped on the medallion.'). For knowledge beats also include `targets`: a short list of\n"
            "    {type, name} pointers naming the NPC, faction, location, or direction the lead points to.\n"
            "  • 'action' for everything else (Persuasion, Stealth, Athletics, Deception, Intimidation, etc.).\n"
            "    For action beats, `description` is the cinematic framing of the moment (always shown); no\n"
            "    `prompt` or `targets` needed.\n"
            "- NO clichés ('ancient evil', 'chosen one', 'prophecy'). Real human stakes.\n"
            "- Title for the storyline is 3-6 words.\n\n"
            "=== OUTPUT (strict JSON only, no code fence) ===\n"
            "{\n"
            "  \"title\": \"...\",\n"
            "  \"beats\": [\n"
            "    {\n"
            "      \"title\": \"...\",\n"
            "      \"description\": \"1-2 sentences (mid-cinematic, present tense, second person; <=240 chars). For knowledge beats, this is the SECRET REVELATION shown only on success.\",\n"
            "      \"task\": \"what the hero must DO this beat (one short imperative)\",\n"
            "      \"dc\": 10,\n"
            "      \"check_type\": \"Investigation|Perception|Insight|Persuasion|Deception|Intimidation|Stealth|Sleight of Hand|Athletics|Arcana|History|Nature|Survival|Religion\",\n"
            "      \"reveal_type\": \"action|knowledge\",\n"
            "      \"prompt\": \"(knowledge beats only) public-facing tease shown BEFORE the roll, no spoilers\",\n"
            "      \"targets\": [{\"type\": \"npc|faction|location|direction\", \"name\": \"...\"}]\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-draft-{uuid4()}",
            system_message=(
                "You are a senior D&D campaign designer. You draft tight, linked "
                "investigation chains with concrete tasks and clear DCs. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        title = (data.get("title") or "").strip() or fallback["title"]
        raw_beats = data.get("beats") or []
        beats: List[Dict] = []
        for i, rb in enumerate(raw_beats[:5]):
            if not isinstance(rb, dict):
                continue
            t = (rb.get("title") or "").strip()
            d = (rb.get("description") or "").strip()
            tk = (rb.get("task") or "").strip()
            ct = (rb.get("check_type") or "Investigation").strip()
            if ct not in _VALID_CHECK_TYPES:
                ct = "Investigation"
            ab = _VALID_CHECK_TYPES[ct]
            try:
                dc = int(rb.get("dc") or 12)
            except Exception:
                dc = 12
            dc = max(8, min(20, dc))
            if not (t and d and tk):
                continue
            beats.append(_finalize_beat({
                "title": t[:48],
                "description": d[:280],
                "task": tk[:160],
                "dc": dc,
                "check_type": ct,
                "ability": ab,
                "reveal_type": (rb.get("reveal_type") or "").strip().lower(),
                "prompt": (rb.get("prompt") or "").strip()[:200],
                "targets": _normalize_targets(rb.get("targets")),
                "status": "active" if i == 0 else "pending",
                "outcome_text": None,
            }))
        if len(beats) < 3:
            return fallback
        total_dc = sum(b["dc"] for b in beats)
        return {"title": title[:60], "beats": beats, "total_dc": total_dc}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Storyline draft LLM failed, using template: {exc}")
        return fallback


# -------------------- reward --------------------

def _xp_for_total_dc(total_dc: int) -> int:
    """Total DC -> base XP. Roughly DC*8 with a soft floor and ceiling.
    A 4-beat storyline summing to DC 56 yields ~450 XP. The actual XP awarded
    SCALES with how many beats the player actually passed (linear).
    """
    base = max(60, total_dc * 8)
    # Smooth-cap: round to nearest 25, max 1200
    return min(1200, int(round(base / 25)) * 25)


def _scaled_xp(storyline: Dict) -> int:
    """Scale base XP by `passed_beats / total_beats` so failed beats reduce
    the reward proportionally. A run of 3-of-4 passes nets 75% of base XP.
    All-fail completion still nets 0 XP (item also gated below).
    """
    base = _xp_for_total_dc(int(storyline.get("total_dc") or 0))
    beats = storyline.get("beats") or []
    if not beats:
        return base
    passed = sum(1 for b in beats if b.get("status") == "passed")
    ratio = passed / float(len(beats))
    # Round to nearest 25 for cleanliness; never below 0.
    return max(0, int(round(base * ratio / 25)) * 25)


async def generate_storyline_reward(
    campaign: Dict,
    character: Dict,
    storyline: Dict,
    player_intent: Optional[str] = None,
) -> Dict:
    """LLM-themed completion reward. XP is SCALED by passed-beat ratio.
    `item`, `title`, and `description` come from the LLM when available;
    item is only awarded when at least half the beats passed.
    """
    total_dc = int(storyline.get("total_dc") or 0)
    xp = _scaled_xp(storyline)
    beats = storyline.get("beats") or []
    passed = sum(1 for b in beats if b.get("status") == "passed")
    failed = sum(1 for b in beats if b.get("status") == "failed")
    pass_ratio = passed / float(len(beats)) if beats else 0
    # Item is only awarded if at least half the beats passed.
    award_item = pass_ratio >= 0.5

    fallback = {
        "xp": xp,
        "passed": passed,
        "failed": failed,
        "title": storyline.get("title") or "Investigation Resolved",
        "description": (
            f"You closed the thread you started pulling. Word of your work "
            f"will travel quietly through {((campaign.get('world') or {}).get('starting_town') or {}).get('name', 'the district')}."
        ),
        "item": None,
        "tone": "satisfaction" if pass_ratio >= 0.5 else "bitter",
    }

    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        beat_summary = "\n".join(
            f"- {b.get('title','')}: {b.get('outcome_text') or b.get('description','')}"
            for b in (storyline.get("beats") or [])
        )
        intent = campaign.get("intent") or {}

        item_schema = (
            '{"name": "...", "description": "...", "kind": "item|info|favor|key"}'
            if award_item else 'null'
        )
        intent_block = (
            f"=== WHAT THE PLAYER WAS REALLY AFTER ===\n{player_intent}\n"
            "The reward MUST serve this specific goal. If they sought protection, give "
            "them that person's loyalty or a token of it. If they sought closure, give "
            "them the final piece that makes it real. If they failed their true goal, "
            "the closing line should acknowledge what almost was — not just that they "
            "finished the task. Never give generic loot when a specific meaningful "
            "reward is possible.\n\n"
            if player_intent else ""
        )
        prompt = (
            "The player has resolved an investigation chain. Generate a CLOSING REWARD "
            "that feels earned by the actual beats they played through. The reward "
            "should reflect the BEAT OUTCOMES below — celebrate passes, acknowledge "
            "failures honestly. If the player failed half or more of the beats, the "
            "tone should turn bittersweet or grim and NO item should be awarded.\n\n"
            f"=== STORYLINE ===\nTitle: {storyline.get('title','')}\n{beat_summary}\n\n"
            f"{intent_block}"
            f"=== OUTCOME ===\nPassed: {passed} / {len(beats)} | Failed: {failed}\n"
            f"=== CAMPAIGN TONE ===\n{intent.get('tone','Balanced')} | {intent.get('focus','Mystery')}\n\n"
            f"=== TOTAL DIFFICULTY ===\nDC sum: {total_dc} (player will receive {xp} XP separately)\n\n"
            "=== RULES ===\n"
            f"- {'Award' if award_item else 'DO NOT award'} an item.\n"
            "- 1 short closing line (<=160 chars) that lands the resolution as narrative — "
            "  Mercer-style, restrained, no fate talk.\n"
            "- NO XP number in the closing line; XP is shown by the UI.\n"
            "- Output strict JSON, no code fence.\n\n"
            "=== OUTPUT ===\n"
            "{\n"
            f"  \"item\": {item_schema},\n"
            "  \"description\": \"closing line\",\n"
            "  \"tone\": \"satisfaction|grim|hopeful|bitter|reverent\"\n"
            "}\n"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"storyline-reward-{uuid4()}",
            system_message="You are a senior D&D campaign designer. Output strict JSON only.",
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        item = data.get("item") if isinstance(data.get("item"), dict) else None
        if item and award_item:
            item = {
                "name": str(item.get("name") or "Token of the Investigation")[:60],
                "description": str(item.get("description") or "")[:240],
                "kind": str(item.get("kind") or "item")[:16],
            }
        else:
            item = None
        return {
            "xp": xp,
            "passed": passed,
            "failed": failed,
            "title": storyline.get("title") or fallback["title"],
            "description": str(data.get("description") or fallback["description"])[:200],
            "item": item,
            "tone": str(data.get("tone") or fallback["tone"])[:24],
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Reward LLM failed, using template: {exc}")
        return fallback


# -------------------- progression helpers --------------------


def advance_storyline(storyline: Dict, beat_index: int, outcome: str, outcome_text: Optional[str] = None) -> Dict:
    """Mutate `storyline` in place: mark beat `beat_index` with the given outcome,
    activate the next beat, or mark the storyline complete if it was the last beat.

    For OPEN-ENDED storylines (the new scene-driven flow), the caller is
    responsible for appending the next dynamically-generated beat or marking
    completion. We just mark the resolved beat and bump `current_beat` past
    it; status is left 'active' for open-ended chains regardless.

    Returns the (mutated) storyline dict for convenience.
    """
    if outcome not in {"passed", "failed", "skipped"}:
        outcome = "passed"
    beats = storyline.get("beats") or []
    if not (0 <= beat_index < len(beats)):
        return storyline

    beat = beats[beat_index]
    beat["status"] = outcome
    if outcome_text:
        beat["outcome_text"] = outcome_text[:240]
    storyline["updated_at"] = datetime.now(timezone.utc)

    open_ended = bool(storyline.get("open_ended"))

    # Activate next pending beat (legacy multi-beat storylines)
    next_idx = beat_index + 1
    if next_idx < len(beats):
        beats[next_idx]["status"] = "active"
        storyline["current_beat"] = next_idx
    elif open_ended:
        # Caller will either append a new beat (current_beat -> last index) or
        # mark complete. Leave current_beat pointing at the just-resolved beat
        # so we don't index out of range mid-flight.
        storyline["current_beat"] = beat_index
    else:
        storyline["status"] = "completed"
        storyline["current_beat"] = beat_index
    return storyline


def storyline_to_dict(storyline: Dict) -> Dict:
    """Strip _id / normalize datetimes for transport."""
    out = {k: v for k, v in storyline.items() if k != "_id"}
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


# -------------------- failure narration --------------------


_COMPLICATION_FALLBACKS = {
    "Investigation": "You comb the spot a second time and find what you missed: nothing. The trail's gone cold, and a faint sound behind you reminds you that someone else may have been watching.",
    "Perception": "Your gaze slides across the scene without catching. By the time you realize what you missed, the moment is gone — and you've spent it in plain sight.",
    "Insight": "You read them wrong. Whatever you thought you saw in their face, you don't see it now — and the silence that follows is heavier than any answer.",
    "Persuasion": "Your words land badly. The person you came to convince looks past you, decision already made. The room cools by a degree.",
    "Deception": "The lie sits on your tongue, but the listener tilts their head a fraction, and you feel it slip. You'll have to mean what you say next.",
    "Intimidation": "Your threat lands without weight. They've heard worse from worse, and now they're certain you bluffed.",
    "Stealth": "A boot scuff. A breath at the wrong moment. You feel the shift before you see it — eyes finding you in the dim.",
    "Athletics": "Your grip slips. Whatever you reached for is on the ground, and so is some of your dignity. A bruise will surface tomorrow.",
    "Sleight of Hand": "Your fingers move a heartbeat too late. You feel the brush of a sleeve against yours — they noticed.",
    "Arcana": "The runes refuse to resolve. What seemed familiar a breath ago now reads as gibberish, and the moment slips away.",
    "History": "The detail that connected it all has fallen out of your memory like a stone through silk. You'll have to piece it together another way.",
    "Nature": "The signs lie. What you read as one thing is another, and you've spent breath chasing the wrong shape.",
    "Survival": "The wind shifts, and what you tracked is downwind now. Your trail goes nowhere clean.",
}


async def generate_complication_beat(
    intent,
    world: Dict,
    character: Optional[Dict],
    storyline: Dict,
    beat: Dict,
    mode: str = "fail-forward",
) -> str:
    """Produce a 1-2 sentence Mercer-style complication beat for a failed
    check. Lands in the Adventure Log so failure has narrative weight.

    `mode` is one of:
      - "fail-forward" : the story moves on with this failure baked in
      - "press-on"     : the player has chosen to retry; complication = a cost paid

    Falls back to a deterministic template when the LLM is unavailable.
    """
    fallback_base = _COMPLICATION_FALLBACKS.get(beat.get("check_type") or "", _COMPLICATION_FALLBACKS["Investigation"])
    fallback = (
        fallback_base
        if mode == "fail-forward"
        else (fallback_base + " You steel yourself for another try, but it costs you.")
    )

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        hero_name = "the hero"
        if character:
            identity = character.get("identity") or {}
            hero_name = identity.get("name") or hero_name
        beats = storyline.get("beats") or []
        beat_idx = next((i for i, b in enumerate(beats) if b.get("title") == beat.get("title")), -1)

        prompt = (
            "Narrate the COMPLICATION when a D&D player just FAILED an ability check "
            "in the middle of an investigation. 1-2 sentences. Second person, present tense, "
            "Mercer-cinematic, restrained.\n\n"
            f"=== STORYLINE ===\nTitle: {storyline.get('title','')}\n"
            f"Beat {beat_idx+1} of {len(beats)}: {beat.get('title','')}\n"
            f"Task: {beat.get('task','')}\n"
            f"Check: {beat.get('check_type','Investigation')} DC {beat.get('dc',12)}\n"
            f"Beat description: {beat.get('description','')}\n\n"
            f"=== HERO ===\n{hero_name}\n"
            f"Campaign tone: {_intent_get(intent,'tone','Balanced')} | focus: {_intent_get(intent,'focus','Mystery')} | danger: {_intent_get(intent,'danger','Medium')}\n\n"
            "=== MODE ===\n"
            f"{'fail-forward — the story moves on; the failure leaves a mark on the next beat (witness fled, lock jammed, lie noticed, wound taken).' if mode == 'fail-forward' else 'press-on — the player will try again; the complication is the COST paid for getting another shot (a wound, a moment burned, a small debt).'}\n\n"
            "=== RULES ===\n"
            "- 1-2 sentences. 22-50 words.\n"
            "- ONE concrete sensory detail (a sound, a smell, a flicker of expression, a scuff, a drop of blood).\n"
            "- Make the consequence visible — the player should feel something has changed.\n"
            "- NO clichés ('fate', 'the gods', 'a chill runs', 'destiny').\n"
            "- No quotation marks around the passage. Output only the beat."
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"complication-{uuid4()}",
            system_message=(
                "You are a senior D&D narrator (Matt-Mercer style): cinematic, grounded, "
                "restrained. You narrate failure with weight, never with melodrama."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith('"') and text.endswith('"') and len(text) > 2:
            text = text[1:-1].strip()
        return text or fallback
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Complication beat generation failed: {exc}")
        return fallback


# -------------------- creative approach judging --------------------


async def judge_creative_approach(
    intent,
    world: Dict,
    character: Optional[Dict],
    storyline: Dict,
    beat: Dict,
    approach_text: str,
) -> Dict:
    """Player typed an alternative approach to the current beat. Have the
    DM judge whether it works.

    Returns:
      {
        "outcome": "passed" | "partial" | "failed",
        "narration": "1-2 sentence DM beat describing what happens",
        "applied_check": {"type": "<skill>", "dc": int} | null,
      }

    'partial' = the approach worked but at a cost; we treat it as 'passed' for
    progression but the narration captures the price (the storyline still
    advances; XP still credited for this beat).
    """
    fallback = {
        "outcome": "partial",
        "narration": (
            "Your approach works — partly. The path you chose isn't the one the "
            "obstacle was built for, and the seams of it leave marks on you both."
        ),
        "applied_check": None,
    }
    if not (approach_text or "").strip():
        return fallback

    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        return fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        hero_bits = ""
        if character:
            identity = character.get("identity") or {}
            cls = character.get("class") or character.get("class_") or {}
            bg = character.get("background") or {}
            hero_bits = (
                f"Hero: {identity.get('name','the hero')} ({(cls.get('key') or 'adventurer').lower()}, "
                f"{(bg.get('key') or 'wanderer').lower()} background)"
            )

        prompt = (
            "A D&D player has proposed a CREATIVE alternative approach to the current "
            "investigation beat instead of just rolling the suggested check. Judge whether "
            "it would plausibly succeed.\n\n"
            "=== CURRENT BEAT ===\n"
            f"Title: {beat.get('title','')}\n"
            f"Original task: {beat.get('task','')}\n"
            f"Original check: {beat.get('check_type','Investigation')} DC {beat.get('dc',12)}\n"
            f"Beat description: {beat.get('description','')}\n\n"
            f"=== STORYLINE CONTEXT ===\nTitle: {storyline.get('title','')}\n"
            f"Tone: {_intent_get(intent,'tone','Balanced')} | focus: {_intent_get(intent,'focus','Mystery')} | danger: {_intent_get(intent,'danger','Medium')}\n"
            f"{hero_bits}\n\n"
            "=== PLAYER'S APPROACH ===\n"
            f"\"{approach_text.strip()[:600]}\"\n\n"
            "=== RULES ===\n"
            "- Decide outcome: 'passed' (clean success), 'partial' (it works but at a cost), "
            "  or 'failed' (the approach doesn't work for solid in-fiction reasons).\n"
            "- Be GENEROUS with creativity — reward inventive thinking. Only return 'failed' "
            "  if the approach contradicts the fiction (impossible, breaks physics, ignores "
            "  what the player knows about the scene). 'partial' is a good middle ground.\n"
            "- If the approach naturally calls for a different ability check than the original, "
            "  set applied_check = {type, dc}; otherwise null.\n"
            "- Narration: 1-2 sentences, second person, Mercer-cinematic. Show what happens.\n"
            "- NO clichés ('the gods smile', 'fate aligns', etc.).\n"
            "- Output strict JSON, no code fence.\n\n"
            "=== OUTPUT ===\n"
            "{\n"
            "  \"outcome\": \"passed|partial|failed\",\n"
            "  \"narration\": \"...\",\n"
            "  \"applied_check\": {\"type\": \"...\", \"dc\": 10} | null\n"
            "}"
        )
        chat = LlmChat(
            api_key=api_key,
            session_id=f"creative-judge-{uuid4()}",
            system_message=(
                "You are a senior D&D DM judging creative player solutions. You reward "
                "inventive thinking and only call something a failure when the fiction "
                "demands it. Output strict JSON only."
            ),
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=prompt))) or ""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        try:
            data = _json.loads(text)
        except Exception:
            s, e = text.find("{"), text.rfind("}")
            data = _json.loads(text[s:e + 1]) if s != -1 and e > s else {}

        outcome = (data.get("outcome") or "partial").strip().lower()
        if outcome not in {"passed", "partial", "failed"}:
            outcome = "partial"
        narration = (data.get("narration") or "").strip().strip('"')[:280] or fallback["narration"]
        applied = data.get("applied_check") if isinstance(data.get("applied_check"), dict) else None
        if applied:
            t = str(applied.get("type") or "").strip()
            try:
                d = int(applied.get("dc") or beat.get("dc", 12))
            except Exception:
                d = beat.get("dc", 12)
            if t and t in _VALID_CHECK_TYPES:
                applied = {"type": t, "dc": max(8, min(20, d))}
            else:
                applied = None
        return {"outcome": outcome, "narration": narration, "applied_check": applied}
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Creative-approach judge failed: {exc}")
        return fallback

