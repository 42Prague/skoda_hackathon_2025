# Rate Limiting Middleware

import time
from typing import Dict
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self, app, calls_per_minute: int = 60, calls_per_day: int = 1000):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.calls_per_day = calls_per_day
        
        # In-memory storage: {identifier: {minute: count, day: count, last_reset_minute: timestamp, last_reset_day: timestamp}}
        self.request_counts: Dict[str, Dict] = defaultdict(lambda: {
            "minute": 0,
            "day": 0,
            "last_reset_minute": time.time(),
            "last_reset_day": time.time()
        })
    
    def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        Uses API key if present, otherwise IP address.
        """
        # Check for API key in header
        api_key = request.headers.get("X-API-Key") or request.headers.get("Authorization", "").replace("Bearer ", "")
        if api_key:
            return f"key:{api_key[:16]}"  # Use first 16 chars for privacy
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _reset_if_needed(self, identifier: str):
        """Reset counters if time windows have passed"""
        current_time = time.time()
        data = self.request_counts[identifier]
        
        # Reset minute counter (60 seconds)
        if current_time - data["last_reset_minute"] >= 60:
            data["minute"] = 0
            data["last_reset_minute"] = current_time
        
        # Reset day counter (86400 seconds = 24 hours)
        if current_time - data["last_reset_day"] >= 86400:
            data["day"] = 0
            data["last_reset_day"] = current_time
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for certain paths
        exempt_paths = ["/healthz", "/", "/docs", "/openapi.json", "/redoc"]
        if request.url.path in exempt_paths or request.url.path.startswith("/.well-known"):
            return await call_next(request)
        
        # Get identifier and reset counters if needed
        identifier = self._get_identifier(request)
        self._reset_if_needed(identifier)
        
        # Get current counts
        data = self.request_counts[identifier]
        minute_count = data["minute"]
        day_count = data["day"]
        
        # Check limits
        if minute_count >= self.calls_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Maximum {self.calls_per_minute} requests per minute. Try again in {60 - int(time.time() - data['last_reset_minute'])} seconds.",
                    "limit_type": "per_minute",
                    "limit": self.calls_per_minute
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(data["last_reset_minute"] + 60)),
                    "Retry-After": str(60 - int(time.time() - data["last_reset_minute"]))
                }
            )
        
        if day_count >= self.calls_per_day:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Daily rate limit exceeded",
                    "detail": f"Maximum {self.calls_per_day} requests per day. Resets at midnight UTC.",
                    "limit_type": "per_day",
                    "limit": self.calls_per_day
                },
                headers={
                    "X-RateLimit-Limit": str(self.calls_per_day),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(data["last_reset_day"] + 86400))
                }
            )
        
        # Increment counters
        data["minute"] += 1
        data["day"] += 1
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit-Minute"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(self.calls_per_minute - minute_count - 1)
        response.headers["X-RateLimit-Limit-Day"] = str(self.calls_per_day)
        response.headers["X-RateLimit-Remaining-Day"] = str(self.calls_per_day - day_count - 1)
        
        return response

