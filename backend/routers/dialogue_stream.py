"""Real-Time NPC Dialogue Streaming.

WebSocket endpoint: /ws/dialogue/{campaign_id}/{npc_id}

Client sends:  {"text": "...", "emotion": "neutral", "history": [...]}
Server sends:
  {"type": "token",  "word": "hello",  "wordIndex": 0, "chunkId": 0}
  {"type": "audio",  "chunkId": 0, "data": "<base64wav>", "timings": [200,180,...], "chunkWordStartIndex": 0}
  {"type": "done"}
  {"type": "error",  "message": "..."}

Chunk builder: flush on sentence-end (.!? ≥3 words), clause (,;: ≥8 words), or >15 words.
TTS: Kokoro voice matched to NPC voice profile in world_state; falls back to default voice.
Timings: uniform total_duration_ms / word_count per word (V1).
"""

import asyncio
import base64
import io
import json
import logging
import re
import struct
import wave
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dialogue_stream"])

_SENTENCE_END = re.compile(r"[.!?]$")
_CLAUSE_END = re.compile(r"[,;:]$")
_MAX_CHUNK_WORDS = 15
_MIN_SENTENCE_WORDS = 3
_MIN_CLAUSE_WORDS = 8


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wav_duration_ms(wav_bytes: bytes) -> int:
    """Read duration from WAV header without decoding all samples."""
    try:
        with wave.open(io.BytesIO(wav_bytes)) as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            return int(frames / rate * 1000)
    except Exception:
        return 0


