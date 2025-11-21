"""
Async Audit Log System
---------------------
Logs every ingestion, AI call, DB write, and error.
Stores logs in PostgreSQL (via repository) and JSONL files (async).
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles

from swx_api.app.repositories.audit_repository import AuditRepository
from swx_api.app.models.skill_models import AuditLog
from swx_api.app.services.ingestion_service import paths
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("audit")


class AuditService:
    """Async service for comprehensive audit logging."""
    
    def __init__(self, audit_repo: Optional[AuditRepository] = None):
        """
        Initialize audit service with repository.
        
        Args:
            audit_repo: Audit repository instance (optional)
        """
        self.audit_repo = audit_repo
        self.logs_dir = paths.logs_dir
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.audit_file = self.logs_dir / "audit.jsonl"
    
    async def log_ingestion(
        self,
        session: AsyncSession,
        dataset_id: str,
        filename: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log data ingestion event."""
        log_entry = {
            "event_type": "ingestion",
            "dataset_id": dataset_id,
            "filename": filename,
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._write_audit_log_async(log_entry)
        if session and self.audit_repo:
            await self._save_to_db(session, "ingestion", "ingestion_service", log_entry)
    
    async def log_ai_call(
        self,
        prompt_name_or_session: Optional[Union[str, AsyncSession]] = None,
        variables_or_service_name: Optional[Union[Dict[str, Any], str]] = None,
        response_or_model: Optional[Union[Dict[str, Any], str]] = None,
        success: bool = True,
        error: Optional[str] = None,
        session: Optional[AsyncSession] = None,
        service_name: str = "ai_orchestrator",
        model: Optional[str] = None,
        prompt_length: Optional[int] = None,
        response_length: Optional[int] = None,
    ) -> None:
        """
        Log AI/LLM API call from orchestrator (supports multiple calling patterns).
        
        Can be called with:
        - (session, service_name, model, prompt_length, response_length, success) - route style
        - (prompt_name, variables, response, success, ...) - orchestrator style
        """
        # Detect calling pattern based on first argument type or presence of session kwarg
        if session is not None or isinstance(prompt_name_or_session, AsyncSession):
            # Route-style calling: (session, service_name, model, ...)
            if isinstance(prompt_name_or_session, AsyncSession):
                session = prompt_name_or_session
            if isinstance(variables_or_service_name, str):
                service_name = variables_or_service_name
            if isinstance(response_or_model, str):
                model = response_or_model
            prompt_name = None
            variables = None
            response = None
        else:
            # Orchestrator-style calling: (prompt_name, variables, response, success, ...)
            prompt_name = prompt_name_or_session
            variables = variables_or_service_name if isinstance(variables_or_service_name, dict) else None
            response = response_or_model if isinstance(response_or_model, dict) else None
        
        # Support route-style calling: (session, service_name, model, ...)
        if prompt_name is None and variables is None and response is None:
            log_entry = {
                "event_type": "ai_call",
                "service_name": service_name,
                "prompt_name": "unknown",
                "variables_keys": [],
                "response_keys": [],
                "success": success,
                "error": error,
                "ai_mode": "unknown",
                "metadata": {
                    "model": model,
                    "prompt_length": prompt_length,
                    "response_length": response_length,
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            # Orchestrator-style calling: (prompt_name, variables, response, success, ...)
            log_entry = {
                "event_type": "ai_call",
                "service_name": service_name,
                "prompt_name": prompt_name or "unknown",
                "variables_keys": list(variables.keys()) if variables else [],
                "response_keys": list(response.keys()) if response else [],
                "success": success,
                "error": error,
                "ai_mode": response.get("ai_mode", "unknown") if response else "unknown",
                "metadata": {
                    "detected_language": response.get("detected_language", "en") if response else "en",
                    "response_size": len(str(response)) if response else 0,
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        await self._write_audit_log_async(log_entry)
        if session and self.audit_repo:
            await self._save_to_db(session, "ai_call", service_name, log_entry)
    
    async def log_db_write(
        self,
        session: AsyncSession,
        table_name: str,
        operation: str,
        record_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log database write operation."""
        log_entry = {
            "event_type": "db_write",
            "table_name": table_name,
            "operation": operation,  # "insert", "update", "delete"
            "record_id": record_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._write_audit_log_async(log_entry)
        if session and self.audit_repo:
            await self._save_to_db(session, "db_write", None, log_entry)
    
    async def log_error(
        self,
        session: AsyncSession,
        error_type: str,
        error_message: str,
        service_name: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error event."""
        log_entry = {
            "event_type": "error",
            "error_type": error_type,
            "error_message": error_message,
            "service_name": service_name,
            "stack_trace": stack_trace,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._write_audit_log_async(log_entry)
        if session and self.audit_repo:
            await self._save_to_db(session, "error", service_name, log_entry, success=False)
    
    async def log_api_call(
        self,
        session: AsyncSession,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log API call."""
        log_entry = {
            "event_type": "api_call",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self._write_audit_log_async(log_entry)
        if session and self.audit_repo:
            await self._save_to_db(session, "api_call", None, log_entry, success=(status_code < 400))
    
    async def _write_audit_log_async(self, log_entry: Dict[str, Any]) -> None:
        """Write audit log entry to JSONL file asynchronously."""
        try:
            async with aiofiles.open(self.audit_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}", exc_info=True)
    
    async def _save_to_db(
        self,
        session: AsyncSession,
        event_type: str,
        service_name: Optional[str],
        event_data: Dict[str, Any],
        success: bool = True
    ) -> None:
        """Save audit log to database using repository."""
        if not self.audit_repo:
            return
        try:
            audit_record = AuditLog(
                event_type=event_type,
                service_name=service_name,
                event_data=event_data,
                success=success,
            )
            await self.audit_repo.create(session, audit_record)
        except Exception as e:
            logger.warning(f"Failed to save audit log to DB: {e}")
            # Don't fail if DB save fails, file logging is primary
    
    async def get_audit_logs(
        self,
        session: AsyncSession,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """Read audit logs from database."""
        try:
            if event_type:
                logs = await self.audit_repo.get_by_event_type(session, event_type, limit=limit)
            else:
                logs = await self.audit_repo.get_all_logs(session, limit=limit)
            
            return [
                {
                    "id": str(log.id),
                    "event_type": log.event_type,
                    "service_name": log.service_name,
                    "event_data": log.event_data,
                    "success": log.success,
                    "created_at": log.created_at.isoformat(),
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Failed to read audit logs: {e}", exc_info=True)
            return []
