"""Mission Types — structured storyline blueprints.

A mission type is an ordered list of `phases` that constrain the shape of
a storyline:

  Heist:        Discovery → Scouting → Tools & Allies → Plan & Execution
  Rescue:       Locate → Approach → Confrontation → Extraction
  Assassination:Mark → Surveillance → Setup → Strike
  Political:    Power Map → Leverage → Maneuver → Reveal

Each phase carries:
  - goal:               narrative purpose ("Player must learn the target's
                        name and where it sleeps")
  - check_palette:      preferred check types ([Investigation, Perception])
  - reveal_type:        knowledge | social | action
  - target_palette:     card types this phase mints  ([npc, item, location])
  - typical_dc_range:   [low, high]   e.g. [10, 14] for Discovery
  - min_beats/max_beats:1..3
  - signature_rewards:  cards that may drop in this phase

Mission types can be:
  - system   (seeded at boot, shared across all campaigns)
  - user     (owner_id == "campaign:<campaign_id>", visible only there)

The blueprint is injected verbatim into the storyline generator prompt
so beats follow the arc structure while the prose stays creative.

Schema (`mission_types` collection):
  {
    id: str,
    slug: str,                          # 'heist' | 'rescue' | ...
    name: str,                          # 'Heist'
    icon: str,                          # '🎯'
    description: str,                   # 1-3 sentence brief for the DM
    phases: List[PhaseBlueprint],
    signature_rewards: List[str],
    signature_complications: List[str],
    owner_id: str,                      # 'system' or 'campaign:<id>'
    is_system: bool,
    created_at: datetime,
  }
"""
from __future__ import annotations

import json as _json
import logging
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# System seeds — the 4 canonical mission types.
# Slug + name + phases + signature flavor. Slugs are stable IDs the frontend
# can hard-code while the DB id is uuid-based.
# --------------------------------------------------------------------------

