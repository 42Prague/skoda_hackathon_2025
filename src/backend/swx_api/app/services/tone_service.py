"""
TONE Service - Token-Optimized Notation Engine Integration
----------------------------------------------------------
Handles TONE format encoding/decoding for LLM interactions to save tokens.
"""

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from tone import encode as tone_encode, decode as tone_decode
    TONE_AVAILABLE = True
except ImportError:
    TONE_AVAILABLE = False
    logging.warning("toneformat package not installed. TONE features disabled.")

from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("tone_service")

# Validation logs directory (defaults to repo_root/data/logs/validation)
_services_dir = Path(__file__).resolve().parent
_backend_dir = _services_dir.parents[2]
_repo_root = _backend_dir.parent
DATA_ROOT = Path(os.getenv("SKODA_DATA_ROOT", _repo_root / "data")).resolve()
_logged_validation_dir_failures: set[str] = set()


def _resolve_validation_log_dir() -> Path:
    """Determine a writable validation log directory with graceful fallbacks."""
    candidate_dirs = []

    override_dir = os.getenv("SKODA_VALIDATION_LOG_DIR")
    if override_dir:
        candidate_dirs.append(Path(override_dir))

    candidate_dirs.extend([
        Path(os.getenv("SKODA_DATA_ROOT", DATA_ROOT)) / "logs" / "validation",
        _repo_root / "data" / "logs" / "validation",
        Path.cwd() / "data" / "logs" / "validation",
        Path(tempfile.gettempdir()) / "skoda_validation_logs",
    ])

    for path in candidate_dirs:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path
        except PermissionError as exc:
            path_str = str(path)
            if path_str not in _logged_validation_dir_failures:
                logger.warning(f"Validation log dir not writable ({path}): {exc}")
                _logged_validation_dir_failures.add(path_str)
        except OSError as exc:
            path_str = str(path)
            if path_str not in _logged_validation_dir_failures:
                logger.warning(f"Failed to create validation log dir ({path}): {exc}")
                _logged_validation_dir_failures.add(path_str)

    # As a last resort, use a TemporaryDirectory-style path
    fallback = Path(tempfile.mkdtemp(prefix="skoda_validation_"))
    logger.warning(f"Using temporary validation log directory at {fallback}")
    return fallback


VALIDATION_LOG_DIR = _resolve_validation_log_dir()


