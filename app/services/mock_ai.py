"""Deterministic offline stand-ins for Gemini (used when COMICCRAFT_MOCK=1: demos, CI, load tests)."""

_BEATS = [
    ("The Adventure Begins", "{c} sets out from home in the {s}, full of curiosity."),
    ("Into the Unknown", "{c} ventures deeper into the {s} and finds a strange glowing trail."),
    ("A Sudden Twist", "Something unexpected blocks {c}'s path in the {s}."),
    ("Courage Under Pressure", "{c} uses cleverness and courage to face the challenge."),
    ("A New Beginning", "{c} returns from the {s} wiser, and the adventure is remembered forever."),
]


def mock_outline(story_prompt, character_name, setting, tone, art_style) -> list[dict]:
    """Five fixed story beats personalised with the user's inputs."""
    panels = []
    for i, (title, scene) in enumerate(_BEATS, start=1):
        scene_text = scene.format(c=character_name, s=setting)
        panels.append(
            {
                "panel_number": i,
                "title": title,
                "scene_description": scene_text,
                "image_prompt": f"{character_name}, {scene_text} {story_prompt}. {tone} mood, {art_style} style",
            }
        )
    return panels


def mock_story(outline, character_name="Hero", tone="light-hearted") -> str:
    """Panel-by-panel story text in the same format Gemini Pro is asked to produce."""
    blocks = []
    for p in outline:
        blocks.append(
            f"Panel {p['panel_number']}: {p['title']}\n"
            f"Caption: A {tone} moment unfolds.\n"
            f"Narration: {p['scene_description']} \"This is only the start,\" says {character_name}."
        )
    return "\n\n".join(blocks)
