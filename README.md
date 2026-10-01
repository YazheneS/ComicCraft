# ComicCraft - AI Comic Story Creator using Gemini Models

ComicCraft is a FastAPI web app that turns a short prompt (story idea, character name, setting, tone, art style) into a
**5-panel comic**: a panel outline (Gemini Flash), narration + dialogue (Gemini Pro), one illustration per panel
(Stable Diffusion via Hugging Face Diffusers) and a downloadable **PDF** (FPDF).

Part of the *Google Cloud Generative AI - AI/ML & GenAI Track* project. All phase deliverables are in folders `1` to `8`
(same structure as the common project template).

## Project structure
```
.
├── app/
│   ├── main.py                  # FastAPI app, static files, router
│   ├── routes.py                # /, /generate, /generate-comic/json, /download, /export-success, /test-image, /health
│   ├── config.py  schemas.py    # env/config + PromptRequest (Pydantic)
│   └── services/
│       ├── gemini_flash.py      # generate_outline()      -> 5-panel JSON outline
│       ├── gemini_pro.py        # generate_story()        -> narration + dialogue
│       ├── image_generator.py   # generate_image()        -> Stable Diffusion (placeholder fallback)
│       ├── layout_builder.py    # build_comic_layout()    -> matches images + text
│       ├── exporters.py         # save_pdf()              -> timestamped PDF
│       ├── pipeline.py          # create_comic()          -> runs the whole workflow
│       ├── gemini_client.py     # shared Gemini call + retries
│       └── mock_ai.py           # offline stand-ins (COMICCRAFT_MOCK=1)
├── templates/                   # index.html, comic_preview.html, export_success.html
├── static/                      # panels/ (images), exports/ (PDFs), img/background.svg
├── tests/                       # pytest suite (runs offline)
├── scripts/load_test.py         # performance test script
├── 1. Brainstorming & Ideation/ ... 8.Project Demonstration/   # phase deliverables (PDF)
├── requirements.txt  .env.example  Dockerfile
```

## Quick start
```bash
python -m venv env
env\Scripts\activate            # Windows      |   source env/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # then paste your GEMINI_API_KEY and HF_API_KEY
uvicorn app.main:app --reload
```
Open <http://127.0.0.1:8000> (app) and <http://127.0.0.1:8000/docs> (interactive API docs).

**Try it without keys or a GPU** - offline demo mode (mock story + placeholder panels):
```bash
COMICCRAFT_MOCK=1 uvicorn app.main:app --reload        # Windows PowerShell: $env:COMICCRAFT_MOCK=1
```

## Important notes on models
* The project brief names `models/gemini-1.5-flash`, `models/gemini-1.5-pro` and `runwayml/stable-diffusion-v1-5`.
  Google has **retired the Gemini 1.5 models** and the Stable Diffusion 1.5 weights moved to
  `stable-diffusion-v1-5/stable-diffusion-v1-5`, so all three IDs are configurable in `.env`
  (`GEMINI_FLASH_MODEL`, `GEMINI_PRO_MODEL`, `SD_MODEL_ID`). Defaults use Google's `-latest` aliases. If your key cannot
  access a model, run `client.models.list()` to see the names available to you and update `.env`.
* The code uses the current `google-genai` SDK (the older `google-generativeai` package is deprecated).
* Stable Diffusion needs a GPU for practical speed (a free Colab/Kaggle T4 works). On CPU each image can take minutes;
  lower `IMAGE_STEPS` / `IMAGE_SIZE` in `.env`. If the model cannot load, ComicCraft falls back to labelled placeholder
  panels so the rest of the pipeline still works.

## API
| Method | Route | Purpose |
|---|---|---|
| GET | `/` | Story form |
| POST | `/generate` | Form -> full pipeline -> comic preview page |
| POST | `/generate-comic/json` | JSON body (`PromptRequest`) -> `{layout, pdf_path}` |
| GET | `/download/{file}` | Download exported PDF |
| GET | `/export-success?file=` | Success page |
| GET | `/test-image?prompt=` | Test image generation only |
| GET | `/health` | Liveness check |

```bash
curl -X POST http://127.0.0.1:8000/generate-comic/json -H "Content-Type: application/json" \
  -d '{"story_prompt":"A brave fox exploring an enchanted forest","character_name":"Rusty","setting":"forest","tone":"dramatic","art_style":"anime"}'
```

## Tests
```bash
pytest -q                                   # 21 tests, offline
COMICCRAFT_MOCK=1 uvicorn app.main:app &    # then:
python scripts/load_test.py --path /generate --method POST --users 10 --duration 15
```

## Docker
```bash
docker build -t comiccraft . && docker run --env-file .env -p 8000:8000 comiccraft
```

## Security
Secrets live only in `.env` (git-ignored). Inputs are validated with Pydantic; the download route only serves files matching
`comic_<timestamp>.pdf` inside `static/exports` (path-traversal safe).
