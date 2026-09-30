"""Stable Diffusion image generation (Hugging Face Diffusers) with a Pillow placeholder fallback."""
import hashlib
import logging
import re
import threading
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app import config

log = logging.getLogger("comiccraft.image")

_pipe = None
_pipe_failed = False
_pipe_lock = threading.Lock()   # guards one-time model loading
_infer_lock = threading.Lock()  # diffusers pipelines are not thread-safe: run one generation at a time

STYLE_SUFFIX = {
    "anime": "anime style, vibrant colors, clean line art",
    "pixel art": "pixel art, 16-bit retro game style",
    "comic book": "classic comic book style, bold ink outlines, halftone shading",
    "realistic": "realistic digital illustration, detailed, cinematic lighting",
}
NEGATIVE_PROMPT = "text, watermark, blurry, low quality, deformed, extra limbs"


def sanitize_filename(text: str, max_len: int = 40) -> str:
    """Turn any prompt into a safe file-name fragment (a-z, 0-9, dash)."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (slug[:max_len].strip("-")) or "panel"


def _load_pipeline():
    """Load Stable Diffusion once. Returns None (-> placeholder) if it cannot be loaded."""
    global _pipe, _pipe_failed
    if _pipe is not None or _pipe_failed:
        return _pipe
    with _pipe_lock:
        if _pipe is not None or _pipe_failed:
            return _pipe
        try:
            import torch
            from diffusers import StableDiffusionPipeline

            device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
            dtype = torch.float16 if device == "cuda" else torch.float32
            kwargs = {"torch_dtype": dtype}
            if config.HF_API_KEY:
                kwargs["token"] = config.HF_API_KEY
            pipe = StableDiffusionPipeline.from_pretrained(config.SD_MODEL_ID, **kwargs)
            pipe.safety_checker = None  # avoids false-positive black images on comic art
            pipe.set_progress_bar_config(disable=True)
            _pipe = pipe.to(device)
            log.info("Stable Diffusion loaded on %s", device)
        except Exception as exc:  # missing torch, no internet, gated repo ...
            _pipe_failed = True
            log.warning("Stable Diffusion unavailable (%s). Using placeholder panels.", exc)
    return _pipe


def _placeholder_image(prompt: str, panel_label: str = "") -> Image.Image:
    """Colourful labelled panel so the app still works end-to-end without a GPU / model."""
    size = config.IMAGE_SIZE
    h = hashlib.md5(prompt.encode()).digest()
    top, bottom = (h[0], h[1], 160 + h[2] % 90), (200 + h[3] % 55, 150 + h[4] % 100, h[5])
    img = Image.new("RGB", (size, size))
    draw = ImageDraw.Draw(img)
    for y in range(size):  # vertical gradient
        t = y / size
        draw.line([(0, y), (size, y)], fill=tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3)))
    draw.rectangle([8, 8, size - 9, size - 9], outline=(20, 20, 20), width=6)
    words, lines, line = prompt.split(), [], ""
    for w in words:
        if len(line) + len(w) > 30:
            lines.append(line)
            line = ""
        line += w + " "
    lines.append(line)
    try:
        font, big = ImageFont.load_default(size=20), ImageFont.load_default(size=30)
    except TypeError:  # very old Pillow: fixed-size bitmap font
        font = big = ImageFont.load_default()
    draw.text((28, 24), panel_label or "Comic Panel", fill=(255, 255, 255), font=big)
    for i, ln in enumerate(lines[:10]):
        draw.text((28, 80 + i * 28), ln.strip(), fill=(255, 255, 255), font=font)
    return img


def generate_image(prompt: str, art_style: str | None = None, panel_number: int | None = None) -> str:
    """Generate one panel image, save it to static/panels and return its path (relative to project root)."""
    config.ensure_dirs()
    style = STYLE_SUFFIX.get((art_style or "").lower(), art_style or "")
    full_prompt = f"{prompt}, {style}".strip(", ")
    stem = sanitize_filename(prompt)
    filename = f"{'p' + str(panel_number) + '_' if panel_number else ''}{stem}_{uuid.uuid4().hex[:8]}.png"
    out_path: Path = config.PANELS_DIR / filename

    pipe = None if config.is_mock_mode() else _load_pipeline()
    if pipe is None:
        image = _placeholder_image(full_prompt, f"Panel {panel_number}" if panel_number else "")
    else:
        with _infer_lock:
            image = pipe(
                full_prompt,
                negative_prompt=NEGATIVE_PROMPT,
                num_inference_steps=config.IMAGE_STEPS,
                height=config.IMAGE_SIZE,
                width=config.IMAGE_SIZE,
            ).images[0]
    image.save(out_path)
    return f"static/panels/{filename}"
