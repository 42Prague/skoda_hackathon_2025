#!/usr/bin/env python3
"""
Backend runtime smoke test.

Validates that the production image can talk to the database, run Alembic,
import every router/dependency module, boot gunicorn+uvicorn, and answer
HTTP health checks. Exits with a non-zero status on the first failure.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import List

import httpx
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
DEFAULT_SERVER_PORT = int(os.getenv("SMOKE_TEST_PORT", "8765"))

sys.path.insert(0, str(PROJECT_ROOT))

from swx_api.core.config.settings import settings  # noqa: E402
from swx_api.core.db.model_loader import load_all_models  # noqa: E402


def require_path(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{description} not found at {path}")


async def verify_database_connection() -> None:
    engine = create_async_engine(settings.SQLALCHEMY_ASYNC_DATABASE_URI, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    finally:
        await engine.dispose()


def ensure_models_loaded() -> List[str]:
    loaded = load_all_models()
    if not SQLModel.metadata.tables:
        raise RuntimeError("SQLModel metadata is empty after loading models.")
    return loaded


def run_alembic_upgrade() -> None:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.SQLALCHEMY_DATABASE_URI)
    command.upgrade(cfg, "head")


def import_package_modules(package_name: str) -> List[str]:
    import importlib
    import pkgutil

    package = importlib.import_module(package_name)
    imported = [package_name]

    package_path = getattr(package, "__path__", None)
    if not package_path:
        return imported

    for module_info in pkgutil.walk_packages(package_path, f"{package_name}."):
        module = importlib.import_module(module_info.name)
        imported.append(module.__name__)

    return imported


def verify_router_imports() -> List[str]:
    return import_package_modules("swx_api.app.routes")


def verify_dependency_modules() -> List[str]:
    imported: List[str] = []
    for module_name in (
        "swx_api.app.utils.dependencies",
        "swx_api.core.router",
    ):
        imported.extend(import_package_modules(module_name))
    return imported


async def verify_http_health(gunicorn_port: int = DEFAULT_SERVER_PORT) -> None:
    cmd = [
        "gunicorn",
        "swx_api.core.main:app",
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "--bind",
        f"127.0.0.1:{gunicorn_port}",
        "--workers",
        "1",
        "--threads",
        "1",
        "--timeout",
        "60",
        "--log-level",
        "info",
    ]

    env = os.environ.copy()
    env.setdefault("PORT", str(gunicorn_port))
    env.setdefault("PYTHONPATH", str(PROJECT_ROOT))

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )

    try:
        async with httpx.AsyncClient(base_url=f"http://127.0.0.1:{gunicorn_port}", timeout=5.0) as client:
            for _ in range(30):
                if process.poll() is not None:
                    raise RuntimeError("Gunicorn terminated before serving /healthz.")
                try:
                    response = await client.get("/healthz")
                    if response.status_code == 200:
                        return
                except httpx.HTTPError:
                    await asyncio.sleep(1)
                else:
                    await asyncio.sleep(1)
            raise RuntimeError("Health check never succeeded within timeout.")
    finally:
        with contextlib.suppress(ProcessLookupError):
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


async def main() -> None:
    require_path(PROJECT_ROOT / "swx_api", "swx_api package")
    require_path(PROJECT_ROOT / "migrations", "migrations directory")
    require_path(ALEMBIC_INI, "alembic.ini")

    await verify_database_connection()
    ensure_models_loaded()
    verify_router_imports()
    verify_dependency_modules()
    run_alembic_upgrade()
    await verify_http_health()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:  # pragma: no cover - fail fast
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)

