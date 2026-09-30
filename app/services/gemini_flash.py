"""Gemini Flash: fast, structured 5-panel comic outline."""
import json
import re

from app import config
from app.services.errors import GenerationError
from app.services.gemini_client import call_gemini

OUTLINE_PROMPT = """You are a comic book story planner.
Create a {n}-panel comic outline.

Story idea: {story_prompt}
Main character: {character_name}
Setting: {setting}
Tone: {tone}
Art style: {art_style}

Return ONLY a JSON array with exactly {n} objects. Each object must have these keys:
  "panel_number" (integer 1..{n}),
  "title" (short panel title),
  "scene_description" (1-2 sentences describing what happens),
  "image_prompt" (a vivid visual prompt for an image generator, mention the character, setting and the {art_style} style).
The {n} panels must form a beginning, middle and end."""

REQUIRED_KEYS = ("title", "scene_description", "image_prompt")


def _extract_json(text: str) -> list:
    """Parse the model output, tolerating ```json fences or leading chatter."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", cleaned, flags=re.DOTALL)
        if not match:
            raise GenerationError("Outline was not valid JSON.")
        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise GenerationError(f"Outline was not valid JSON: {exc}") from exc
    if isinstance(data, dict):  # some models wrap the list: {"panels": [...]}
        data = next((v for v in data.values() if isinstance(v, list)), None)
    if not isinstance(data, list):
        raise GenerationError("Outline JSON did not contain a list of panels.")
    return data


def normalize_outline(raw: list, n: int = config.NUM_PANELS) -> list[dict]:
    """Validate and clean panels; guarantees n dicts with numbered panels and all keys."""
    panels: list[dict] = []
    for i, item in enumerate(raw[:n], start=1):
        if not isinstance(item, dict) or any(not str(item.get(k, "")).strip() for k in REQUIRED_KEYS):
            raise GenerationError(f"Panel {i} is missing required fields.")
        panels.append(
            {
                "panel_number": i,
                "title": str(item["title"]).strip(),
                "scene_description": str(item["scene_description"]).strip(),
                "image_prompt": str(item["image_prompt"]).strip(),
            }
        )
    if len(panels) != n:
        raise GenerationError(f"Expected {n} panels but received {len(panels)}.")
    return panels


def generate_outline(story_prompt: str, character_name: str, setting: str, tone: str, art_style: str) -> list[dict]:
    """Return a list of 5 dicts: panel_number, title, scene_description, image_prompt."""
    if config.is_mock_mode():
        from app.services import mock_ai

        return mock_ai.mock_outline(story_prompt, character_name, setting, tone, art_style)
    prompt = OUTLINE_PROMPT.format(
        n=config.NUM_PANELS, story_prompt=story_prompt, character_name=character_name,
        setting=setting, tone=tone, art_style=art_style,
    )
    text = call_gemini(config.GEMINI_FLASH_MODEL, prompt, json_mode=True)
    return normalize_outline(_extract_json(text))
