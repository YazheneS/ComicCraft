import re

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
GOOD = {"story_prompt": "A brave fox exploring an enchanted forest", "character_name": "Rusty",
        "setting": "forest", "tone": "dramatic", "art_style": "anime"}


def test_home_page_has_all_form_fields():
    r = client.get("/")
    assert r.status_code == 200
    for name in ("story_prompt", "character_name", "setting", "tone", "art_style"):
        assert f'name="{name}"' in r.text


def test_health():
    assert client.get("/health").json()["status"] == "ok"


def test_generate_form_renders_preview_with_five_panels():
    r = client.post("/generate", data=GOOD)
    assert r.status_code == 200
    assert r.text.count('class="panel"') == 5
    assert "Download Your Comic as PDF" in r.text
    assert "Rusty" in r.text


def test_generate_form_validation_error():
    r = client.post("/generate", data={**GOOD, "story_prompt": "hi"})
    assert r.status_code == 422 and "Invalid input" in r.text


def test_json_api_returns_layout_and_pdf():
    r = client.post("/generate-comic/json", json=GOOD)
    assert r.status_code == 200
    body = r.json()
    assert len(body["layout"]) == 5 and body["pdf_path"].endswith(".pdf")
    assert {"panel_number", "title", "image_path", "text"} <= set(body["layout"][0])


def test_json_api_validation_error():
    assert client.post("/generate-comic/json", json={"story_prompt": ""}).status_code == 422


def test_download_and_export_success_flow():
    pdf = client.post("/generate-comic/json", json=GOOD).json()["pdf_path"].split("/")[-1]
    d = client.get(f"/download/{pdf}")
    assert d.status_code == 200 and d.content.startswith(b"%PDF")
    s = client.get(f"/export-success?file={pdf}")
    assert s.status_code == 200 and "Go Create Another Comic" in s.text


def test_download_blocks_path_traversal_and_missing():
    assert client.get("/download/..%2F..%2Fetc%2Fpasswd").status_code in (400, 404)
    assert client.get("/download/evil.pdf").status_code == 400
    assert client.get("/download/comic_00000000_000000_000000.pdf").status_code == 404


def test_export_success_ignores_unsafe_file_param():
    r = client.get("/export-success?file=../../etc/passwd")
    assert r.status_code == 200 and "passwd" not in r.text


def test_test_image_route():
    r = client.get("/test-image", params={"prompt": "a robot in space"})
    assert r.status_code == 200 and r.json()["image_path"].endswith(".png")
    assert client.get("/" + r.json()["image_path"]).status_code == 200  # served statically


def test_generation_failure_returns_502(monkeypatch):
    from app import routes
    from app.services.errors import GenerationError

    def boom(_):
        raise GenerationError("quota exceeded")

    monkeypatch.setattr(routes, "create_comic", boom)
    r = client.post("/generate", data=GOOD)
    assert r.status_code == 502 and "quota exceeded" in r.text
    assert client.post("/generate-comic/json", json=GOOD).status_code == 502
