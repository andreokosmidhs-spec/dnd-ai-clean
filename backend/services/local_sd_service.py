"""Local Stable Diffusion image generation — free, no API cost.

Two backends (tried in order):

  A) Automatic1111 WebUI API
     Set A1111_URL=http://localhost:7860
     Requires Automatic1111 running separately. Any SD model works.

  B) HuggingFace Diffusers (pure Python, models auto-download)
     Set SD_LOCAL=true
     Set SD_MODEL_ID=Lykon/dreamshaper-8  (default — good fantasy art, ~4 GB)
     Set SD_DEVICE=cuda|cpu              (default: auto-detect)
     First run downloads the model to ~/.cache/huggingface/hub.
     Install deps:  pip install diffusers transformers accelerate torch

Both return data URLs (data:image/png;base64,...) or None on failure.
"""

import asyncio
import base64
import io
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "Lykon/dreamshaper-8"
_NEG = (
    "deformed, blurry, bad anatomy, disfigured, poorly drawn face, mutation, "
    "extra limb, ugly, disgusting, poorly drawn hands, missing limb, "
    "floating limbs, disconnected limbs, malformed hands, watermark, text, logo"
)

# ── Lazy pipeline singleton (diffusers) ───────────────────────────────────────
_pipeline = None
_pipeline_loaded = False


def _load_pipeline():
    global _pipeline, _pipeline_loaded
    if _pipeline_loaded:
        return _pipeline

    _pipeline_loaded = True
    model_id = os.getenv("SD_MODEL_ID", _DEFAULT_MODEL)

    try:
        import torch
        from diffusers import AutoPipelineForText2Image

        sd_device = os.getenv("SD_DEVICE", "")
        if sd_device:
            device = sd_device
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        dtype = torch.float16 if device == "cuda" else torch.float32

        logger.info(f"[local_sd] Loading model '{model_id}' on {device} ({dtype})…")
        pipe = AutoPipelineForText2Image.from_pretrained(
            model_id,
            torch_dtype=dtype,
            use_safetensors=True,
            safety_checker=None,
            requires_safety_checker=False,
        ).to(device)

        if device == "cuda":
            try:
                pipe.enable_model_cpu_offload()
            except Exception:
                pass

        _pipeline = pipe
        logger.info(f"[local_sd] Model loaded: {model_id}")
    except ImportError:
        logger.warning(
            "[local_sd] diffusers/torch not installed. "
            "Run: pip install diffusers transformers accelerate torch"
        )
    except Exception as exc:
        logger.error(f"[local_sd] Pipeline load failed: {exc}")

    return _pipeline


def _generate_diffusers_sync(
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
) -> Optional[str]:
    pipe = _load_pipeline()
    if pipe is None:
        return None
    try:
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
        )
        img = result.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode()
        return f"data:image/png;base64,{b64}"
    except Exception as exc:
        logger.error(f"[local_sd] Generation failed: {exc}")
        return None


# ── A1111 backend ─────────────────────────────────────────────────────────────

async def _generate_a1111(
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
) -> Optional[str]:
    base_url = os.getenv("A1111_URL", "").rstrip("/")
    if not base_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{base_url}/sdapi/v1/txt2img",
                json={
                    "prompt": prompt,
                    "negative_prompt": negative_prompt,
                    "steps": steps,
                    "width": width,
                    "height": height,
                    "cfg_scale": guidance,
                    "sampler_name": "DPM++ 2M Karras",
                    "send_images": True,
                    "save_images": False,
                },
            )
            resp.raise_for_status()
            images = resp.json().get("images", [])
            if not images:
                return None
            return f"data:image/png;base64,{images[0]}"
    except Exception as exc:
        logger.warning(f"[local_sd] A1111 error: {exc}")
        return None


# ── Diffusers async wrapper ───────────────────────────────────────────────────

async def _generate_diffusers(
    prompt: str,
    negative_prompt: str,
    width: int,
    height: int,
    steps: int,
    guidance: float,
) -> Optional[str]:
    if not os.getenv("SD_LOCAL"):
        return None
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        _generate_diffusers_sync,
        prompt, negative_prompt, width, height, steps, guidance,
    )


# ── Public API ────────────────────────────────────────────────────────────────

async def is_available() -> bool:
    """Return True if at least one local backend is configured."""
    return bool(os.getenv("A1111_URL") or os.getenv("SD_LOCAL"))


async def generate_portrait(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 768,
    steps: int = 25,
    guidance: float = 7.0,
) -> Optional[str]:
    """Portrait-aspect image (512×768 by default)."""
    neg = negative_prompt or _NEG
    result = await _generate_a1111(prompt, neg, width, height, steps, guidance)
    if result:
        return result
    return await _generate_diffusers(prompt, neg, width, height, steps, guidance)


async def generate_scene(
    prompt: str,
    negative_prompt: str = "",
    width: int = 768,
    height: int = 432,
    steps: int = 25,
    guidance: float = 7.0,
) -> Optional[str]:
    """Landscape-aspect image (768×432 ≈ 16:9 by default)."""
    neg = negative_prompt or _NEG
    result = await _generate_a1111(prompt, neg, width, height, steps, guidance)
    if result:
        return result
    return await _generate_diffusers(prompt, neg, width, height, steps, guidance)


async def generate_square(
    prompt: str,
    negative_prompt: str = "",
    size: int = 512,
    steps: int = 25,
    guidance: float = 7.0,
) -> Optional[str]:
    """Square image (512×512 by default)."""
    neg = negative_prompt or _NEG
    result = await _generate_a1111(prompt, neg, size, size, steps, guidance)
    if result:
        return result
    return await _generate_diffusers(prompt, neg, size, size, steps, guidance)
