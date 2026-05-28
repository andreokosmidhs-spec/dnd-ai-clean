"""Local TTS using Kokoro-ONNX — no API key required.

Model files (~120 MB total) are downloaded once on first use to KOKORO_MODEL_DIR
(default: /tmp/kokoro_models) and reused on subsequent requests.

Voice mapping (OpenAI names → Kokoro voices):
  onyx    → bm_george  (deep British male — default DM voice)
  alloy   → af_sky
  echo    → am_adam
  fable   → bf_emma
  nova    → af_heart
  shimmer → af_sky
"""

import io
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MODEL_DIR = Path(os.getenv("KOKORO_MODEL_DIR", "/tmp/kokoro_models"))
_ONNX_FILENAME = "kokoro-v0_19.onnx"
_VOICES_FILENAME = "voices-v1.0.bin"

_VOICE_MAP: dict[str, str] = {
    "onyx":    "bm_george",
    "alloy":   "af_sky",
    "echo":    "am_adam",
    "fable":   "bf_emma",
    "nova":    "af_heart",
    "shimmer": "af_sky",
}

_kokoro_instance = None
_init_attempted = False


def _download_file(url: str, dest: Path) -> bool:
    import requests
    try:
        logger.info(f"[TTS] Downloading {dest.name} …")
        resp = requests.get(url, stream=True, timeout=300)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
        logger.info(f"[TTS] {dest.name} saved ({dest.stat().st_size // 1024} KB)")
        return True
    except Exception as exc:
        logger.error(f"[TTS] Download failed for {dest.name}: {exc}")
        if dest.exists():
            dest.unlink(missing_ok=True)
        return False


def _ensure_models() -> Optional[tuple[str, str]]:
    _MODEL_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = _MODEL_DIR / _ONNX_FILENAME
    voices_path = _MODEL_DIR / _VOICES_FILENAME

    if onnx_path.exists() and voices_path.exists():
        return str(onnx_path), str(voices_path)

    logger.info("[TTS] First-run: downloading Kokoro models (~120 MB, one-time) …")

    # Try HuggingFace Hub first (respects HF_HOME cache)
    try:
        from huggingface_hub import hf_hub_download
        for fname, dest in [(_ONNX_FILENAME, onnx_path), (_VOICES_FILENAME, voices_path)]:
            if not dest.exists():
                hf_hub_download(
                    repo_id="thewh1teagle/kokoro-onnx",
                    filename=fname,
                    local_dir=str(_MODEL_DIR),
                )
        if onnx_path.exists() and voices_path.exists():
            return str(onnx_path), str(voices_path)
    except Exception as exc:
        logger.warning(f"[TTS] HuggingFace download failed ({exc}), trying GitHub releases …")

    # Fallback: direct GitHub release download
    base_url = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files"
    for fname, dest in [(_ONNX_FILENAME, onnx_path), (_VOICES_FILENAME, voices_path)]:
        if not dest.exists():
            if not _download_file(f"{base_url}/{fname}", dest):
                return None

    if onnx_path.exists() and voices_path.exists():
        return str(onnx_path), str(voices_path)
    return None


def _get_kokoro():
    global _kokoro_instance, _init_attempted
    if _init_attempted:
        return _kokoro_instance
    _init_attempted = True

    paths = _ensure_models()
    if not paths:
        logger.error("[TTS] Kokoro models unavailable — TTS will fall back to OpenAI or browser.")
        return None

    try:
        from kokoro_onnx import Kokoro
        onnx_path, voices_path = paths
        _kokoro_instance = Kokoro(onnx_path, voices_path)
        logger.info("[TTS] Kokoro TTS initialized ✅")
    except Exception as exc:
        logger.error(f"[TTS] Kokoro init error: {exc}")

    return _kokoro_instance


def generate_speech_bytes(text: str, voice: str = "onyx", speed: float = 1.0) -> Optional[bytes]:
    """Return WAV audio bytes for *text*, or None if Kokoro is unavailable."""
    kokoro = _get_kokoro()
    if kokoro is None:
        return None

    kokoro_voice = _VOICE_MAP.get(voice, "bm_george")
    try:
        import soundfile as sf
        samples, sample_rate = kokoro.create(
            text, voice=kokoro_voice, speed=speed, lang="en-us"
        )
        buf = io.BytesIO()
        sf.write(buf, samples, sample_rate, format="WAV", subtype="PCM_16")
        buf.seek(0)
        return buf.read()
    except Exception as exc:
        logger.error(f"[TTS] Speech generation error: {exc}")
        return None