SYSTEM_MISSION_TYPES: List[Dict] = [
    {
        "slug": "heist",
        "name": "Heist",
        "icon": "🎯",
        "description": (
            "A high-stakes theft. The arc moves from learning the target "
            "exists, to mapping defences, to acquiring the tools and "
            "allies, to a final execution where everything converges or "
            "spectacularly falls apart."
        ),
        "phases": [
            {
                "name": "Discovery",
                "goal": "Player learns the target exists, what it is, and roughly where. Reveal 1-2 NPCs who know something.",
                "check_palette": ["Investigation", "Perception", "Persuasion"],
                "reveal_type": "knowledge",
                "target_palette": ["item", "location", "npc"],
                "typical_dc_range": [10, 14],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["clue card", "informant NPC"],
            },
            {
                "name": "Scouting",
                "goal": "Player learns who guards the target, the patrol/lock/trap layout, the history and rivalries around it.",
                "check_palette": ["Investigation", "Stealth", "Perception", "Insight"],
                "reveal_type": "knowledge",
                "target_palette": ["npc", "location", "faction"],
                "typical_dc_range": [12, 16],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["map card", "patrol schedule", "rival faction lead"],
            },
            {
                "name": "Tools & Allies",
                "goal": "Player must acquire a tool, recruit a specialist, or earn a favour required for the heist. Side-quests live here.",
                "check_palette": ["Persuasion", "Sleight of Hand", "Deception", "Athletics"],
                "reveal_type": "social",
                "target_palette": ["item", "npc"],
                "typical_dc_range": [12, 16],
                "min_beats": 1,
                "max_beats": 3,
                "signature_rewards": ["tool card", "specialist NPC", "favour token"],
            },
            {
                "name": "Plan & Execution",
                "goal": "The heist itself. Stealth, timing, improvisation under pressure; success or fail-forward to a chase or fallout.",
                "check_palette": ["Stealth", "Sleight of Hand", "Deception", "Athletics", "Acrobatics"],
                "reveal_type": "action",
                "target_palette": ["item", "location"],
                "typical_dc_range": [13, 18],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["stolen item card", "infamy boost", "criminal contact"],
            },
        ],
        "signature_rewards": ["stolen-item card", "criminal contact", "infamy boost"],
        "signature_complications": [
            "the target is moved",
            "a rival crew got there first",
            "a guard recognizes the player",
            "the fence won't take the item",
        ],
    },
    {
        "slug": "rescue",
        "name": "Rescue",
        "icon": "🛟",
        "description": (
            "Someone is being held against their will. The arc moves from "
            "discovering they're missing, to finding them, to getting "
            "past whoever holds them, to escape under pursuit."
        ),
        "phases": [
            {
                "name": "Locate",
                "goal": "Player confirms who is missing, where they were taken, and roughly who took them.",
                "check_palette": ["Investigation", "Persuasion", "Insight", "Perception"],
                "reveal_type": "knowledge",
                "target_palette": ["npc", "location"],
                "typical_dc_range": [10, 14],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["witness NPC", "location card"],
            },
            {
                "name": "Approach",
                "goal": "Player chooses an angle: stealth, social, force, or trickery. Negotiate with intermediaries or scout the holding site.",
                "check_palette": ["Stealth", "Persuasion", "Deception", "Survival"],
                "reveal_type": "social",
                "target_palette": ["npc", "faction"],
                "typical_dc_range": [12, 16],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["safe-passage favour", "ally NPC"],
            },
            {
                "name": "Confrontation",
                "goal": "Player reaches the captor(s) — a tense parley, a fight, or a desperate stealth bypass.",
                "check_palette": ["Intimidation", "Persuasion", "Athletics", "Stealth"],
                "reveal_type": "action",
                "target_palette": ["npc", "location"],
                "typical_dc_range": [13, 17],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["captor's secret", "evidence card"],
            },
            {
                "name": "Extraction",
                "goal": "Get the rescued person OUT — chase, pursuit, or escape under fire. Final tension.",
                "check_palette": ["Athletics", "Acrobatics", "Survival", "Insight"],
                "reveal_type": "action",
                "target_palette": ["npc", "location"],
                "typical_dc_range": [14, 18],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["rescued NPC bond", "owed favour"],
            },
        ],
        "signature_rewards": ["rescued NPC", "owed favour", "captor's secret"],
        "signature_complications": [
            "the captive is wounded and slows you down",
            "a second captor returns",
            "the captive doesn't want to leave",
            "you're spotted by patrols",
        ],
    },
    {
        "slug": "assassination",
        "name": "Assassination",
        "icon": "🗡",
        "description": (
            "A targeted kill. The arc moves from identifying the mark and "
            "their justification, to surveillance and pattern-learning, "
            "to setup of the kill location, to the strike — with the "
            "ability to abort or be turned at any phase."
        ),
        "phases": [
            {
                "name": "Mark",
                "goal": "Player confirms the target's name, location, public role, and who wants them dead — and why.",
                "check_palette": ["Investigation", "Persuasion", "Insight"],
                "reveal_type": "knowledge",
                "target_palette": ["npc", "faction"],
                "typical_dc_range": [10, 14],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["contract card", "patron NPC"],
            },
            {
                "name": "Surveillance",
                "goal": "Player learns the target's routine, bodyguards, weaknesses, and the political fallout of their death.",
                "check_palette": ["Stealth", "Perception", "Investigation", "Insight"],
                "reveal_type": "knowledge",
                "target_palette": ["npc", "location"],
                "typical_dc_range": [12, 16],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["routine card", "bodyguard intel"],
            },
            {
                "name": "Setup",
                "goal": "Player positions tools, picks the kill site, plants an escape route or alibi. Optional side-quest to acquire poison / scroll / blade.",
                "check_palette": ["Sleight of Hand", "Stealth", "Deception"],
                "reveal_type": "action",
                "target_palette": ["item", "location"],
                "typical_dc_range": [12, 16],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["assassin's tool card", "alibi NPC"],
            },
            {
                "name": "Strike",
                "goal": "The kill itself — clean, messy, or aborted. Fail-forward to chase, capture, or moral fallout.",
                "check_palette": ["Stealth", "Deception", "Athletics"],
                "reveal_type": "action",
                "target_palette": ["npc", "location"],
                "typical_dc_range": [14, 19],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["mark's effect", "blood-money", "infamy"],
            },
        ],
        "signature_rewards": ["mark's signet", "blood-money", "patron's favour"],
        "signature_complications": [
            "the mark switches doubles",
            "a witness must be silenced",
            "the patron betrays you",
            "the mark turns out to be sympathetic",
        ],
    },
    {
        "slug": "political_intrigue",
        "name": "Political Intrigue",
        "icon": "🏛",
        "description": (
            "Power, leverage, betrayal. The arc moves from mapping the "
            "factions and their grudges, to acquiring leverage, to "
            "maneuvering in the open court, to the reveal that reshapes "
            "the political landscape."
        ),
        "phases": [
            {
                "name": "Power Map",
                "goal": "Player learns the major factions in play, their leaders, and the surface positions vs hidden alliances.",
                "check_palette": ["Investigation", "Persuasion", "Insight", "History"],
                "reveal_type": "knowledge",
                "target_palette": ["faction", "npc"],
                "typical_dc_range": [12, 15],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["faction dossier", "rumour card"],
            },
            {
                "name": "Leverage",
                "goal": "Player gains something to trade — a secret, a debt, a piece of evidence, a private letter.",
                "check_palette": ["Insight", "Deception", "Investigation", "Sleight of Hand"],
                "reveal_type": "social",
                "target_palette": ["item", "npc"],
                "typical_dc_range": [13, 16],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["evidence card", "blackmail item"],
            },
            {
                "name": "Maneuver",
                "goal": "Player works the room — banquets, council chambers, private gardens. Each move shifts a faction's posture.",
                "check_palette": ["Persuasion", "Deception", "Insight", "Performance"],
                "reveal_type": "social",
                "target_palette": ["npc", "faction"],
                "typical_dc_range": [13, 17],
                "min_beats": 1,
                "max_beats": 3,
                "signature_rewards": ["pledged ally", "shifted faction stance"],
            },
            {
                "name": "Reveal",
                "goal": "The public moment — a denouncement, a marriage offer, a vote, a betrayal made visible. The court's shape changes.",
                "check_palette": ["Persuasion", "Performance", "Intimidation", "Insight"],
                "reveal_type": "social",
                "target_palette": ["faction", "npc"],
                "typical_dc_range": [14, 18],
                "min_beats": 1,
                "max_beats": 2,
                "signature_rewards": ["title", "ally faction", "rival's downfall"],
            },
        ],
        "signature_rewards": ["title", "shifted faction stance", "private favour from a noble"],
        "signature_complications": [
            "a key witness retracts",
            "an unexpected faction enters the contest",
            "your leverage becomes leverage against you",
            "the court mood shifts overnight",
        ],
    },
]


