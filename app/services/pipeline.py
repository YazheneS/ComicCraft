"""One reusable function that runs the full comic workflow (used by /generate and /generate-comic/json)."""
from app.schemas import PromptRequest
from app.services.exporters import save_pdf
from app.services.gemini_flash import generate_outline
from app.services.gemini_pro import generate_story
from app.services.image_generator import generate_image
from app.services.layout_builder import build_comic_layout


def create_comic(req: PromptRequest) -> tuple[list[dict], str]:
    """outline -> story -> images -> layout -> PDF. Returns (layout, pdf_path)."""
    outline = generate_outline(req.story_prompt, req.character_name, req.setting, req.tone, req.art_style)
    story = generate_story(outline, req.character_name, req.tone)
    images = [generate_image(p["image_prompt"], req.art_style, p["panel_number"]) for p in outline]
    layout = build_comic_layout(outline, story, images)
    title = f"{req.character_name}: {req.story_prompt[:60]}"
    pdf_path = save_pdf(layout, title)
    return layout, pdf_path