class TONEService:
    """Service for TONE format encoding/decoding and validation."""
    
    def __init__(self):
        self.use_tone = os.getenv("USE_TONE", "false").lower() == "true"
        self.validation_mode = os.getenv("VALIDATION_MODE", "false").lower() == "true"
        self.tone_available = TONE_AVAILABLE
        
        if self.use_tone and not self.tone_available:
            logger.warning("USE_TONE=true but toneformat package not installed. Falling back to JSON.")
            self.use_tone = False
    
    def build_tone_prompt(
        self,
        base_prompt: str,
        schema: Dict[str, Any],
        example_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build a TONE-formatted prompt with schema.
        
        Args:
            base_prompt: The base prompt text
            schema: Expected response schema
            example_data: Optional example data in TONE format
            
        Returns:
            Enhanced prompt with TONE instructions
        """
        if not self.use_tone:
            return base_prompt
        
        tone_instructions = """
IMPORTANT: Respond using TONE format (Token-Optimized Notation Engine) to save tokens.

TONE Format Guidelines:
- Use tabular arrays for uniform data: items[2]{id,name,value}:
  1,Item1,100
  2,Item2,200
- Use objects for nested data: user:
  id: 123
  name: John
- Use inline arrays for simple lists: tags[3]: tag1,tag2,tag3
- Minimize punctuation and whitespace
- Declare keys once, stream data as rows

Expected Response Schema:
"""
        
        # Add schema description
        schema_desc = self._describe_schema(schema)
        tone_instructions += schema_desc
        
        if example_data:
            try:
                example_tone = tone_encode(example_data)
                tone_instructions += f"\n\nExample TONE Response:\n{example_tone}\n"
            except Exception as e:
                logger.warning(f"Failed to encode example as TONE: {e}")
        
        tone_instructions += "\n\nRespond ONLY with valid TONE format. Do not include markdown code blocks or explanations."
        
        return base_prompt + "\n\n" + tone_instructions
    
    def parse_llm_response(
        self,
        response_text: str,
        expected_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Parse LLM response, attempting TONE first, then JSON fallback.
        
        Args:
            response_text: Raw response from LLM
            expected_schema: Expected response schema for validation
            
        Returns:
            Parsed Python dictionary
        """
        # Clean response text
        cleaned = self._clean_response_text(response_text)
        
        # Try TONE parsing first if enabled
        if self.use_tone:
            try:
                result = tone_decode(cleaned)
                if self.validation_mode:
                    result = self._validate_and_fix(result, expected_schema)
                return result
            except Exception as e:
                logger.warning(f"TONE parsing failed, trying JSON fallback: {e}")
        
        # Fallback to JSON
        try:
            result = json.loads(cleaned)
            if self.validation_mode:
                result = self._validate_and_fix(result, expected_schema)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing also failed: {e}")
            # Last resort: return safe default
            return self._create_safe_default(expected_schema)
    
    def encode_to_tone(self, data: Dict[str, Any]) -> str:
        """Encode Python dict to TONE format."""
        if not self.tone_available:
            return json.dumps(data, indent=2)
        
        try:
            return tone_encode(data)
        except Exception as e:
            logger.warning(f"TONE encoding failed, using JSON: {e}")
            return json.dumps(data, indent=2)
    
    def decode_from_tone(self, tone_text: str) -> Dict[str, Any]:
        """Decode TONE format to Python dict."""
        if not self.tone_available:
            return json.loads(tone_text)
        
        try:
            return tone_decode(tone_text)
        except Exception as e:
            logger.warning(f"TONE decoding failed, trying JSON: {e}")
            return json.loads(tone_text)
    
    def _clean_response_text(self, text: str) -> str:
        """Clean LLM response text (remove markdown, code blocks, etc.)."""
        # Remove markdown code blocks
        if "```" in text:
            # Extract content between code blocks
            parts = text.split("```")
            if len(parts) >= 3:
                # Take the middle part (the code)
                text = parts[1]
                # Remove language identifier if present
                if "\n" in text:
                    lines = text.split("\n")
                    if lines[0].strip() in ["tone", "json", "TONE", "JSON"]:
                        text = "\n".join(lines[1:])
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common prefixes
        prefixes = ["Response:", "Output:", "Result:", "Answer:"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        return text
    
    def _describe_schema(self, schema: Dict[str, Any]) -> str:
        """Describe schema in human-readable format."""
        if not schema:
            return "No specific schema required."
        
        description = "{\n"
        for key, value_type in schema.items():
            if isinstance(value_type, dict):
                description += f"  {key}: object with fields {list(value_type.keys())}\n"
            elif isinstance(value_type, list):
                description += f"  {key}: array of {value_type[0] if value_type else 'any'}\n"
            else:
                description += f"  {key}: {value_type}\n"
        description += "}"
        
        return description
    
    def _validate_and_fix(
        self,
        data: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validate data against schema and fix missing fields.
        
        Args:
            data: Parsed data to validate
            schema: Expected schema
            
        Returns:
            Validated and fixed data
        """
        if not schema:
            return data
        
        fixed_data = data.copy()
        missing_fields = []
        
        for key, expected_type in schema.items():
            if key not in fixed_data:
                # Add safe default
                if expected_type is list or expected_type == list:
                    fixed_data[key] = []
                elif expected_type is dict or expected_type == dict:
                    fixed_data[key] = {}
                elif expected_type == int:
                    fixed_data[key] = 0
                elif expected_type == float:
                    fixed_data[key] = 0.0
                elif expected_type == bool:
                    fixed_data[key] = False
                else:
                    fixed_data[key] = ""
                
                missing_fields.append(key)
        
        # Log validation results
        if missing_fields or self.validation_mode:
            self._log_validation(data, fixed_data, missing_fields, schema)
        
        return fixed_data
    
    def _create_safe_default(self, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create safe default response when parsing fails."""
        if not schema:
            return {
                "error": "Failed to parse response",
                "success": False
            }
        
        default = {}
        for key, value_type in schema.items():
            if value_type is list or value_type == list:
                default[key] = []
            elif value_type is dict or value_type == dict:
                default[key] = {}
            elif value_type == int:
                default[key] = 0
            elif value_type == float:
                default[key] = 0.0
            elif value_type == bool:
                default[key] = False
            else:
                default[key] = ""
        
        default["error"] = "Failed to parse response, using defaults"
        return default
    
    def _log_validation(
        self,
        original: Dict[str, Any],
        fixed: Dict[str, Any],
        missing_fields: List[str],
        schema: Optional[Dict[str, Any]]
    ) -> None:
        """Log validation results to file."""
        if not self.validation_mode:
            return
        
        try:
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat()
            
            log_entry = {
                "timestamp": timestamp,
                "missing_fields": missing_fields,
                "original_keys": list(original.keys()),
                "fixed_keys": list(fixed.keys()),
                "schema_keys": list(schema.keys()) if schema else []
            }
            
            log_file = VALIDATION_LOG_DIR / f"validation_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
            # File I/O for logging (async)
            try:
                import aiofiles
                async def _write_log():
                    async with aiofiles.open(log_file, "a", encoding="utf-8") as f:
                        await f.write(json.dumps(log_entry) + "\n")
                # Run in background if event loop exists
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(_write_log())
                    else:
                        loop.run_until_complete(_write_log())
                except RuntimeError:
                    # No event loop, use sync fallback
                    with log_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(log_entry) + "\n")
            except ImportError:
                # Fallback to sync if aiofiles not available
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to log validation: {e}")


# Global instance
_tone_service: Optional[TONEService] = None


def get_tone_service() -> TONEService:
    """Get global TONE service instance."""
    global _tone_service
    if _tone_service is None:
        _tone_service = TONEService()
    return _tone_service

