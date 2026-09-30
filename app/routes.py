"""All FastAPI routes for ComicCraft."""
import logging
import re

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app import config
from app.schemas import PromptRequest
from app.services.errors import GenerationError
from app.services.image_generator import generate_image
from app.services.pipeline import create_comic

log = logging.getLogger("comiccraft.routes")
router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))

_SAFE_PDF = re.compile(r"^comic_[0-9_]+\.pdf$")  # blocks path traversal on /download


def _render_index(request: Request, error: str | None = None, status: int = 200, form: dict | None = None):
    return templates.TemplateResponse(request, "index.html", {"error": error, "form": form or {}}, status_code=status)


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Homepage with the story form."""
    return _render_index(request)


@router.get("/health")
def health():
    """Liveness probe (also used by the performance tests)."""
    return {"status": "ok", "mock_mode": config.is_mock_mode()}


@router.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    story_prompt: str = Form(...),
    character_name: str = Form("Hero"),
    setting: str = Form("forest"),
    tone: str = Form("light-hearted"),
    art_style: str = Form("comic book"),
):
    """Form submission -> full AI pipeline -> comic preview page."""
    form = dict(story_prompt=story_prompt, character_name=character_name, setting=setting, tone=tone, art_style=art_style)
    try:
        req = PromptRequest(**form)
    except ValidationError as exc:
        first = exc.errors()[0]
        return _render_index(request, f"Invalid input for '{first['loc'][0]}': {first['msg']}", 422, form)
    try:
        layout, pdf_path = create_comic(req)
    except GenerationError as exc:
        log.error("Generation failed: %s", exc)
        return _render_index(request, f"Comic generation failed: {exc}", 502, form)
    except Exception:  # unexpected -> never leak a stack trace to the user
        log.exception("Unexpected error while generating a comic")
        return _render_index(request, "Something went wrong while creating your comic. Please try again.", 500, form)
    return templates.TemplateResponse(
        request,
        "comic_preview.html",
        {"layout": layout, "pdf_file": pdf_path.split("/")[-1], "req": req},
    )


@router.post("/generate-comic/json")
def generate_comic_json(payload: PromptRequest):
    """JSON API: same pipeline, returns layout data + PDF path."""
    try:
        layout, pdf_path = create_comic(payload)
    except GenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        log.exception("Unexpected error in JSON API")
        raise HTTPException(status_code=500, detail="Internal error while generating the comic.") from exc
    return {"layout": layout, "pdf_path": pdf_path}


@router.get("/download/{filename}")
def download(filename: str):
    """Serve an exported PDF as a file download."""
    if not _SAFE_PDF.match(filename):
        raise HTTPException(status_code=400, detail="Invalid file name.")
    path = config.EXPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path, media_type="application/pdf", filename=filename)


@router.get("/export-success", response_class=HTMLResponse)
def export_success(request: Request, file: str = ""):
    """Confirmation page shown after the PDF download starts."""
    file = file if _SAFE_PDF.match(file) else ""
    return templates.TemplateResponse(request, "export_success.html", {"pdf_file": file})


@router.get("/test-image")
def test_image(prompt: str = "a brave fox in an enchanted forest, comic book style", art_style: str = "comic book"):
    """Developer utility: test image generation on its own."""
    try:
        path = generate_image(prompt, art_style)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Image generation failed: {exc}") from exc
    return {"prompt": prompt, "image_path": path}
