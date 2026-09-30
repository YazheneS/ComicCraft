"""Central configuration: paths, model IDs and secrets loaded from the environment / .env file."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---- folders ----
STATIC_DIR = BASE_DIR / "static"
PANELS_DIR = STATIC_DIR / "panels"
EXPORTS_DIR = STATIC_DIR / "exports"
TEMPLATES_DIR = BASE_DIR / "templates"


def ensure_dirs() -> None:
    """Create the output folders if they do not exist yet."""
    PANELS_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---- secrets ----
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
HF_API_KEY = os.getenv("HF_API_KEY", "")

# ---- models (override in .env; Google retires model names often) ----
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-flash-latest")
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-pro-latest")
SD_MODEL_ID = os.getenv("SD_MODEL_ID", "stable-diffusion-v1-5/stable-diffusion-v1-5")

# ---- generation settings ----
NUM_PANELS = 5
IMAGE_STEPS = int(os.getenv("IMAGE_STEPS", "25"))
IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "512"))


def is_mock_mode() -> bool:
    """True when COMICCRAFT_MOCK=1 -> offline deterministic AI stand-ins (demo / tests)."""
    return os.getenv("COMICCRAFT_MOCK", "0").strip().lower() in {"1", "true", "yes"}
