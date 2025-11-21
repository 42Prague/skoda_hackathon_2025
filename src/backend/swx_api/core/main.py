import os
from contextlib import asynccontextmanager

try:
    import ngrok
except ImportError:
    ngrok = None

import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk import capture_exception
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException

from swx_api.app.config.settings import app_settings
from swx_api.core.background_task import start_cache_refresh
from swx_api.core.config.settings import settings
from swx_api.core.middleware.logging_middleware import logger
from swx_api.core.router import router
from swx_api.core.utils.domain_router import DomainRouterMiddleware
from swx_api.core.utils.loader import load_middleware

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.2,
    environment=settings.ENVIRONMENT,
    release=f"swx-api@{app_settings.PROJECT_VERSION}",
    send_default_pii=True
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Validate environment variables at startup
    from swx_api.app.utils.env_validator import validate_environment
    validate_environment()
    
    # Log AI provider configuration
    from swx_api.app.services.llm_client import LLMConfig
    llm_config = LLMConfig.from_env()
    logger.info(f"[AI] Provider={llm_config.provider} Model={llm_config.model} Endpoint={llm_config.endpoint or 'N/A'}")
    
    start_cache_refresh()
    if app_settings.USE_NGROK and app_settings.NGROK_AUTH_TOKEN and ngrok:
        logger.info("Starting ngrok tunnel...")
        try:
            ngrok.set_auth_token(app_settings.NGROK_AUTH_TOKEN)
            listener = await ngrok.forward(app_settings.APP_PORT)
            app.state.public_url = listener.url()
            logger.info(f"🔗 NGROK Tunnel ready: {app.state.public_url}")
        except Exception as e:
            logger.error(f"Ngrok tunnel error: {e}")
    elif app_settings.USE_NGROK and not ngrok:
        logger.warning("USE_NGROK is enabled but ngrok module is not installed. Install with: pip install ngrok")
    yield
    if app_settings.USE_NGROK and ngrok:
        try:
            ngrok.disconnect()
            logger.info("Ngrok tunnel closed.")
        except Exception as e:
            logger.warning(f"Ngrok shutdown failed: {e}")
    logger.info("Shutdown complete.")


#  Initialize FastAPI app
app = FastAPI(
    title=app_settings.PROJECT_NAME,
    version=app_settings.PROJECT_VERSION,
    openapi_url=f"{settings.ROUTE_PREFIX}/openapi.json",
    lifespan=lifespan,
)


#  Exception handlers
def create_error_response(
    error_type: str,
    message: str,
    details: dict = None,
    status_code: int = 500
) -> JSONResponse:
    """Create a unified error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error_type,
            "detail": message,
            "details": details or {},
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc):
    error_type = "NotFound" if exc.status_code == 404 else "InternalError"
    return create_error_response(
        error_type=error_type,
        message=str(exc.detail) if exc.detail else "An error occurred",
        status_code=exc.status_code
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return create_error_response(
        error_type="ValidationError",
        message="Request validation failed",
        details={"fields": jsonable_encoder(exc.errors())},
        status_code=422
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    capture_exception(exc)
    return create_error_response(
        error_type="InternalError",
        message="An internal server error occurred",
        details={"detail": str(exc)} if settings.ENVIRONMENT == "local" else {},
        status_code=500
    )


#  Load global middleware
load_middleware(app)

#  Register all API routes
app.include_router(router)


#  Root route
@app.get("/")
def read_root(request: Request):
    return {
        "message": "Welcome to ŠKODA AI Skill Coach API 🚀",
        "version": app_settings.PROJECT_VERSION,
        "ngrok_url": getattr(request.app.state, "public_url", None) if app_settings.USE_NGROK else None,
    }


#  Optional health check endpoint
@app.get("/healthz", include_in_schema=False)
def health_check():
    return {"status": "ok"}

@app.get("/sentry-test")
def sentry_test():
    1 / 0  # 🔥 This will raise a ZeroDivisionError

# MCP tools removed - Skill Coach only

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # go up from swx_api/core
# Use absolute path for .well-known directory
well_known_path = "/app/.well-known" if os.path.exists("/app/.well-known") else os.path.join(BASE_DIR, ".well-known")

# Mount .well-known with public access (no trailing slash important!)
if os.path.exists(well_known_path):
    app.mount("/.well-known", StaticFiles(directory=well_known_path), name="well-known")
    logger.info(f"✅ Mounted .well-known from: {well_known_path}")
else:
    logger.warning(f"⚠️  .well-known directory not found at: {well_known_path}")

# Mount uploads directory for static file serving
uploads_path = os.path.join(BASE_DIR, "uploads")
os.makedirs(uploads_path, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

# 🔐 Wrap app with Sentry middleware
app = SentryAsgiMiddleware(app)

#  Apply final domain-based middleware wrapping
app = DomainRouterMiddleware(app)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description="ŠKODA AI Skill Coach API",
    )
    security_schemes = openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    # Authentication disabled for development/testing
    # Uncomment below to enable authentication in OpenAPI schema
    # security_schemes["DemoToken"] = {
    #     "type": "http",
    #     "scheme": "bearer",
    #     "bearerFormat": "Token",
    #     "description": "Demo bearer token defined by DEMO_API_TOKEN",
    # }
    # openapi_schema["security"] = [{"DemoToken": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
