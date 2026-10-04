from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    """App settings, read from environment variables and the optional .env file.

    Environment variables take precedence over .env; names are case-insensitive
    (GENERATOR, GEMINI_API_KEY, GEMINI_MODEL, LLM_TIMEOUT_SECONDS).
    """

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    generator: Literal["fake", "llm"] = "fake"
    # SecretStr keeps the key out of reprs, logs and tracebacks.
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_timeout_seconds: float = 20

    @model_validator(mode="after")
    def require_api_key_for_llm(self) -> "Settings":
        if self.generator == "llm" and not self.has_api_key:
            raise ValueError(
                "GENERATOR=llm requires GEMINI_API_KEY to be set (in the environment or .env)"
            )
        return self

    @property
    def has_api_key(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