# --------------------------------------------------------------------------
# CRUD helpers
# --------------------------------------------------------------------------


def _doc_from_dict(payload: Dict, owner_id: str = "system") -> Dict:
    return {
        "id": payload.get("id") or f"mt_{uuid4().hex[:10]}",
        "slug": str(payload["slug"]).lower().strip()[:40],
        "name": str(payload["name"]).strip()[:60],
        "icon": str(payload.get("icon") or "🎲")[:4],
        "description": str(payload.get("description") or "").strip()[:600],
        "phases": payload.get("phases") or [],
        "signature_rewards": payload.get("signature_rewards") or [],
        "signature_complications": payload.get("signature_complications") or [],
        "owner_id": owner_id,
        "is_system": owner_id == "system",
        "created_at": _now(),
    }


async def ensure_seeded(db) -> int:
    """Idempotently insert system mission types. Returns the count of
    newly-created docs (0 if everything was already present)."""
    coll = db["mission_types"]
    created = 0
    for spec in SYSTEM_MISSION_TYPES:
        slug = spec["slug"]
        existing = await coll.find_one({"slug": slug, "owner_id": "system"})
        if existing:
            continue
        await coll.insert_one(_doc_from_dict(spec, owner_id="system"))
        created += 1
    if created:
        logger.info(f"[mission_types] seeded {created} system blueprints")
    return created


