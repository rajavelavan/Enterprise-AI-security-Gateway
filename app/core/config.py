"""Application settings and environment configuration.

Manages DLP policy settings, sensitive keyword lists, and LLM provider
configuration via pydantic-settings with environment variable support.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the AI Security Gateway.

    All settings can be overridden via environment variables or a ``.env``
    file in the project root.
    """

    PROJECT_NAME: str = "Cryptographic AI Governance Gateway"
    API_V1_STR: str = "/api/v1"

    # --------------- DLP Configuration ---------------
    # DLP_MODE controls how the gateway handles detected violations:
    #   "block"  — reject the request entirely with HTTP 403
    #   "redact" — replace sensitive content with mask and forward
    #   "audit"  — log findings but forward the original prompt unchanged
    DLP_MODE: str = "redact"
    DLP_REDACTION_MASK: str = "[REDACTED]"

    # Predefined sensitive keywords for the Aho-Corasick DFA scanner.
    # In production, these should be loaded from a database or config file
    # and hot-reloaded via the /admin/dlp/reload endpoint.
    SENSITIVE_KEYWORDS: list[str] = [
        "CONFIDENTIAL",
        "SSN",
        "CREDIT_CARD",
        "PASSWORD",
        "SECRET_KEY",
        "TOP SECRET",
        "INTERNAL ONLY",
        "DO NOT DISTRIBUTE",
        "api_key",
        "auth_token",
        "bearer_token",
        "private_key",
    ]

    # --------------- LLM Provider Configuration ---------------
    LLM_BASE_URL: str = "https://api.openai.com/v1/chat/completions"
    LLM_API_KEY: str = ""       # Loaded from environment variable LLM_API_KEY
    LLM_MODEL: str = "gpt-4"
    LLM_TIMEOUT: float = 30.0   # Seconds before LLM request times out

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
