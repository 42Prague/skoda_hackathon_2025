"""
AI Orchestrator
---------------
Central module for all AI calls through Azure OpenAI.
Handles prompt loading, variable injection, language detection, retries, validation.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from swx_api.app.services.azure_llm_client import AzureLLMClient
from swx_api.app.config.settings import app_settings
from swx_api.core.middleware.logging_middleware import logger

# Optional import for audit logging
try:
    from swx_api.app.services.audit_service import AuditService
except ImportError:
    AuditService = None


CZECH_CHARS = "áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ"


class AIOrchestrator:
    """Orchestrates all AI calls through Azure OpenAI."""
    
    def __init__(self):
        self.prompts_dir = Path(__file__).parent.parent.parent / "app" / "prompts"
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._prompt_cache: Dict[str, str] = {}
        self.max_retries = app_settings.AI_MAX_RETRIES
        self.timeout_seconds = app_settings.AI_TIMEOUT_SECONDS
        self.audit_service = AuditService() if (AuditService and app_settings.ENABLE_AI_AUDIT_LOGGING) else None
    
    async def run(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        schema: Dict[str, Any],
        language: Optional[str] = None,
        temperature: float = 0.7,  # Ignored - Azure GPT-5.1 uses default only
        max_completion_tokens: int = 1024,  # Default to 1024
    ) -> Dict[str, Any]:
        """
        Execute AI call with prompt template and variable injection.
        
        Args:
            prompt_name: Name of prompt template file (without .txt)
            variables: Dictionary of variables to inject into template
            schema: Expected JSON schema for response
            language: "cz", "en", or None for auto-detect
            temperature: LLM temperature (default: 0.7)
            max_completion_tokens: Maximum completion tokens (default: 2048)
            
        Returns:
            Validated JSON response matching schema
        """
        # Force Azure provider - check if fallback is enabled
        if app_settings.AI_FORCE_FALLBACK:
            logger.warning(f"AI_FORCE_FALLBACK enabled - using fallback for {prompt_name}. This should be False for Azure.")
            return await self._fallback_response(prompt_name, variables, schema, "AI_FORCE_FALLBACK enabled")
        
        # Validate Azure provider is set
        if app_settings.SKILL_LLM_PROVIDER != "azure":
            logger.warning(f"SKILL_LLM_PROVIDER is {app_settings.SKILL_LLM_PROVIDER}, expected 'azure'. Forcing Azure usage.")
        
        try:
            template = self._load_prompt(prompt_name)
            prompt = self._inject(template, variables)
            
            detected_lang = language or self._detect_language(prompt)
            
            if detected_lang == "cz":
                prompt = self._add_czech_instructions(prompt)
            else:
                prompt = self._add_english_instructions(prompt)
            
            response = await self._call_azure(
                prompt=prompt,
                schema=schema,
                temperature=temperature,
                max_completion_tokens=max_completion_tokens,
            )
            
            validated = self._validate_schema(response, schema)
            validated["detected_language"] = detected_lang
            validated["ai_mode"] = "azure"
            
            if self.audit_service:
                try:
                    await self.audit_service.log_ai_call(
                        prompt_name=prompt_name,
                        variables=variables,
                        response=validated,
                        success=True
                    )
                except Exception as audit_exc:
                    logger.warning(f"AI audit logging failed: {audit_exc}")
            
            return validated
            
        except Exception as exc:
            logger.error(f"AI Orchestrator error for {prompt_name}: {exc}", exc_info=True)
            # NO FALLBACK - raise exception if Azure fails
            raise RuntimeError(f"AI Orchestrator failed for {prompt_name}. Azure OpenAI is required and not responding correctly: {exc}") from exc
    
    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt template from file."""
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        prompt_path = self.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {prompt_path}")
        
        template = prompt_path.read_text(encoding="utf-8")
        self._prompt_cache[prompt_name] = template
        
        return template
    
    def _inject(self, template: str, variables: Dict[str, Any]) -> str:
        """Inject variables into template placeholders."""
        result = template
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (list, dict)):
                value_str = json.dumps(value, ensure_ascii=False, indent=2)
            else:
                value_str = str(value)
            result = result.replace(placeholder, value_str)
        
        return result
    
    def _detect_language(self, text: str) -> str:
        """Detect if text contains Czech characters."""
        if any(char in CZECH_CHARS for char in text):
            return "cz"
        return "en"
    
    def _add_czech_instructions(self, prompt: str) -> str:
        """Add Czech-specific instructions to prompt."""
        instructions = """
        
        INSTRUKCE:
        - Odpověz POUZE ve formátu JSON.
        - Používej české popisky kde je to vhodné.
        - Všechna čísla musí být validní JSON hodnoty.
        - Pole musí odpovídat poskytnutému schématu.
        """
        return prompt + instructions
    
    def _add_english_instructions(self, prompt: str) -> str:
        """Add English-specific instructions to prompt."""
        instructions = """
        
        INSTRUCTIONS:
        - Respond ONLY in JSON format.
        - All numbers must be valid JSON values.
        - Fields must match the provided schema.
        - Do not include any text outside the JSON object.
        """
        return prompt + instructions
    
    async def _call_azure(
        self,
        prompt: str,
        schema: Dict[str, Any],
        temperature: float = 0.7,  # Ignored - Azure GPT-5.1 uses default only
        max_completion_tokens: int = 1024,  # Default to 1024
    ) -> Dict[str, Any]:
        """Call Azure OpenAI with retry logic. Uses minimal Azure 2025-01-01-preview format."""
        system_message = "You are an expert HR and career development analyst for Škoda Auto. Always respond with valid JSON only. Return ONLY valid JSON, no other text."
        
        for attempt in range(self.max_retries):
            try:
                azure_client = AzureLLMClient(
                    endpoint=app_settings.AZURE_OPENAI_ENDPOINT or "",
                    api_key=app_settings.AZURE_OPENAI_API_KEY or "",
                    model=app_settings.AZURE_OPENAI_MODEL,
                    api_version=app_settings.AZURE_OPENAI_API_VERSION,
                    deployment_name=app_settings.AZURE_OPENAI_DEPLOYMENT_NAME or "",
                )
                
                async with azure_client:
                    # Temperature is NOT sent - Azure GPT-5.1 only supports default
                    response = await azure_client.call_llm(
                        prompt=prompt,
                        schema=schema,
                        system_message=system_message,
                        max_completion_tokens=max_completion_tokens,
                    )
                
                return response
                
            except Exception as exc:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Azure call attempt {attempt + 1} failed: {exc}")
                continue
        
        raise RuntimeError("All Azure retry attempts failed")
    
    def _validate_schema(self, response: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate response matches expected schema."""
        if not isinstance(response, dict):
            raise ValueError("Response must be a dictionary")
        
        validated = {}
        
        for key, expected_type in schema.items():
            if key not in response:
                if expected_type == list:
                    validated[key] = []
                elif expected_type == dict:
                    validated[key] = {}
                elif expected_type == str:
                    validated[key] = ""
                elif expected_type in (int, float):
                    validated[key] = 0
                elif expected_type == bool:
                    validated[key] = False
                else:
                    validated[key] = None
            else:
                value = response[key]
                if expected_type == list and not isinstance(value, list):
                    validated[key] = [value] if value else []
                elif expected_type == dict and not isinstance(value, dict):
                    validated[key] = {}
                elif expected_type == str and not isinstance(value, str):
                    validated[key] = str(value)
                elif expected_type in (int, float) and not isinstance(value, (int, float)):
                    try:
                        validated[key] = expected_type(value)
                    except (ValueError, TypeError):
                        validated[key] = 0
                else:
                    validated[key] = value
        
        return validated
    
    async def _fallback_response(
        self,
        prompt_name: str,
        variables: Dict[str, Any],
        schema: Dict[str, Any],
        error_message: str,
    ) -> Dict[str, Any]:
        """Generate fallback response when AI fails."""
        logger.warning(f"AI fallback triggered for {prompt_name}: {error_message}")
        
        fallback = {}
        for key, expected_type in schema.items():
            if expected_type == list:
                fallback[key] = []
            elif expected_type == dict:
                fallback[key] = {}
            elif expected_type == str:
                fallback[key] = f"AI analysis unavailable: {error_message}"
            elif expected_type in (int, float):
                fallback[key] = 0
            elif expected_type == bool:
                fallback[key] = False
            else:
                fallback[key] = None
        
        fallback["ai_mode"] = "fallback"
        fallback["error"] = error_message
        fallback["detected_language"] = "en"
        
        if self.audit_service:
            try:
                await self.audit_service.log_ai_call(
                    prompt_name=prompt_name,
                    variables=variables,
                    response=fallback,
                    success=False,
                    error=error_message
                )
            except Exception as audit_exc:
                logger.warning(f"AI audit logging failed: {audit_exc}")
        
        return fallback
    
    async def _retry(
        self,
        func,
        *args,
        max_attempts: int = 3,
        **kwargs
    ) -> Any:
        """Retry function with exponential backoff."""
        for attempt in range(max_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                if attempt == max_attempts - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Retry attempt {attempt + 1} failed, waiting {wait_time}s: {exc}")
                import asyncio
                await asyncio.sleep(wait_time)
        
        raise RuntimeError("All retry attempts failed")