async def list_mission_types(db, *, campaign_id: Optional[str] = None) -> List[Dict]:
    coll = db["mission_types"]
    query: Dict = {"$or": [{"owner_id": "system"}]}
    if campaign_id:
        query["$or"].append({"owner_id": f"campaign:{campaign_id}"})
    cursor = coll.find(query, {"_id": 0}).sort([("is_system", -1), ("name", 1)])
    return await cursor.to_list(length=200)


async def get_mission_type(db, *, mission_type_id: str) -> Optional[Dict]:
    return await db["mission_types"].find_one({"id": mission_type_id}, {"_id": 0})


async def get_mission_type_by_slug(db, *, slug: str, campaign_id: Optional[str] = None) -> Optional[Dict]:
    query: Dict = {"slug": slug}
    if campaign_id:
        query["$or"] = [
            {"owner_id": "system"},
            {"owner_id": f"campaign:{campaign_id}"},
        ]
    return await db["mission_types"].find_one(query, {"_id": 0})


async def create_mission_type(db, *, owner_id: str, data: Dict) -> Dict:
    doc = _doc_from_dict(data, owner_id=owner_id)
    await db["mission_types"].insert_one(dict(doc))
    return doc


async def delete_mission_type(db, *, mission_type_id: str, requester_owner: str) -> bool:
    """Only user-owned mission types can be deleted. System seeds are
    immutable. requester_owner must equal the doc's owner_id."""
    res = await db["mission_types"].delete_one(
        {"id": mission_type_id, "owner_id": requester_owner, "is_system": False}
    )
    return res.deleted_count > 0


# --------------------------------------------------------------------------
# LLM "from prompt" generator — player types a free-text description and
# the LLM emits a structured mission type they can review before saving.
# --------------------------------------------------------------------------


def _strip_json_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("json"):
            s = s[4:].lstrip()
    return s


