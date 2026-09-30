import json
import re

import pytest

from app import config
from app.services.errors import GenerationError
from app.services.exporters import save_pdf
from app.services.gemini_flash import _extract_json, generate_outline, normalize_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image, sanitize_filename
from app.services.layout_builder import build_comic_layout, parse_story


def _panels(n=5):
    return [{"panel_number": i, "title": f"T{i}", "scene_description": f"S{i}", "image_prompt": f"P{i}"} for i in range(1, n + 1)]


def test_outline_has_five_complete_panels():
    outline = generate_outline("A brave fox", "Rusty", "forest", "dramatic", "anime")
    assert len(outline) == config.NUM_PANELS
    assert [p["panel_number"] for p in outline] == [1, 2, 3, 4, 5]
    assert all(p["title"] and p["scene_description"] and p["image_prompt"] for p in outline)
    assert "Rusty" in outline[0]["scene_description"]


def test_extract_json_handles_fences_and_wrapper_objects():
    raw = json.dumps(_panels())
    assert len(_extract_json(f"```json\n{raw}\n```")) == 5
    assert len(_extract_json(json.dumps({"panels": _panels()}))) == 5
    assert len(_extract_json(f"Sure! Here you go: {raw}")) == 5


def test_extract_json_rejects_garbage():
    with pytest.raises(GenerationError):
        _extract_json("not json at all")


def test_normalize_outline_validates():
    assert len(normalize_outline(_panels())) == 5
    with pytest.raises(GenerationError):
        normalize_outline(_panels(3))
    bad = _panels()
    bad[2]["title"] = ""
    with pytest.raises(GenerationError):
        normalize_outline(bad)


def test_story_contains_every_panel():
    outline = generate_outline("x story", "Rusty", "forest", "funny", "comic book")
    story = generate_story(outline, "Rusty", "funny")
    parsed = parse_story(story)
    assert sorted(parsed) == [1, 2, 3, 4, 5]
    assert parsed[1]["caption"] and parsed[1]["narration"]


def test_sanitize_filename():
    assert sanitize_filename("A fox! In/../the *forest?") == "a-fox-in-the-forest"
    assert sanitize_filename("???") == "panel"
    assert len(sanitize_filename("word " * 50)) <= 40


def test_generate_image_saves_png():
    path = generate_image("a fox in a forest", "anime", 1)
    assert path.startswith("static/panels/") and path.endswith(".png")
    assert (config.BASE_DIR / path).exists()


def test_layout_matches_images_and_text():
    outline = generate_outline("story", "Rusty", "city", "poetic", "realistic")
    story = generate_story(outline, "Rusty", "poetic")
    layout = build_comic_layout(outline, story, [f"img{i}.png" for i in range(5)])
    assert len(layout) == 5
    assert layout[2]["image_path"] == "img2.png" and layout[2]["panel_number"] == 3
    assert layout[0]["narration"]


def test_layout_falls_back_when_story_missing_panel():
    layout = build_comic_layout(_panels(2), "Panel 1: A\nCaption: c\nNarration: only one", ["a.png", "b.png"])
    assert layout[0]["narration"] == "only one"
    assert layout[1]["narration"] == "S2"  # fallback to scene description


def test_pdf_export_is_valid_and_timestamped():
    outline = generate_outline("story", "Rusty", "forest", "funny", "comic book")
    story = generate_story(outline, "Rusty", "funny")
    imgs = [generate_image(p["image_prompt"], "comic book", p["panel_number"]) for p in outline]
    layout = build_comic_layout(outline, story, imgs)
    path = save_pdf(layout, "Rusty’s “Test” — Comic…")  # unicode punctuation must not crash
    full = config.BASE_DIR / path
    data = full.read_bytes()
    assert data.startswith(b"%PDF") and full.name.startswith("comic_") and full.suffix == ".pdf"
    assert len(re.findall(rb"/Type\s*/Page(?![s\w])", data)) == 6  # cover + 5 panels
