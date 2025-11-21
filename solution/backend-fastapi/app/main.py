from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from fastapi.openapi.docs import get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html
# Import routes
from app.routes import health, chatbot, documents, analytics, auth, db_utils

# Import initialization modules
from app.core.database import init_database, sync_db_to_minio
from app.core.storage import init_buckets
from app.core.vector_store import init_collections

app = FastAPI(title="Škoda Chatbot API", version="1.0.0")

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize databases and storage on startup"""
    try:
        # Initialize buckets first (needed for DB sync)
        init_buckets()
        # Initialize database (will sync from MinIO)
        init_database()
        # Initialize vector store collections
        init_collections()
        print("All systems initialized successfully")
    except Exception as e:
        print(f"Warning: Initialization error: {e}")

# Sync database to MinIO on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Sync DuckDB to MinIO on shutdown"""
    try:
        sync_db_to_minio()
        print("Database synced to MinIO on shutdown")
    except Exception as e:
        print(f"Warning: Could not sync database to MinIO on shutdown: {e}")
# Custom Swagger UI route
@app.get("/swagger", include_in_schema=False)
async def swagger_ui_html():
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=f"{app.title} - Swagger UI")

# OAuth2 redirect used by the swagger UI if needed
@app.get("/swagger/oauth2-redirect", include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()

# Optional Redoc
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    from fastapi.openapi.docs import get_redoc_html
    return get_redoc_html(openapi_url=app.openapi_url, title=f"{app.title} - ReDoc")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(chatbot.router)
app.include_router(documents.router)
app.include_router(auth.router)
app.include_router(db_utils.router)
app.include_router(analytics.router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