async def generate_from_prompt(prompt: str) -> Optional[Dict]:
    """Single LLM call: free-text → structured mission_type dict.
    Returns None on failure; caller should surface a friendly error."""
    if not prompt or not prompt.strip():
        return None
    api_key = os.getenv("EMERGENT_LLM_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("mission_type generate_from_prompt: no API key")
        return None
    sys_msg = (
        "You are a senior D&D Dungeon Master designing a STRUCTURED MISSION TYPE "
        "blueprint. A mission type is a 3-5 phase arc that storylines of this "
        "type should follow. Each phase has a goal, check palette, reveal type, "
        "target palette (card types it mints), typical DC range, and beat count. "
        "Be tight and craft-focused. Output STRICT JSON only."
    )
    user_msg = (
        f"=== PLAYER PROMPT ===\n{prompt[:1000].strip()}\n\n"
        "=== TASK ===\n"
        "Emit a single mission_type JSON object. 3-5 phases is ideal. "
        "Phase goals must be CONCRETE (what the player must learn or do), not vague. "
        "check_palette uses standard D&D 5e check names. target_palette uses lowercase "
        "['item','npc','location','faction']. typical_dc_range is [low,high] within 8..20.\n\n"
        "=== OUTPUT (strict JSON, no code fence) ===\n"
        "{\n"
        "  \"slug\": \"<lowercase-with-hyphens, 3-20 chars>\",\n"
        "  \"name\": \"<Title Case, 2-4 words>\",\n"
        "  \"icon\": \"<1 emoji>\",\n"
        "  \"description\": \"<1-3 sentence brief for the DM>\",\n"
        "  \"phases\": [\n"
        "    {\n"
        "      \"name\": \"<Phase Name>\",\n"
        "      \"goal\": \"<concrete narrative goal>\",\n"
        "      \"check_palette\": [\"<check>\", \"<check>\"],\n"
        "      \"reveal_type\": \"<knowledge|social|action>\",\n"
        "      \"target_palette\": [\"<item|npc|location|faction>\"],\n"
        "      \"typical_dc_range\": [12, 15],\n"
        "      \"min_beats\": 1,\n"
        "      \"max_beats\": 2,\n"
        "      \"signature_rewards\": [\"<card type the player might earn>\"]\n"
        "    }\n"
        "  ],\n"
        "  \"signature_rewards\": [\"<top-level rewards across the arc>\"],\n"
        "  \"signature_complications\": [\"<things that can go wrong>\"]\n"
        "}"
    )
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=api_key,
            session_id=f"mt-gen-{uuid4()}",
            system_message=sys_msg,
        )
        chat.with_model("openai", "gpt-4o-mini")
        raw = (await chat.send_message(UserMessage(text=user_msg))) or ""
        s = _strip_json_fence(raw)
        try:
            data = _json.loads(s)
        except Exception:
            a, b = s.find("{"), s.rfind("}")
            data = _json.loads(s[a:b + 1]) if a != -1 and b > a else {}
        if not isinstance(data, dict) or not data.get("slug") or not data.get("phases"):
            return None
        return data
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"mission_type from-prompt failed: {exc}")
        return None


# --------------------------------------------------------------------------
# Prompt rendering — injected into storyline_service.draft_storyline so
# the LLM follows the blueprint's phase structure.
# --------------------------------------------------------------------------


def render_blueprint_for_prompt(mission_type: Optional[Dict]) -> str:
    """Render a mission_type as a markdown block the storyline generator
    can use to structure beats. Returns empty string when no type given.
    """
    if not mission_type or not mission_type.get("phases"):
        return ""
    lines: List[str] = [
        "=== MISSION TYPE BLUEPRINT (FOLLOW THE PHASE ARC) ===",
        f"Type: {mission_type.get('icon','')} {mission_type.get('name','')}",
        f"Brief: {mission_type.get('description','')}",
        "",
        "Phases (each storyline must include 1 beat per phase, in order — feel free to "
        "split a phase into 2 beats if min_beats=1, max_beats>=2):",
    ]
    for i, p in enumerate(mission_type["phases"], 1):
        checks = ", ".join(p.get("check_palette") or []) or "(any)"
        targets = ", ".join(p.get("target_palette") or []) or "(any)"
        dc = p.get("typical_dc_range") or [12, 15]
        rewards = ", ".join(p.get("signature_rewards") or [])
        lines.append(
            f"  PHASE {i} — {p.get('name','?')}: {p.get('goal','')}\n"
            f"     reveal_type: {p.get('reveal_type','knowledge')} | "
            f"check_palette: [{checks}] | target_palette: [{targets}] | "
            f"DC range: {dc[0]}–{dc[1]}\n"
            f"     mints rewards like: {rewards or '(open)'}"
        )
    sig_comp = mission_type.get("signature_complications") or []
    if sig_comp:
        lines.append("")
        lines.append("Signature complications (use on failed beats): " + "; ".join(sig_comp[:4]))
    lines.append("")
    lines.append(
        "Each generated beat MUST come from one of the phases above. "
        "Beats progress IN ORDER — Phase 1 beats come first, Phase 4 last. "
        "Use the phase's reveal_type and pick a check from its palette. "
        "DC must fall inside the phase's typical_dc_range. Targets must be "
        "of the phase's target_palette type."
    )
    return "\n".join(lines)
