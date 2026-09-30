"""Gemini Pro: rich narration + character dialogue for every outlined panel."""
from app import config
from app.services.gemini_client import call_gemini

STORY_PROMPT = """You are a comic book writer. Expand this panel outline into a finished comic story.

Main character: {character_name}
Tone: {tone}

Panel outline:
{outline_text}

For EACH panel write exactly this format (no extra commentary, no markdown symbols):

Panel <number>: <title>
Caption: <one short line about the environment, mood or sound>
Narration: <2-4 sentences of narration and character dialogue in quotation marks>

Write all {n} panels in order."""


def generate_story(outline: list[dict], character_name: str = "Hero", tone: str = "light-hearted") -> str:
    """Return one formatted text block that contains the story for every panel."""
    if config.is_mock_mode():
        from app.services import mock_ai

        return mock_ai.mock_story(outline, character_name, tone)
    outline_text = "\n".join(
        f"Panel {p['panel_number']} - {p['title']}: {p['scene_description']}" for p in outline
    )
    prompt = STORY_PROMPT.format(
        character_name=character_name, tone=tone, outline_text=outline_text, n=len(outline)
    )
    return call_gemini(config.GEMINI_PRO_MODEL, prompt, json_mode=False)
