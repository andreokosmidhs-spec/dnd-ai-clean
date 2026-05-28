"""NPC Voice Casting Service.

Assigns a permanent Kokoro voice to each NPC based on semantic tags,
applies emotional modifiers at generation time, and caches generated audio
so repeated dialogue lines are instant.

Flow:
  AI DM generates voiceTags  →  match_voice()  →  assign_voice_to_npc()
  Player triggers dialogue    →  generate_npc_speech()  →  WAV bytes

Voice profiles are stored at:
  world_state["npc_voice_profiles"][npc_id] = { assignedVoice, pitch, speed, voiceTags, emotionalStyle }

Audio cache (session-scoped):
  In-memory dict  →  instant replay for greetings, barks, repeated lines.
"""

import hashlib
import io
import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ── Registry ─────────────────────────────────────────────────────────────────

_REGISTRY_PATH = Path(__file__).parent.parent / "data" / "voices" / "registry.json"
_registry: Optional[list] = None

# ── Tag-match weights ─────────────────────────────────────────────────────────
# Gender must match; age group very important; accent, core traits, class next.

_WEIGHTS: dict[str, int] = {
    # Gender (highest — wrong gender is disqualifying)
    "female": 20, "male": 20,
    # Age group
    "child": 14, "young": 12, "young_adult": 12, "middle_aged": 12,
    "mature": 12, "elderly": 12, "old": 12, "elder": 12,
    # Accent
    "british": 10, "american": 6,
    # Core vocal qualities
    "deep": 8, "authoritative": 8, "commanding": 8,
    "sharp": 6, "warm": 6, "elegant": 6, "refined": 6,
    "sophisticated": 6, "eloquent": 6, "bright": 5, "soft": 5,
    "dry": 5, "calm": 5, "energetic": 5,
    # Energy / attitude
    "low_energy": 4, "high_energy": 4, "gravitas": 5,
    "tired": 4, "cynical": 4, "guarded": 4, "secretive": 4, "cold": 4,
    # Social class
    "noble": 5, "upper_class": 5, "regal": 6, "powerful": 5,
    "working_class": 4, "urban": 3,
    # Personality/archetype tags
    "noble": 5, "rogue": 4, "merchant": 3, "priest": 4,
    "soldier": 3, "bard": 3, "scholar": 3,
    "approachable": 3, "trustworthy": 3, "reliable": 3, "confident": 3,
    "ambitious": 3, "composed": 4, "controlled": 4, "measured": 4,
    "articulate": 4, "educated": 4, "professional": 4,
    "friendly": 3, "casual": 3, "conversational": 3,
    "hopeful": 2, "empathetic": 2, "nurturing": 2, "cheerful": 2,
    "straightforward": 2, "steady": 2,
}

# ── Emotional modifiers ───────────────────────────────────────────────────────

_EMOTION_MODS: dict[str, dict] = {
    "neutral":      {"speed_mult": 1.00, "pitch_semi": 0},
    "calm":         {"speed_mult": 0.93, "pitch_semi": 0},
    "happy":        {"speed_mult": 1.05, "pitch_semi": 1},
    "excited":      {"speed_mult": 1.12, "pitch_semi": 1},
    "angry":        {"speed_mult": 1.10, "pitch_semi": -2},
    "furious":      {"speed_mult": 1.20, "pitch_semi": -3},
    "nervous":      {"speed_mult": 1.15, "pitch_semi": 2},
    "fearful":      {"speed_mult": 1.18, "pitch_semi": 2},
    "sad":          {"speed_mult": 0.85, "pitch_semi": -1},
    "grieving":     {"speed_mult": 0.78, "pitch_semi": -2},
    "tired":        {"speed_mult": 0.88, "pitch_semi": -1},
    "whispering":   {"speed_mult": 0.80, "pitch_semi": 0},
    "contemptuous": {"speed_mult": 0.95, "pitch_semi": -1},
    "suspicious":   {"speed_mult": 0.92, "pitch_semi": -1},
    "impressed":    {"speed_mult": 0.98, "pitch_semi": 1},
    "serious":      {"speed_mult": 0.96, "pitch_semi": 0},
}

# ── In-memory audio cache ─────────────────────────────────────────────────────
# key: "{npc_id}:{emotion}:{text_hash8}" → WAV bytes
_audio_cache: dict[str, bytes] = {}
# Tier-2 bark cache — short lines cached on NPC activation
_bark_cache: dict[str, bytes] = {}


