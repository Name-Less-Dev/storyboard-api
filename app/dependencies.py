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
    raise NotImplementedError("LLM generator is not implemented yet")
