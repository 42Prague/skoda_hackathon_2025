"""
Async LLM Client Service
------------------------
Provides explicit provider selection for Featherless, OpenAI, or Ollama
using the OpenAI-compatible SDK with structured logging and TONE support.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx
from openai import AsyncOpenAI

from swx_api.app.config.settings import app_settings
from swx_api.app.services.tone_service import get_tone_service
from swx_api.core.middleware.logging_middleware import logger

# Export for test mocking compatibility
OpenAI = AsyncOpenAI
try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    ollama_endpoint: Optional[str] = None
    ollama_model: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_api_version: Optional[str] = None
    azure_deployment_name: Optional[str] = None

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = (app_settings.SKILL_LLM_PROVIDER or "featherless").lower()
        fallback_model = app_settings.SKILL_LLM_MODEL or app_settings.FEATHERLESS_MODEL

        if provider == "heuristic":
            return cls(
                provider="heuristic",
                model="heuristic",
                api_key=None,
                endpoint=None,
                ollama_endpoint=None,
                ollama_model=None,
            )

        if provider == "azure":
            return cls(
                provider="azure",
                model=app_settings.AZURE_OPENAI_MODEL,
                api_key=app_settings.AZURE_OPENAI_API_KEY,
                endpoint=None,
                ollama_endpoint=app_settings.OLLAMA_ENDPOINT or "http://localhost:11434/v1",
                ollama_model=app_settings.OLLAMA_MODEL or "llama3.1",
                azure_endpoint=app_settings.AZURE_OPENAI_ENDPOINT,
                azure_api_key=app_settings.AZURE_OPENAI_API_KEY,
                azure_api_version=app_settings.AZURE_OPENAI_API_VERSION,
                azure_deployment_name=app_settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            )

        if provider == "openai":
            return cls(
                provider="openai",
                model=app_settings.OPENAI_MODEL or fallback_model,
                api_key=app_settings.OPENAI_API_KEY,
                endpoint="https://api.openai.com/v1",
                ollama_endpoint=app_settings.OLLAMA_ENDPOINT or "http://localhost:11434/v1",
                ollama_model=app_settings.OLLAMA_MODEL or "llama3.1",
            )

        if provider == "ollama":
            return cls(
                provider="ollama",
                model=app_settings.OLLAMA_MODEL or "llama3.1",
                api_key=None,
                endpoint=None,
                ollama_endpoint=app_settings.OLLAMA_ENDPOINT or "http://localhost:11434/v1",
                ollama_model=app_settings.OLLAMA_MODEL or "llama3.1",
            )

        # Default -> Featherless
        return cls(
            provider="featherless",
            model=app_settings.FEATHERLESS_MODEL,
            api_key=app_settings.FEATHERLESS_API_KEY,
            endpoint=app_settings.FEATHERLESS_BASE_URL,
            ollama_endpoint=app_settings.OLLAMA_ENDPOINT or "http://localhost:11434/v1",
            ollama_model=app_settings.OLLAMA_MODEL or "llama3.1",
        )


class LLMClient:
    """Async LLM client with explicit provider selection and structured logs."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self.tone_service = get_tone_service()
        self._client: Optional[AsyncOpenAI] = None
        self._http_client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "LLMClient":
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=120.0)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def analyze_skills(
        self,
        employee_data: Dict[str, Any],
        role_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze employee skills via configured provider."""
        schema = {
            "current_skills": list,
            "missing_skills": list,
            "gap_score": int,
            "ai_gap_score": int,
            "ai_readiness": int,
            "ai_risk_signal": int,
            "ai_skill_recommendations_count": int,
            "strengths": list,
            "recommended_roles": list,
            "development_path": list,
            "analysis_summary": str,
        }
        prompt = self._build_skill_analysis_prompt(employee_data, role_requirements, schema)
        system_message = "You are an expert HR and career development analyst."

        provider = self._selected_provider()
        if provider == "heuristic" or app_settings.AI_FORCE_FALLBACK:
            logger.info("LLM provider set to heuristic/fallback - returning generated fallback response")
            fallback = self._generate_fallback_response(schema)
            return self._validate_analysis_result(fallback)
        if provider == "azure":
            from swx_api.app.services.azure_llm_client import AzureLLMClient
            azure_client = AzureLLMClient(
                endpoint=self.config.azure_endpoint or "",
                api_key=self.config.azure_api_key or "",
                model=self.config.model,
                api_version=self.config.azure_api_version or "2024-02-15-preview",
                deployment_name=self.config.azure_deployment_name or ""
            )
            async with azure_client:
                result = await azure_client.analyze_skills(employee_data, role_requirements)
        elif provider == "ollama":
            result = await self._invoke_ollama(
                prompt=prompt,
                schema=schema,
                system_message=system_message,
                temperature=0.7,
                max_tokens=2000,
            )
        else:
            result = await self._invoke_openai_compatible(
                provider_label=provider,
                prompt=prompt,
                schema=schema,
                system_message=system_message,
                temperature=0.7,
                max_tokens=2000,
            )

        return self._validate_analysis_result(result)

    async def call_llm(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Generic async LLM call with TONE helpers."""
        # Check if force fallback is enabled
        if app_settings.AI_FORCE_FALLBACK:
            logger.info("AI_FORCE_FALLBACK enabled - returning fallback response")
            return self._generate_fallback_response(schema)
        
        apply_prompt = prompt
        if schema:
            apply_prompt = self.tone_service.build_tone_prompt(prompt, schema)

        base_system = system_message or "You are a helpful AI assistant."
        if self.tone_service.use_tone:
            base_system += " Respond using TONE format (Token-Optimized Notation Engine) to save tokens."
        else:
            base_system += " Always respond with valid JSON only."

        provider = self._selected_provider()
        if provider == "heuristic":
            logger.info("LLM provider set to heuristic - using fallback response")
            return self._generate_fallback_response(schema)
        if provider == "azure":
            from swx_api.app.services.azure_llm_client import AzureLLMClient
            azure_client = AzureLLMClient(
                endpoint=self.config.azure_endpoint or "",
                api_key=self.config.azure_api_key or "",
                model=self.config.model,
                api_version=self.config.azure_api_version or "2024-02-15-preview",
                deployment_name=self.config.azure_deployment_name or ""
            )
            async with azure_client:
                return await azure_client.call_llm(
                    prompt=apply_prompt,
                    schema=schema,
                    system_message=base_system,
                    temperature=temperature,
                    max_completion_tokens=max_tokens,  # Azure uses max_completion_tokens, not max_tokens
                )
        
        if provider == "ollama":
            return await self._invoke_ollama(
                prompt=apply_prompt,
                schema=schema,
                system_message=base_system,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        return await self._invoke_openai_compatible(
            provider_label=provider,
            prompt=apply_prompt,
            schema=schema,
            system_message=base_system,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def _selected_provider(self) -> str:
        provider = (self.config.provider or "").lower()
        if provider not in {"heuristic", "featherless", "openai", "ollama", "azure"}:
            raise ValueError(f"Unsupported LLM provider: {provider}")
        return provider

    def _build_skill_analysis_prompt(
        self,
        employee_data: Dict[str, Any],
        role_requirements: Optional[Dict[str, Any]],
        schema: Dict[str, Any],
    ) -> str:
        employee_id = employee_data.get("employee_id", "Unknown")
        department = employee_data.get("department", "Unknown")
        current_skills = employee_data.get("skills", [])

        base_prompt = f"""Analyze the following employee's skills and provide a comprehensive assessment.

Employee ID: {employee_id}
Department: {department}
Current Skills: {', '.join(current_skills) if current_skills else 'None listed'}
"""

        if role_requirements:
            required_skills = role_requirements.get("required_skills", [])
            preferred_skills = role_requirements.get("preferred_skills", [])
            base_prompt += f"""
Target Role Requirements:
- Required Skills: {', '.join(required_skills) if required_skills else 'None'}
- Preferred Skills: {', '.join(preferred_skills) if preferred_skills else 'None'}
"""

        example_data = {
            "current_skills": ["Python", "SQL"],
            "missing_skills": ["Docker"],
            "gap_score": 75,
            "ai_gap_score": 74,
            "ai_readiness": 78,
            "ai_risk_signal": 32,
            "ai_skill_recommendations_count": 3,
            "strengths": ["Data analysis depth"],
            "recommended_roles": ["Data Engineer"],
            "development_path": ["Learn Docker basics", "Deploy sample services"],
            "analysis_summary": "Employee has strong analytics strength but needs DevOps coverage.",
        }
        return self.tone_service.build_tone_prompt(base_prompt, schema, example_data)

    async def _invoke_openai_compatible(
        self,
        *,
        provider_label: str,
        prompt: str,
        schema: Dict[str, Any],
        system_message: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        if not self.config.api_key or not self.config.endpoint:
            raise ValueError(f"{provider_label} API key is not configured")

        client = await self._get_client()
        response_format = None if self.tone_service.use_tone else {"type": "json_object"}
        start = time.perf_counter()
        try:
            response = await client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                response_format=response_format,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            self._log_ai_failure(exc)
            raise

        self._log_ai_success(
            provider_label=provider_label,
            model=self.config.model,
            start_time=start,
            usage=getattr(response, "usage", None),
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        return self.tone_service.parse_llm_response(content, schema)

    async def _invoke_ollama(
        self,
        *,
        prompt: str,
        schema: Dict[str, Any],
        system_message: str,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        endpoint = (self.config.ollama_endpoint or "http://localhost:11434/v1").rstrip("/")
        model = self.config.ollama_model or "llama3.1"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "temperature": temperature,
            "options": {"num_predict": max_tokens},
        }

        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=120.0)

        start = time.perf_counter()
        try:
            response = await self._http_client.post(f"{endpoint}/chat/completions", json=payload)
            response.raise_for_status()
        except Exception as exc:
            self._log_ai_failure(exc)
            raise

        payload_json = response.json()
        content = (
            payload_json.get("message", {}).get("content")
            or payload_json.get("choices", [{}])[0].get("message", {}).get("content")
        )
        if not content:
            raise ValueError("Empty response from Ollama")

        self._log_ai_success(
            provider_label="ollama",
            model=model,
            start_time=start,
            usage=None,
        )
        return self.tone_service.parse_llm_response(content, schema)

    def _generate_fallback_response(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback response matching schema when AI_FORCE_FALLBACK is enabled."""
        fallback = {}
        for key, expected_type in schema.items():
            if expected_type == list:
                fallback[key] = []
            elif expected_type == dict:
                fallback[key] = {}
            elif expected_type == str:
                fallback[key] = f"Fallback response (AI_FORCE_FALLBACK enabled)"
            elif expected_type in (int, float):
                fallback[key] = 0
            elif expected_type == bool:
                fallback[key] = False
            else:
                fallback[key] = None
        fallback["ai_mode"] = "fallback"
        fallback["fallback_reason"] = "AI_FORCE_FALLBACK enabled"
        return fallback

    def _validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        ai_gap = int(result.get("ai_gap_score", result.get("gap_score", 65)))
        ai_readiness = int(result.get("ai_readiness", ai_gap))
        ai_risk = int(result.get("ai_risk_signal", max(0, 100 - ai_readiness)))
        ai_skill_recs = int(
            result.get(
                "ai_skill_recommendations_count",
                len(result.get("missing_skills", [])),
            )
        )

        return {
            "current_skills": result.get("current_skills", []),
            "missing_skills": result.get("missing_skills", []),
            "gap_score": int(result.get("gap_score", ai_gap)),
            "ai_gap_score": ai_gap,
            "ai_readiness": ai_readiness,
            "ai_risk_signal": ai_risk,
            "ai_skill_recommendations_count": ai_skill_recs,
            "strengths": result.get("strengths", []),
            "recommended_roles": result.get("recommended_roles", []),
            "development_path": result.get("development_path", []),
            "analysis_summary": result.get("analysis_summary", "Analysis completed."),
        }

    async def _get_client(self) -> AsyncOpenAI:
        if self.config.provider == "ollama":
            raise RuntimeError("Ollama provider does not use the OpenAI SDK client")
        if self.config.provider == "azure":
            raise RuntimeError("Azure provider uses AzureLLMClient, not OpenAI SDK client")
        if not self._client:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=self.config.endpoint,
            )
        return self._client

    def _log_ai_success(
        self,
        *,
        provider_label: str,
        model: str,
        start_time: float,
        usage: Any,
    ) -> None:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
        logger.info("[AI] Provider=%s Model=%s", provider_label, model)
        logger.info("[AI] Request tokens=%s", prompt_tokens if prompt_tokens is not None else "unknown")
        logger.info("[AI] Response tokens=%s", completion_tokens if completion_tokens is not None else "unknown")
        logger.info("[AI] Elapsed_ms=%s", elapsed_ms)
        logger.info("[AI] Status=success")

    def _log_ai_failure(self, error: Exception) -> None:
        logger.error("[AI] Fallback mode triggered: reason=%s", error)