# ── Registry helpers ──────────────────────────────────────────────────────────

def load_registry() -> list:
    global _registry
    if _registry is not None:
        return _registry
    try:
        with open(_REGISTRY_PATH) as f:
            _registry = json.load(f)
        logger.info(f"[voice] Registry loaded: {len(_registry)} voices")
    except Exception as exc:
        logger.error(f"[voice] Registry load failed: {exc}")
        _registry = []
    return _registry


def get_registry() -> list:
    return load_registry()


# ── Voice matching ────────────────────────────────────────────────────────────

def match_voice(npc_tags: list[str]) -> Optional[dict]:
    """Score all registry voices against npc_tags. Return best match."""
    registry = load_registry()
    if not registry:
        return None

    npc_tag_set = set(t.lower() for t in npc_tags)
    best = None
    best_score = -1

    for voice in registry:
        voice_tags = set(t.lower() for t in voice.get("tags", []))
        score = sum(_WEIGHTS.get(tag, 2) for tag in npc_tag_set if tag in voice_tags)
        if score > best_score:
            best_score = score
            best = {**voice, "_score": score}

    return best


def _infer_tags_from_identity(identity: dict) -> list[str]:
    """Fallback: derive minimal voice tags from NPC identity fields."""
    tags: list[str] = []

    gender = (identity.get("gender") or "").lower()
    if "female" in gender or "woman" in gender or "girl" in gender:
        tags.append("female")
    elif "male" in gender or "man" in gender or "boy" in gender:
        tags.append("male")

    age = (identity.get("ageGroup") or "").lower()
    age_map = {
        "child": "child", "teen": "young", "young": "young",
        "adult": "young_adult", "middle": "middle_aged",
        "old": "elderly", "elderly": "elderly", "ancient": "elderly",
    }
    for key, tag in age_map.items():
        if key in age:
            tags.append(tag)
            break

    social = (identity.get("socialClass") or "").lower()
    if any(k in social for k in ("noble", "aristocrat", "royal")):
        tags.extend(["noble", "elegant", "articulate"])
    elif any(k in social for k in ("working", "peasant", "commoner")):
        tags.append("working_class")

    role = (identity.get("role") or "").lower()
    role_tags = {
        "guard": "soldier", "soldier": "soldier", "knight": "soldier",
        "merchant": "merchant", "trader": "merchant",
        "priest": "priest", "cleric": "priest", "monk": "priest",
        "bard": "bard", "performer": "bard",
        "rogue": "rogue", "thief": "rogue", "spy": "rogue",
        "noble": "noble", "lord": "noble", "lady": "noble",
        "scholar": "scholar", "mage": "scholar", "wizard": "scholar",
    }
    for key, tag in role_tags.items():
        if key in role:
            tags.append(tag)

    return tags


# ── Voice assignment ──────────────────────────────────────────────────────────

def assign_voice_to_npc(npc: dict) -> dict:
    """Match voice tags to the best Kokoro voice. Return updated voiceProfile.

    This should be called once on NPC first activation and the result stored
    permanently in world_state.npc_voice_profiles[npc_id].
    """
    voice_profile = (npc.get("voiceProfile") or {}).copy()
    voice_tags = voice_profile.get("voiceTags") or []

    if not voice_tags:
        identity = npc.get("identity") or {}
        voice_tags = _infer_tags_from_identity(identity)

    best = match_voice(voice_tags)
    if not best:
        logger.warning(f"[voice] No match found for tags {voice_tags}")
        return voice_profile

    voice_profile["assignedVoice"] = best["voiceId"]
    voice_profile["pitch"] = best.get("basePitch", 0)
    voice_profile["speed"] = best.get("baseSpeed", 1.0)
    voice_profile["voiceTags"] = voice_tags
    voice_profile["_matchScore"] = best.get("_score", 0)
    voice_profile.setdefault("emotionalStyle", "neutral")

    logger.info(
        f"[voice] Assigned {best['voiceId']} to NPC "
        f"'{npc.get('name', '?')}' (score={best.get('_score', 0)}, tags={voice_tags})"
    )
    return voice_profile


# ── Emotion helpers ───────────────────────────────────────────────────────────

def get_emotion_modifiers(emotion: str) -> dict:
    return _EMOTION_MODS.get(emotion.lower(), _EMOTION_MODS["neutral"])


def get_supported_emotions() -> list[str]:
    return list(_EMOTION_MODS.keys())


