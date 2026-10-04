import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.dependencies import get_generator
from app.services.gemini import GeminiGenerator
from app.services.storyboard import FakeGenerator


@pytest.fixture
def fresh_caches():
    get_settings.cache_clear()
    get_generator.cache_clear()
    yield
    get_settings.cache_clear()
    get_generator.cache_clear()


def test_suite_runs_with_fake_generator(fresh_caches):
    assert get_settings().generator == "fake"
    assert isinstance(get_generator(), FakeGenerator)


def test_llm_without_api_key_fails_with_clear_message(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(ValidationError, match="GENERATOR=llm requires GEMINI_API_KEY"):
        Settings(_env_file=None, generator="llm")


def test_api_key_is_hidden_from_repr():
    settings = Settings(_env_file=None, generator="llm", gemini_api_key="super-secret")

    assert "super-secret" not in repr(settings)


def test_llm_setting_selects_gemini_generator(monkeypatch, fresh_caches):
    monkeypatch.setenv("GENERATOR", "llm")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    generator = get_generator()  # builds the SDK client; no network call happens here

    assert isinstance(generator, GeminiGenerator)
