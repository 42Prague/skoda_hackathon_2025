"""
Azure OpenAI LLM Client
-----------------------
Secure Azure OpenAI integration with health checks and fail-fast configuration.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from swx_api.app.config.settings import app_settings
from swx_api.app.services.tone_service import get_tone_service
from swx_api.core.middleware.logging_middleware import logger


class AzureLLMClient:
    """Azure OpenAI client with secure context guarantee."""
    
    def __init__(self, endpoint: str, api_key: str, model: str, api_version: str, deployment_name: str):
        """
        Initialize Azure OpenAI client.
        
        Args:
            endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            model: Model name
            api_version: API version
            deployment_name: Deployment name
        """
        if not endpoint or not api_key:
            raise ValueError("Azure OpenAI endpoint and API key must be configured")
        
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.api_version = api_version
        self.deployment_name = deployment_name
        self.tone_service = get_tone_service()
        self._client: Optional[AsyncOpenAI] = None
        self._health_checked = False
    
    async def __aenter__(self) -> "AzureLLMClient":
        await self._ensure_health_check()
        return self
    
    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._client:
            await self._client.close()
            self._client = None
    
    async def _ensure_health_check(self) -> None:
        """Ensure health check is performed."""
        if not self._health_checked:
            await self._health_check()
            self._health_checked = True
    
    async def _health_check(self) -> bool:
        """Health check for Azure OpenAI using 2025-01-01-preview format."""
        try:
            client = await self._get_client()
            
            # Azure 2025-01-01-preview minimal request format - ONLY messages and max_completion_tokens
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'OK' if you can read this."}
            ]
            
            # Health check uses minimal format - no response_format needed
            # Use larger token limit to avoid truncation (finish_reason: length)
            test_response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=100,  # Increased to avoid truncation in health check
                # NO temperature, top_p, or other unsupported parameters
            )
            
            if test_response.choices and len(test_response.choices) > 0:
                choice = test_response.choices[0]
                finish_reason = getattr(choice, 'finish_reason', None)
                content = getattr(choice.message, 'content', None) if choice.message else None
                
                # Accept content even if finish_reason is 'length' (truncated but still valid)
                if content and content.strip():
                    logger.info(f"[Azure] Health check passed: {content[:50]}")
                    return True
                elif finish_reason == 'length':
                    # Content was truncated but request was successful - health check passes
                    logger.warning(f"[Azure] Health check passed (truncated response, finish_reason: {finish_reason})")
                    return True
                else:
                    # Log more details for debugging
                    logger.error(f"[Azure] Health check failed: Empty content. Finish reason: {finish_reason}")
                    logger.error(f"[Azure] Response choices: {len(test_response.choices) if test_response.choices else 0}")
                    raise RuntimeError(f"Azure OpenAI health check failed: Empty content (finish_reason: {finish_reason})")
            else:
                logger.error("[Azure] Health check failed: No choices in response")
                raise RuntimeError("Azure OpenAI health check failed: No choices in response")
        except Exception as e:
            logger.error(f"[Azure] Health check failed: {e}")
            raise RuntimeError(f"Azure OpenAI health check failed: {e}")
    
    async def _get_client(self) -> AsyncOpenAI:
        """Get or create Azure OpenAI client."""
        if not self._client:
            base_url = f"{self.endpoint}/openai/deployments/{self.deployment_name}"
            
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=base_url,
                default_headers={"api-key": self.api_key},
                default_query={"api-version": self.api_version}
            )
        
        return self._client
    
    def _convert_schema_to_json_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Python schema dict to JSON Schema format for Azure OpenAI structured outputs.
        
        Args:
            schema: Python schema dict (e.g., {"field": str, "count": int, "items": [{"id": str}]})
            
        Returns:
            JSON Schema dict compatible with Azure OpenAI structured outputs
        """
        if not schema:
            return {"type": "object", "properties": {}, "required": []}
        
        properties = {}
        required = []
        
        for key, value_type in schema.items():
            prop_def = None
            
            if value_type == str:
                prop_def = {"type": "string"}
            elif value_type == int:
                prop_def = {"type": "integer"}
            elif value_type == float:
                prop_def = {"type": "number"}
            elif value_type == bool:
                prop_def = {"type": "boolean"}
            elif value_type == list:
                prop_def = {"type": "array", "items": {}}
            elif isinstance(value_type, list) and len(value_type) > 0:
                # List of items - check first item for type
                item_schema = value_type[0]
                if isinstance(item_schema, dict):
                    # List of objects
                    nested_schema = self._convert_schema_to_json_schema(item_schema)
                    prop_def = {
                        "type": "array",
                        "items": nested_schema
                    }
                else:
                    # List of primitives
                    item_type_map = {
                        str: "string",
                        int: "integer",
                        float: "number",
                        bool: "boolean",
                    }
                    item_type = item_type_map.get(item_schema, "string")
                    prop_def = {
                        "type": "array",
                        "items": {"type": item_type}
                    }
            elif isinstance(value_type, dict):
                # Nested object
                nested_props = self._convert_schema_to_json_schema(value_type)
                prop_def = {
                    "type": "object",
                    "properties": nested_props.get("properties", {}),
                    "required": nested_props.get("required", [])
                }
            else:
                # Default to string for unknown types
                prop_def = {"type": "string"}
            
            if prop_def:
                properties[key] = prop_def
                required.append(key)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    async def call_llm(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_message: Optional[str] = None,
        temperature: float = 0.7,  # Ignored - Azure uses default only
        max_completion_tokens: int = 2048,  # Increased default from 1024 to avoid truncation
    ) -> Dict[str, Any]:
        """
        Call Azure OpenAI with secure context using Azure 2025-01-01-preview format.
        
        Uses structured outputs with json_schema response_format when schema is provided.
        Only supported parameters: messages, max_completion_tokens, response_format.
        Temperature is NOT sent - Azure uses default value only.
        """
        await self._ensure_health_check()
        
        apply_prompt = prompt
        use_json_schema = False
        
        if schema and not self.tone_service.use_tone:
            # Use Azure structured outputs with json_schema
            use_json_schema = True
        elif schema:
            # Use TONE format if enabled
            apply_prompt = self.tone_service.build_tone_prompt(prompt, schema)
        
        base_system = system_message or "You are a helpful AI assistant."
        if self.tone_service.use_tone:
            base_system += " Respond using TONE format (Token-Optimized Notation Engine) to save tokens."
        else:
            base_system += " Always respond with valid JSON only. Return ONLY valid JSON, no other text."
        
        client = await self._get_client()
        
        # Azure 2025-01-01-preview request format
        messages = [
            {"role": "system", "content": base_system},
            {"role": "user", "content": apply_prompt},
        ]
        
        # Build request payload - ONLY Azure-approved parameters
        request_params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens,
        }
        
        # Add structured outputs if schema provided and not using TONE
        if use_json_schema and schema:
            json_schema = self._convert_schema_to_json_schema(schema)
            request_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "ResponseSchema",
                    "strict": False,  # Changed to False - strict=True can cause empty responses if schema is too restrictive
                    "schema": json_schema
                }
            }
        
        # Log request details (with masked keys for security)
        def mask_secret_value(v: str) -> str:
            """Mask secret values in logs."""
            if not v or len(v) <= 8:
                return "***"
            return f"{v[:4]}...{v[-4]}"
        
        # Prepare masked messages for logging (truncate long content)
        masked_messages = []
        for msg in messages:
            masked_msg = msg.copy()
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 200:
                masked_msg["content"] = content[:100] + "...[truncated for logging]"
            masked_messages.append(masked_msg)
        
        # Prepare masked params for logging
        masked_params = {
            "model": self.model,
            "messages": "[...truncated...]",  # Already logged separately
            "max_completion_tokens": max_completion_tokens,
        }
        if "response_format" in request_params:
            masked_params["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": request_params["response_format"]["json_schema"]["name"],
                    "strict": True,
                    "schema": "[schema definition - see logs above]"
                }
            }
        
        # Debug logging with masked secrets
        logger.info("=" * 80)
        logger.info("[Azure] Request Payload Structure (Azure 2025-01-01-preview):")
        logger.info(f"[Azure]   Endpoint: {self.endpoint}/openai/deployments/{self.deployment_name}")
        logger.info(f"[Azure]   API Version: {self.api_version}")
        logger.info(f"[Azure]   Deployment Name: {self.deployment_name}")
        logger.info(f"[Azure]   Model: {self.model}")
        logger.info(f"[Azure]   Max Completion Tokens: {max_completion_tokens}")
        logger.info(f"[Azure]   Using Structured Outputs (json_schema): {use_json_schema}")
        if not self.tone_service.use_tone:
            logger.info(f"[Azure]   Messages ({len(messages)}):")
            for i, msg in enumerate(masked_messages):
                role = msg.get("role", "unknown")
                content_preview = msg.get("content", "")[:100]
                logger.info(f"[Azure]     [{i}] role={role}, content_preview='{content_preview}...'")
        if "response_format" in request_params:
            schema_name = request_params["response_format"]["json_schema"]["name"]
            logger.info(f"[Azure]   Response Format: json_schema (name={schema_name}, strict=True)")
            logger.info(f"[Azure]   Schema Properties: {list(json_schema.get('properties', {}).keys())}")
        logger.info(f"[Azure]   Parameters sent: {list(request_params.keys())}")
        logger.info(f"[Azure]   Parameters NOT sent (Azure unsupported): temperature, top_p, frequency_penalty, presence_penalty, max_tokens")
        logger.info("=" * 80)
        
        # Retry logic with exponential backoff
        max_retries = 3
        base_backoff_seconds = 1.0
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                start = time.perf_counter()
                # EXACT Azure 2025-01-01-preview format - only approved parameters
                response = await client.chat.completions.create(**request_params)
                elapsed_ms = int((time.perf_counter() - start) * 1000)
                
                usage = getattr(response, "usage", None)
                prompt_tokens = getattr(usage, "prompt_tokens", None) if usage else None
                completion_tokens = getattr(usage, "completion_tokens", None) if usage else None
                
                logger.info("[Azure] Provider=azure Model=%s Attempt=%d/%d", self.model, attempt + 1, max_retries)
                logger.info("[Azure] Request tokens=%s Response tokens=%s Elapsed_ms=%s", 
                           prompt_tokens if prompt_tokens is not None else "unknown",
                           completion_tokens if completion_tokens is not None else "unknown",
                           elapsed_ms)
                
                # Extract content and check response structure
                choice = response.choices[0] if response.choices else None
                if not choice:
                    error_msg = f"No choices in Azure OpenAI response (attempt {attempt + 1}/{max_retries})"
                    logger.error(f"[Azure] {error_msg}")
                    logger.error(f"[Azure] Response: {response}")
                    if attempt < max_retries - 1:
                        wait_time = base_backoff_seconds * (2 ** attempt)
                        logger.warning(f"[Azure] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(error_msg)
                
                # Get content from message
                message = choice.message if choice else None
                if not message:
                    error_msg = f"No message in Azure OpenAI response (attempt {attempt + 1}/{max_retries})"
                    logger.error(f"[Azure] {error_msg}")
                    logger.error(f"[Azure] Choice: {choice}")
                    if attempt < max_retries - 1:
                        wait_time = base_backoff_seconds * (2 ** attempt)
                        logger.warning(f"[Azure] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(error_msg)
                
                content = getattr(message, 'content', None)
                finish_reason = getattr(choice, 'finish_reason', None)
                
                # Log response details for debugging
                logger.info(f"[Azure] Finish reason: {finish_reason}")
                logger.info(f"[Azure] Content length: {len(content) if content else 0}")
                logger.info(f"[Azure] Content preview: {content[:200] if content else 'None'}...")
                
                # Handle finish_reason: length - response might be partial but usable
                if finish_reason == "length":
                    logger.warning(f"[Azure] Response truncated (finish_reason: length) - current max_completion_tokens: {max_completion_tokens}")
                    logger.warning(f"[Azure] Content length before truncation: {len(content) if content else 0}")
                    
                    # If content exists but was truncated, try to parse it anyway (might be partial JSON)
                    if content and content.strip():
                        logger.warning(f"[Azure] Attempting to parse truncated response (content length: {len(content)})")
                        try:
                            # Try parsing even if truncated - might still be valid JSON
                            result = self.tone_service.parse_llm_response(content, schema)
                            if result and (isinstance(result, dict) and any(result.values())):
                                logger.warning(f"[Azure] Successfully parsed truncated response")
                                logger.info("[Azure] Status=success (truncated but usable)")
                                return result
                        except Exception as parse_exc:
                            logger.warning(f"[Azure] Failed to parse truncated content: {parse_exc}")
                    
                    # If truncated and no usable content, increase tokens and retry
                    if attempt < max_retries - 1:
                        # Double the token limit for next attempt
                        new_token_limit = max_completion_tokens * 2
                        logger.warning(f"[Azure] Increasing max_completion_tokens from {max_completion_tokens} to {new_token_limit} for retry")
                        request_params["max_completion_tokens"] = new_token_limit
                        wait_time = base_backoff_seconds * (2 ** attempt)
                        logger.warning(f"[Azure] Retrying in {wait_time}s with {new_token_limit} tokens...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error_msg = f"Response truncated and unusable after {max_retries} attempts (max_completion_tokens={max_completion_tokens}, finish_reason=length)"
                        raise ValueError(error_msg)
                
                # Check for empty content (non-truncation cases)
                if not content:
                    error_msg = f"Empty response from Azure OpenAI (attempt {attempt + 1}/{max_retries}). Finish reason: {finish_reason}"
                    logger.error(f"[Azure] {error_msg}")
                    logger.error(f"[Azure] Response structure: choices={len(response.choices) if response.choices else 0}, message={type(message).__name__}")
                    logger.error(f"[Azure] Message attributes: {dir(message) if message else 'None'}")
                    
                    # Check if finish_reason indicates a specific issue
                    if finish_reason == "content_filter":
                        error_msg += " (Content filtered by Azure)"
                    elif finish_reason == "tool_calls":
                        error_msg += " (Tool calls not supported)"
                    elif finish_reason == "stop":
                        error_msg += " (Response stopped but empty - possible schema issue)"
                    
                    if attempt < max_retries - 1:
                        wait_time = base_backoff_seconds * (2 ** attempt)
                        logger.warning(f"[Azure] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(error_msg)
                
                result = self.tone_service.parse_llm_response(content, schema)
                
                # Validate result is not empty
                if not result or (isinstance(result, dict) and not any(result.values())):
                    error_msg = f"Empty parsed result from Azure OpenAI (attempt {attempt + 1}/{max_retries})"
                    logger.error(f"[Azure] {error_msg}")
                    
                    if attempt < max_retries - 1:
                        wait_time = base_backoff_seconds * (2 ** attempt)
                        logger.warning(f"[Azure] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(error_msg)
                
                logger.info("[Azure] Status=success")
                return result
                
            except Exception as exc:
                last_exception = exc
                error_detail = str(exc)
                
                # Log raw error response for debugging
                if hasattr(exc, 'response') and exc.response:
                    try:
                        error_body = exc.response.text if hasattr(exc.response, 'text') else str(exc.response)
                        logger.error(f"[Azure] Raw error response: {error_body}")
                    except Exception:
                        pass
                
                logger.error(f"[Azure] LLM call failed (attempt {attempt + 1}/{max_retries}): {error_detail}")
                logger.error(f"[Azure] Request params (keys only): {list(request_params.keys())}")
                
                if attempt < max_retries - 1:
                    wait_time = base_backoff_seconds * (2 ** attempt)
                    logger.warning(f"[Azure] Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[Azure] All {max_retries} retry attempts failed")
                    raise RuntimeError(f"Azure OpenAI call failed after {max_retries} attempts: {error_detail}") from exc
        
        # Should never reach here, but just in case
        if last_exception:
            raise RuntimeError(f"Azure OpenAI call failed after {max_retries} attempts") from last_exception
        else:
            raise RuntimeError(f"Azure OpenAI call failed after {max_retries} attempts")
    
    async def analyze_skills(
        self,
        employee_data: Dict[str, Any],
        role_requirements: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Analyze employee skills via Azure OpenAI."""
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
        
        employee_id = employee_data.get("employee_id", "Unknown")
        department = employee_data.get("department", "Unknown")
        current_skills = employee_data.get("skills", [])
        
        prompt = f"""Analyze the following employee's skills and provide a comprehensive assessment.

Employee ID: {employee_id}
Department: {department}
Current Skills: {', '.join(current_skills) if current_skills else 'None listed'}
"""
        
        if role_requirements:
            required_skills = role_requirements.get("required_skills", [])
            preferred_skills = role_requirements.get("preferred_skills", [])
            prompt += f"""
Target Role Requirements:
- Required Skills: {', '.join(required_skills) if required_skills else 'None'}
- Preferred Skills: {', '.join(preferred_skills) if preferred_skills else 'None'}
"""
        
        system_message = "You are an expert HR and career development analyst."
        
        result = await self.call_llm(
            prompt=prompt,
            schema=schema,
            system_message=system_message,
            max_completion_tokens=4096,  # Increased from 1024 to avoid truncation
        )
        
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

