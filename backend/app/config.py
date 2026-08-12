"""
Central application configuration.

All tunables live here and are sourced from environment variables (via .env).
Nothing else in the app should call os.environ directly -- this keeps
config drift from creeping into random modules.

Provider fields use Literal types rather than plain str deliberately: a
typo like EMBEDDING_PROVIDER=OpenAI (wrong case) would otherwise silently
fall back to "local" (since the code just checks `== "openai"`), which is a
confusing way to fail -- the app would run, just with worse retrieval
quality, and nothing would tell you why. With Literal, pydantic-settings
rejects the bad value at startup with a clear error naming the allowed
values, so misconfiguration fails loudly instead of silently.
"""
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Provider selection -------------------------------------------------
    # "local" (default): TF-IDF embeddings, zero network calls, zero cost.
    # "openai": text-embedding-3-small, requires OPENAI_API_KEY.
    embedding_provider: Literal["local", "openai"] = "local"

    # "openai" (default): gpt-4o-mini if OPENAI_API_KEY is set, otherwise
    #   automatically falls back to "extractive" behavior at runtime.
    # "extractive": explicitly force the no-LLM fallback even if a key is
    #   set -- useful for testing/demoing the fallback path deliberately.
    generation_provider: Literal["openai", "extractive"] = "openai"

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_generation_model: str = "gpt-4o-mini"

    # --- Storage -------------------------------------------------------------
    database_path: str = "knowledge_inbox.db"

    # --- Chunking --------------------------------------------------------------
    chunk_size_chars: int = 800
    chunk_overlap_chars: int = 150

    # --- Retrieval -------------------------------------------------------------
    top_k: int = 4

    # --- HTTP fetch --------------------------------------------------------------
    fetch_timeout_seconds: int = 10
    max_page_chars: int = 20_000

    # --- CORS ------------------------------------------------------------------
    # Example env value: CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
    cors_origins: list[str] = Field(
        default=[],
        validation_alias="CORS_ORIGINS",
    )


settings = Settings()
