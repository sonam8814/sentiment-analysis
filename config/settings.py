"""Application settings loaded from environment variables via Pydantic."""

from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Centralized configuration. All env vars are loaded and validated here."""

    # Supabase
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str = Field(..., description="Supabase anonymous/public key")
    supabase_table_name: str = Field(
        default="nps_responses", description="Table name for NPS data"
    )

    # LLM — Groq
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile", description="Groq model ID"
    )

    # LLM — Gemini
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-2.0-flash", description="Gemini model ID")

    # App behavior
    llm_provider_primary: Literal["groq", "gemini"] = Field(
        default="groq", description="Primary LLM provider"
    )
    llm_batch_size: int = Field(
        default=10, ge=1, le=50, description="Comments per LLM call"
    )
    llm_max_retries: int = Field(
        default=3, ge=1, le=10, description="Max retries per provider"
    )
    llm_timeout_seconds: int = Field(
        default=30, ge=5, le=120, description="LLM call timeout"
    )
    cache_dir: str = Field(default="./data/cache", description="Disk cache directory")
    cache_expiry_days: int = Field(default=30, ge=1, description="Cache TTL in days")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """Return a validated Settings instance. Fails loudly if required vars are missing."""
    return Settings()
