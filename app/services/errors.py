"""Custom exceptions so routes can translate AI failures into clean HTTP errors."""


class GenerationError(RuntimeError):
    """Raised when an AI call fails or returns unusable output."""
