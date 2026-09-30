"""Pydantic schemas for request validation."""
from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Validated user input for comic generation (used by form route and JSON API)."""

    story_prompt: str = Field(..., min_length=5, max_length=500, description="Main idea for the comic")
    character_name: str = Field("Hero", min_length=1, max_length=40)
    setting: str = Field("forest", min_length=1, max_length=60)
    tone: str = Field("light-hearted", min_length=1, max_length=40)
    art_style: str = Field("comic book", min_length=1, max_length=40)

    model_config = {
        "json_schema_extra": {
            "example": {
                "story_prompt": "A brave fox exploring an enchanted forest",
                "character_name": "Rusty",
                "setting": "forest",
                "tone": "dramatic",
                "art_style": "anime",
            }
        }
    }
