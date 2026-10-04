from functools import lru_cache

from app.config import get_settings
from app.services.base import StoryboardGenerator
from app.services.storyboard import FakeGenerator


@lru_cache
def get_generator() -> StoryboardGenerator:
    """Pick the storyboard generator from settings (cached: one instance per process)."""
    settings = get_settings()
    if settings.generator == "fake":
        return FakeGenerator()

    # Imported lazily so the fake path never needs the Gemini SDK.
    from app.services.gemini import GeminiGenerator

    return GeminiGenerator(
        api_key=settings.gemini_api_key.get_secret_value(),
        model=settings.gemini_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