# ── Pitch shifting (numpy-based, no extra deps) ───────────────────────────────

def _pitch_shift(samples: np.ndarray, sample_rate: int, semitones: float) -> np.ndarray:
    """Pitch shift via resampling. Duration preserved via second resample."""
    if abs(semitones) < 0.25:
        return samples

    factor = 2.0 ** (semitones / 12.0)
    target_len = max(1, int(round(len(samples) / factor)))

    # Resample to change pitch (also changes speed)
    indices = np.linspace(0, len(samples) - 1, target_len)
    shifted = np.interp(indices, np.arange(len(samples)), samples)

    # Resample back to original length to restore speed
    restore_indices = np.linspace(0, len(shifted) - 1, len(samples))
    return np.interp(restore_indices, np.arange(len(shifted)), shifted)


# ── Speech generation ─────────────────────────────────────────────────────────

def _cache_key(npc_id: str, text: str, emotion: str) -> str:
    text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
    return f"{npc_id}:{emotion}:{text_hash}"


def generate_npc_speech(
    npc_id: str,
    text: str,
    voice_profile: dict,
    emotion: str = "neutral",
    use_cache: bool = True,
    tier: int = 1,
) -> Optional[bytes]:
    """Generate WAV audio for an NPC line with emotional modifiers applied.

    Tier 1 (main speaking NPC) → realtime + cached.
    Tier 2 (nearby NPC barks)  → cached only after first generation.
    Tier 3 (crowds)            → return None, use ambient loops externally.

    Returns WAV bytes or None on failure.
    """
    if tier >= 3:
        return None

    ck = _cache_key(npc_id, text, emotion)
    if use_cache and ck in _audio_cache:
        logger.debug(f"[voice] cache hit: {ck}")
        return _audio_cache[ck]

    assigned = voice_profile.get("assignedVoice")
    if not assigned:
        logger.warning(f"[voice] NPC {npc_id} has no assignedVoice")
        return None

    base_speed = float(voice_profile.get("speed", 1.0))
    base_pitch = float(voice_profile.get("pitch", 0))

    mods = get_emotion_modifiers(emotion)
    final_speed = round(base_speed * mods["speed_mult"], 3)
    final_pitch = base_pitch + mods["pitch_semi"]

    from services.tts_service import _get_kokoro
    kokoro = _get_kokoro()
    if kokoro is None:
        return None

    try:
        import soundfile as sf

        samples, sample_rate = kokoro.create(
            text, voice=assigned, speed=final_speed, lang="en-us"
        )
        arr = np.array(samples, dtype=np.float32)

        if abs(final_pitch) >= 0.25:
            arr = _pitch_shift(arr, sample_rate, final_pitch).astype(np.float32)

        buf = io.BytesIO()
        sf.write(buf, arr, sample_rate, format="WAV", subtype="PCM_16")
        buf.seek(0)
        audio_bytes = buf.read()

        if use_cache:
            _audio_cache[ck] = audio_bytes

        logger.debug(
            f"[voice] Generated {len(audio_bytes)//1024} KB for npc={npc_id} "
            f"voice={assigned} emotion={emotion} speed={final_speed:.2f} pitch={final_pitch:+.1f}"
        )
        return audio_bytes

    except Exception as exc:
        logger.error(f"[voice] Speech generation failed for npc={npc_id}: {exc}")
        return None


# ── Cache management ──────────────────────────────────────────────────────────

def cache_bark(npc_id: str, text: str, emotion: str, voice_profile: dict) -> bool:
    """Pre-generate and cache a short bark for a Tier-2 NPC."""
    audio = generate_npc_speech(npc_id, text, voice_profile, emotion, use_cache=True, tier=1)
    return audio is not None


def clear_npc_cache(npc_id: Optional[str] = None) -> int:
    """Clear cached audio. If npc_id given, only clear that NPC's entries."""
    removed = 0
    if npc_id:
        keys = [k for k in _audio_cache if k.startswith(f"{npc_id}:")]
    else:
        keys = list(_audio_cache.keys())
    for k in keys:
        del _audio_cache[k]
        removed += 1
    logger.info(f"[voice] Cleared {removed} cached audio entries")
    return removed


def cache_stats() -> dict:
    total = len(_audio_cache)
    size_kb = sum(len(v) for v in _audio_cache.values()) // 1024
    return {"entries": total, "size_kb": size_kb}
