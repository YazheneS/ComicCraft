"""Thin wrapper around the Google Gen AI SDK with retries, used by gemini_flash / gemini_pro."""
import time

from app import config
from app.services.errors import GenerationError

_client = None


def _get_client():
    """Create the Gemini client once (lazy) so the app can start without a key."""
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise GenerationError("GEMINI_API_KEY is not set. Add it to your .env file.")
        from google import genai  # imported lazily: keeps tests / mock mode light

        _client = genai.Client(api_key=config.GEMINI_API_KEY)
    return _client


def call_gemini(model: str, prompt: str, json_mode: bool = False, retries: int = 3) -> str:
    """Send a prompt to a Gemini model and return the text. Retries transient failures."""
    from google.genai import types

    cfg = types.GenerateContentConfig(
        response_mime_type="application/json" if json_mode else "text/plain",
        temperature=0.9,
    )
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = _get_client().models.generate_content(model=model, contents=prompt, config=cfg)
            text = (response.text or "").strip()
            if not text:
                raise GenerationError("Gemini returned an empty response.")
            return text
        except GenerationError:
            raise
        except Exception as exc:  # network / quota / 5xx
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)  # simple linear back-off
    raise GenerationError(f"Gemini request failed after {retries} attempts: {last_error}")
