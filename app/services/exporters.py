"""Export the finished comic layout to a multi-page PDF with FPDF."""
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from app import config

_REPLACEMENTS = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"', "\u2014": "-", "\u2013": "-", "\u2026": "..."}


def _latin1(text: str) -> str:
    """Core PDF fonts are latin-1 only: swap common typographic characters, drop the rest."""
    for src, dst in _REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "replace").decode("latin-1")


def save_pdf(layout: list[dict], title: str = "My ComicCraft Story") -> str:
    """Write the PDF to static/exports/comic_<timestamp>.pdf and return that path (relative to project root)."""
    config.ensure_dirs()
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.add_page()  # cover page
    pdf.set_font("Helvetica", "B", 26)
    pdf.ln(70)
    pdf.multi_cell(0, 14, _latin1(title), align="C")
    pdf.set_font("Helvetica", "I", 12)
    pdf.ln(6)
    pdf.cell(0, 8, "Created with ComicCraft - AI Comic Story Creator", align="C", new_x="LMARGIN", new_y="NEXT")

    for panel in layout:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.multi_cell(0, 10, _latin1(f"Panel {panel['panel_number']}: {panel['title']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        img = config.BASE_DIR / panel["image_path"] if panel.get("image_path") else None
        if img and Path(img).exists():
            pdf.image(str(img), x=30, w=150)
            pdf.ln(4)
        pdf.set_font("Helvetica", "I", 11)
        pdf.multi_cell(0, 6, _latin1(panel["scene_description"]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        if panel.get("caption"):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, _latin1("Caption: " + panel["caption"]), new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 7, _latin1(panel["narration"]), new_x="LMARGIN", new_y="NEXT")

    filename = f"comic_{datetime.now():%Y%m%d_%H%M%S_%f}.pdf"
    out = config.EXPORTS_DIR / filename
    pdf.output(str(out))
    return f"static/exports/{filename}"
