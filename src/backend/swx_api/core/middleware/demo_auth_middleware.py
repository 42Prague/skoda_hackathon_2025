"""
Demo-level bearer token middleware for MVP hardening.
"""

from __future__ import annotations

import os
from typing import Iterable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


UNPROTECTED_PATHS: Iterable[str] = {"/", "/healthz", "/docs", "/redoc", "/openapi.json", "/api/openapi.json"}


class DemoTokenMiddleware(BaseHTTPMiddleware):
    """Simple Bearer token check sourced from DEMO_API_TOKEN."""

    def __init__(self, app):
        super().__init__(app)
        self.expected_token = os.getenv("DEMO_API_TOKEN")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if (path in UNPROTECTED_PATHS 
            or path.startswith("/.well-known")
            or path.endswith("/openapi.json")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        token = auth_header.split("Bearer ", 1)[1].strip() if auth_header.startswith("Bearer ") else None

        if not self.expected_token:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "DEMO_API_TOKEN not configured"},
            )

        if token != self.expected_token:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Invalid bearer token"},
            )

        return await call_next(request)


def apply_middleware(app):
    """Hook for dynamic middleware loader."""
    # AUTHENTICATION DISABLED FOR DEVELOPMENT/TESTING
    # Uncomment the line below to enable authentication
    # app.add_middleware(DemoTokenMiddleware)

