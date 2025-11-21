"""
Environment Variable Validator
------------------------------
Validates required environment variables at startup.
Aborts if critical Azure variables are missing when provider=azure.
"""

import logging
import os
import sys
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """Mask secret values for logging."""
    if not value or len(value) <= visible_chars * 2:
        return "***"
    return f"{value[:visible_chars]}...{value[-visible_chars]}"


class EnvironmentValidator:
    """Validates environment variables at startup."""
    
    # Azure required variables when SKILL_LLM_PROVIDER=azure
    AZURE_REQUIRED = {
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
        "AZURE_OPENAI_API_VERSION",
    }
    
    # Optional Azure variables (have defaults)
    AZURE_OPTIONAL = {
        "AZURE_OPENAI_MODEL",
    }
    
    # General required variables
    GENERAL_REQUIRED = {
        "PROJECT_NAME",
    }
    
    def __init__(self):
        self.variables_present: Set[str] = set()
        self.variables_missing: Set[str] = set()
        self.secrets_masked: Dict[str, str] = {}
        
    def validate(self) -> bool:
        """
        Validate environment variables.
        
        Returns:
            True if validation passes, False otherwise
        """
        logger.info("=" * 80)
        logger.info("Environment Variable Validation")
        logger.info("=" * 80)
        
        # Check all environment variables
        all_env_vars = set(os.environ.keys())
        
        # Find Azure variables and log with proper masking format
        azure_vars = {k for k in all_env_vars if k.startswith("AZURE_")}
        logger.info(f"\nFound {len(azure_vars)} Azure environment variables:")
        for var in sorted(azure_vars):
            value = os.environ.get(var, "")
            if "KEY" in var or "SECRET" in var or "PASSWORD" in var:
                masked = mask_secret(value)
                self.secrets_masked[var] = masked
                logger.info(f"  ✓ {var} ✗{masked}")
            else:
                logger.info(f"  ✓ {var}={value}")
        
        # Check LLM provider
        provider = os.environ.get("SKILL_LLM_PROVIDER", "heuristic").lower()
        ai_force_fallback = os.environ.get("AI_FORCE_FALLBACK", "false").lower() == "true"
        
        logger.info(f"\nLLM Provider: {provider}")
        logger.info(f"AI_FORCE_FALLBACK: {ai_force_fallback}")
        
        # Check required general variables
        logger.info(f"\nChecking required general variables:")
        for var in self.GENERAL_REQUIRED:
            value = os.environ.get(var)
            if value:
                self.variables_present.add(var)
                logger.info(f"  ✓ {var}={value}")
            else:
                self.variables_missing.add(var)
                logger.error(f"  ✗ {var} is MISSING (required)")
        
        # Check Azure variables if provider is azure
        if provider == "azure" and not ai_force_fallback:
            logger.info(f"\nChecking required Azure variables (provider=azure):")
            missing_azure = []
            
            for var in self.AZURE_REQUIRED:
                value = os.environ.get(var)
                if value and value.strip():
                    self.variables_present.add(var)
                    if "KEY" in var:
                        logger.info(f"  ✓ {var} ✗{mask_secret(value)}")
                    else:
                        logger.info(f"  ✓ {var}={value}")
                else:
                    self.variables_missing.add(var)
                    missing_azure.append(var)
                    logger.error(f"  ✗ {var} is MISSING or EMPTY (required for Azure)")
            
            # Check optional Azure variables
            for var in self.AZURE_OPTIONAL:
                value = os.environ.get(var)
                if value:
                    logger.info(f"  ✓ {var}={value} (optional, has default)")
                else:
                    logger.info(f"  ⚠ {var} not set (will use default)")
            
            # Validate AI_FORCE_FALLBACK
            if ai_force_fallback:
                logger.error(f"  ✗ AI_FORCE_FALLBACK=true but SKILL_LLM_PROVIDER=azure")
                logger.error(f"    Azure calls will be disabled. Set AI_FORCE_FALLBACK=false")
            
            # Abort if critical variables are missing
            if missing_azure:
                logger.error("\n" + "=" * 80)
                logger.error("FATAL: Missing required Azure environment variables!")
                logger.error("=" * 80)
                logger.error("Missing variables:")
                for var in missing_azure:
                    logger.error(f"  - {var}")
                logger.error("\nPlease set these variables in your .env file:")
                logger.error("  AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com")
                logger.error("  AZURE_OPENAI_API_KEY=your-api-key")
                logger.error("  AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name")
                logger.error("  AZURE_OPENAI_API_VERSION=2025-01-01-preview")
                logger.error("=" * 80)
                return False
        elif provider == "azure" and ai_force_fallback:
            logger.warning("\n⚠ WARNING: SKILL_LLM_PROVIDER=azure but AI_FORCE_FALLBACK=true")
            logger.warning("  Azure integration will be disabled. Set AI_FORCE_FALLBACK=false to enable.")
        elif provider != "azure":
            logger.info(f"\n✓ Skipping Azure validation (provider={provider})")
        
        # Log other important variables
        logger.info(f"\nOther environment variables present:")
        important_vars = [
            "DATABASE_URL",
            "DB_HOST",
            "DB_PORT",
            "DB_USER",
            "DB_NAME",
            "SKILL_LLM_PROVIDER",
            "ENVIRONMENT",
            "LOG_LEVEL",
            "SENTRY_DSN",
        ]
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                if "PASSWORD" in var or "SECRET" in var or "KEY" in var:
                    logger.info(f"  ✓ {var} ✗{mask_secret(value)}")
                else:
                    logger.info(f"  ✓ {var}={value}")
            else:
                logger.debug(f"  - {var} not set")
        
        logger.info("=" * 80)
        logger.info(f"Validation complete: {len(self.variables_present)} present, {len(self.variables_missing)} missing")
        logger.info("=" * 80)
        
        return len(self.variables_missing) == 0


def validate_environment() -> None:
    """
    Validate environment variables at startup.
    Aborts application if critical variables are missing.
    """
    validator = EnvironmentValidator()
    if not validator.validate():
        logger.error("Environment validation failed. Aborting startup.")
        sys.exit(1)

