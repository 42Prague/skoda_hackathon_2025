"""
Minimal DomainRouter middleware placeholder.

The original project loads an optional middleware that can route requests
based on domain metadata. The open-source bundle we received does not
include that utility, yet the FastAPI application imports it
unconditionally. Without providing at least a stub implementation, any
attempt to import the app (for OpenAPI generation, tests, etc.) fails
with `ModuleNotFoundError`.

This lightweight middleware simply passes the ASGI scope through to the
wrapped application. It keeps the import path stable for the rest of the
stack while avoiding behavioural changes for the demo environment.
"""

from typing import Awaitable, Callable

ASGIApp = Callable[[dict, Callable[..., Awaitable[object]], Callable[..., Awaitable[object]]], Awaitable[None]]


class DomainRouterMiddleware:
    """Transparent middleware that proxies all requests to the inner app."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)