def _uniform_timings(n_words: int, total_ms: int) -> list[int]:
    if n_words <= 0:
        return []
    per = max(80, total_ms // n_words)
    return [per] * n_words


async def _get_npc_voice_profile(campaign_id: str, npc_id: str) -> dict:
    """Load voice profile from DB or return empty dict."""
    try:
        from server import db
        if db is None:
            return {}
        doc = await db["campaigns"].find_one({"_id": campaign_id})
        if not doc:
            return {}
        return (doc.get("world_state") or {}).get("npc_voice_profiles", {}).get(npc_id, {})
    except Exception as exc:
        logger.warning(f"[dialogue] Could not load voice profile: {exc}")
        return {}


async def _get_npc_context(campaign_id: str, npc_id: str) -> dict:
    """Load NPC data from world_blueprint for system prompt construction."""
    try:
        from server import db
        if db is None:
            return {}
        doc = await db["campaigns"].find_one({"_id": campaign_id})
        if not doc:
            return {}
        blueprint = doc.get("world_blueprint") or {}
        for npc in blueprint.get("key_npcs", []):
            nid = npc.get("id") or npc.get("name", "").lower().replace(" ", "_")
            if nid == npc_id:
                return npc
        return {}
    except Exception as exc:
        logger.warning(f"[dialogue] Could not load NPC context: {exc}")
        return {}


def _build_npc_system_prompt(npc: dict) -> str:
    name = npc.get("name") or npc_id_to_name(npc.get("id", "Unknown"))
    role = npc.get("role") or ""
    personality = npc.get("personality") or npc.get("secret_content", {}).get("personality", {})
    trait = personality.get("trait", "") if isinstance(personality, dict) else ""
    speech_style = (npc.get("secret_content") or {}).get("speech_style") or npc.get("speechStyle", "")
    background = (npc.get("secret_content") or {}).get("background") or npc.get("background", "")
    desc = npc.get("description") or ""

    lines = [
        f"You are {name}" + (f", {role}" if role else "") + ".",
        f"Speak in character. Keep replies to 1–4 sentences, no scene description.",
    ]
    if desc:
        lines.append(desc[:200])
    if trait:
        lines.append(f"Personality: {trait}")
    if speech_style:
        lines.append(f"Speech style: {speech_style}")
    if background:
        lines.append(f"Background: {background[:200]}")
    lines.append("Do not break character. Do not narrate actions (no asterisks).")
    return " ".join(lines)


def npc_id_to_name(npc_id: str) -> str:
    return npc_id.replace("_", " ").title()


def _tts_for_chunk(chunk_words: list[str], voice_profile: dict, npc_id: str, emotion: str) -> Optional[bytes]:
    """Generate TTS synchronously (runs in thread pool)."""
    from services.voice_casting_service import generate_npc_speech, assign_voice_to_npc
    text = " ".join(chunk_words)
    if not voice_profile.get("assignedVoice"):
        voice_profile = assign_voice_to_npc({"id": npc_id})
    return generate_npc_speech(
        npc_id=npc_id,
        text=text,
        voice_profile=voice_profile,
        emotion=emotion,
        use_cache=True,
        tier=1,
    )


# ── Chunk builder ─────────────────────────────────────────────────────────────

class ChunkBuilder:
    def __init__(self):
        self._words: list[str] = []

    def add(self, token: str) -> list[list[str]]:
        """Add a token (may contain multiple words/punctuation). Returns any complete chunks."""
        # Split on whitespace to get individual words
        parts = token.split()
        chunks = []
        for part in parts:
            if not part:
                continue
            self._words.append(part)
            if self._should_flush():
                chunks.append(self.flush())
        return chunks

    def flush(self) -> list[str]:
        words = self._words[:]
        self._words = []
        return words

    def _should_flush(self) -> bool:
        n = len(self._words)
        if n == 0:
            return False
        last = self._words[-1]
        stripped = last.rstrip("\"'")
        if _SENTENCE_END.search(stripped) and n >= _MIN_SENTENCE_WORDS:
            return True
        if _CLAUSE_END.search(stripped) and n >= _MIN_CLAUSE_WORDS:
            return True
        if n >= _MAX_CHUNK_WORDS:
            return True
        return False


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/dialogue/{campaign_id}/{npc_id}")
async def dialogue_stream(ws: WebSocket, campaign_id: str, npc_id: str):
    await ws.accept()
    loop = asyncio.get_event_loop()

    try:
        raw = await asyncio.wait_for(ws.receive_text(), timeout=15)
        payload = json.loads(raw)
    except asyncio.TimeoutError:
        await ws.send_text(json.dumps({"type": "error", "message": "No message received"}))
        await ws.close()
        return
    except Exception as exc:
        await ws.send_text(json.dumps({"type": "error", "message": str(exc)}))
        await ws.close()
        return

    player_text = (payload.get("text") or "").strip()
    emotion = (payload.get("emotion") or "neutral").strip()
    history = payload.get("history") or []

    if not player_text:
        await ws.send_text(json.dumps({"type": "error", "message": "Empty message"}))
        await ws.close()
        return

    # Load NPC context + voice in parallel
    npc_ctx, voice_profile = await asyncio.gather(
        _get_npc_context(campaign_id, npc_id),
        _get_npc_voice_profile(campaign_id, npc_id),
    )

    system_prompt = _build_npc_system_prompt(npc_ctx)

    # Build messages list
    messages = [{"role": "system", "content": system_prompt}]
    for h in history[-10:]:  # last 10 turns
        role = h.get("role", "user")
        content = h.get("content", "")
        if content and role in ("user", "assistant"):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": player_text})

    chunk_builder = ChunkBuilder()
    word_index = 0
    chunk_id = 0
    chunk_word_start = 0
    pending_tts: list[asyncio.Task] = []

    async def send_chunk_audio(chunk_words: list[str], cid: int, word_start: int):
        nonlocal pending_tts
        audio_bytes = await loop.run_in_executor(
            None, _tts_for_chunk, chunk_words, voice_profile.copy(), npc_id, emotion
        )
        if audio_bytes:
            dur_ms = _wav_duration_ms(audio_bytes)
            timings = _uniform_timings(len(chunk_words), dur_ms)
            b64 = base64.b64encode(audio_bytes).decode()
            try:
                await ws.send_text(json.dumps({
                    "type": "audio",
                    "chunkId": cid,
                    "data": b64,
                    "timings": timings,
                    "chunkWordStartIndex": word_start,
                }))
            except Exception:
                pass  # client disconnected

    try:
        anthropic_key = __import__("os").getenv("ANTHROPIC_API_KEY")

        if anthropic_key:
            from litellm import acompletion
            stream = await acompletion(
                model="claude-haiku-4-5-20251001",
                messages=messages,
                max_tokens=300,
                temperature=0.85,
                api_key=anthropic_key,
                stream=True,
            )
            async for part in stream:
                delta = part.choices[0].delta
                token = getattr(delta, "content", None) or ""
                if not token:
                    continue

                # Send word tokens to client
                words_in_token = token.split()
                for w in words_in_token:
                    try:
                        await ws.send_text(json.dumps({
                            "type": "token",
                            "word": w,
                            "wordIndex": word_index,
                            "chunkId": chunk_id,
                        }))
                    except Exception:
                        return
                    word_index += 1

                # Feed chunk builder
                for completed_chunk in chunk_builder.add(token):
                    n_words = len(completed_chunk)
                    cid = chunk_id
                    ws_idx = chunk_word_start
                    chunk_id += 1
                    chunk_word_start += n_words
                    asyncio.ensure_future(send_chunk_audio(completed_chunk, cid, ws_idx))

        else:
            # OpenAI / Emergent fallback (non-streaming)
            from services.claude_client import call_haiku_async
            system_text = system_prompt
            user_text = player_text
            full_text = await call_haiku_async(
                system_prompt=system_text,
                user_content=user_text,
                max_tokens=300,
                temperature=0.85,
            )
            for w in full_text.split():
                try:
                    await ws.send_text(json.dumps({
                        "type": "token",
                        "word": w,
                        "wordIndex": word_index,
                        "chunkId": chunk_id,
                    }))
                except Exception:
                    return
                word_index += 1
                for completed_chunk in chunk_builder.add(w + " "):
                    n_words = len(completed_chunk)
                    cid = chunk_id
                    ws_idx = chunk_word_start
                    chunk_id += 1
                    chunk_word_start += n_words
                    asyncio.ensure_future(send_chunk_audio(completed_chunk, cid, ws_idx))

        # Flush any remaining words
        tail = chunk_builder.flush()
        if tail:
            asyncio.ensure_future(send_chunk_audio(tail, chunk_id, chunk_word_start))

        # Wait briefly for TTS tasks before sending done
        await asyncio.sleep(0.1)
        try:
            await ws.send_text(json.dumps({"type": "done"}))
        except Exception:
            pass

    except WebSocketDisconnect:
        logger.debug(f"[dialogue] Client disconnected: campaign={campaign_id} npc={npc_id}")
    except Exception as exc:
        logger.error(f"[dialogue] Stream error: {exc}", exc_info=True)
        try:
            await ws.send_text(json.dumps({"type": "error", "message": str(exc)}))
        except Exception:
            pass
