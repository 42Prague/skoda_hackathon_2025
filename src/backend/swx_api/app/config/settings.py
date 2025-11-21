"""
Application Settings Configuration
----------------------------------
This module defines the global settings for the SwX-API.

It extends the base CoreSettings class from swx_api/core/config/settings.
"""

import logging
from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict
from swx_api.core.config.settings import Settings as CoreSettings


logger = logging.getLogger("app_settings")


class AppSettings(CoreSettings):
    model_config = SettingsConfigDict(
        # ONLY read from OS environment variables (Docker injects from .env via docker-compose)
        # In Docker: docker-compose reads .env → injects as environment variables → Settings reads from OS env
        # In local dev: User must export variables or use tool (direnv, etc.) - Settings reads from OS env
        # Do NOT read .env file directly - rely on OS environment variables only
        # This ensures no silent overrides and clear variable sources
        env_file=".env",  # Try .env for local dev compatibility, but OS env takes precedence
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=False,
        # Environment variables ALWAYS take precedence over .env file
        # In Docker, docker-compose sets OS env vars from .env, so .env file is never read
    )
    USE_NGROK: bool = Field(default=False)
    NGROK_AUTH_TOKEN: str = Field(default="")
    PROJECT_VERSION: str = Field(default="1.0")

    APP_PORT: int = Field(default=8000)
    REDIS_URL: str = Field(default="REDIS_URL")
    REDIS_HOST: str = Field(default="czfb-redis")
    REDIS_PORT: int = Field(default="6379")
    SESSION_SECRET_KEY: str = Field(default="DLgd15zT1qP4YYo5PEkJ_4DPPMi7iXSfp3vDTns1Xi")
    SESSION_COOKIE_NAME: str = Field(default="session_id")
    SESSION_TIMEOUT: int = Field(default=900)
    MCP_API_KEY: str = Field(default="")

    SKILL_LLM_PROVIDER: Literal["heuristic", "featherless", "openai", "ollama", "azure"] = Field(default="heuristic")
    FEATHERLESS_API_KEY: Optional[str] = Field(default=None)
    FEATHERLESS_MODEL: str = Field(default="meta-llama/Meta-Llama-3.1-8B-Instruct")
    FEATHERLESS_BASE_URL: str = Field(default="https://api.featherless.ai/v1")
    SKILL_LLM_MODEL: Optional[str] = Field(default=None)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: Optional[str] = Field(default=None)
    OLLAMA_ENDPOINT: Optional[str] = Field(default=None)
    OLLAMA_MODEL: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_MODEL: str = Field(default="gpt-4")
    AZURE_OPENAI_API_VERSION: str = Field(default="2025-01-01-preview")
    AZURE_OPENAI_DEPLOYMENT_NAME: Optional[str] = Field(default=None)
    ENABLE_AI_ORCHESTRATOR: bool = Field(default=True, description="Enable AI orchestrator for all AI calls")
    ENABLE_AI_AUDIT_LOGGING: bool = Field(default=True, description="Enable audit logging for AI responses")
    AI_MAX_RETRIES: int = Field(default=3, description="Maximum retries for AI calls")
    AI_TIMEOUT_SECONDS: int = Field(default=60, description="Timeout for AI calls in seconds")
    AI_FORCE_FALLBACK: bool = Field(default=False, description="Force fallback mode - skip all external AI calls")

    @model_validator(mode="after")
    def _validate_llm_credentials(cls, values: "AppSettings") -> "AppSettings":
        """
        Validate LLM provider configuration.
        
        When SKILL_LLM_PROVIDER=azure:
        - Requires AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME
        - Requires AI_FORCE_FALLBACK=False
        - Aborts if missing (no silent fallback)
        """
        provider = (values.SKILL_LLM_PROVIDER or "").lower()
        
        if provider == "azure":
            # Azure provider requires all variables - no silent fallback
            missing = []
            
            if not values.AZURE_OPENAI_ENDPOINT or not values.AZURE_OPENAI_ENDPOINT.strip():
                missing.append("AZURE_OPENAI_ENDPOINT")
            
            if not values.AZURE_OPENAI_API_KEY or not values.AZURE_OPENAI_API_KEY.strip():
                missing.append("AZURE_OPENAI_API_KEY")
            
            if not values.AZURE_OPENAI_DEPLOYMENT_NAME or not values.AZURE_OPENAI_DEPLOYMENT_NAME.strip():
                missing.append("AZURE_OPENAI_DEPLOYMENT_NAME")
            
            if missing:
                error_msg = (
                    f"SKILL_LLM_PROVIDER=azure requires these environment variables: {', '.join(missing)}. "
                    f"Please set them in your .env file or environment."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Validate AI_FORCE_FALLBACK
            if values.AI_FORCE_FALLBACK:
                error_msg = (
                    "SKILL_LLM_PROVIDER=azure but AI_FORCE_FALLBACK=True. "
                    "Azure integration requires AI_FORCE_FALLBACK=False. "
                    "Please set AI_FORCE_FALLBACK=false in your .env file."
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Validate endpoint has no trailing slash
            if values.AZURE_OPENAI_ENDPOINT.endswith("/"):
                values.AZURE_OPENAI_ENDPOINT = values.AZURE_OPENAI_ENDPOINT.rstrip("/")
                logger.warning("Removed trailing slash from AZURE_OPENAI_ENDPOINT")
            
            logger.info(f"✓ Azure OpenAI configuration validated: endpoint={values.AZURE_OPENAI_ENDPOINT}, deployment={values.AZURE_OPENAI_DEPLOYMENT_NAME}")
        
        elif provider == "featherless":
            if not values.FEATHERLESS_API_KEY:
                logger.warning(
                    "SKILL_LLM_PROVIDER=featherless but FEATHERLESS_API_KEY missing. Falling back to heuristic provider."
                )
                values.SKILL_LLM_PROVIDER = "heuristic"
        
        elif provider == "heuristic":
            logger.info("Using heuristic LLM provider (no external API calls)")
        
        return values


# Create global settings instance
app_settings = AppSettings()
