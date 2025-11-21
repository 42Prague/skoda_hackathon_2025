import os
import sys
from logging.config import fileConfig
from pathlib import Path
from typing import Sequence

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from swx_api.core.config.settings import settings
from swx_api.core.db.model_loader import load_all_models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def ensure_models_registered() -> Sequence[str]:
    loaded_modules = load_all_models()
    if not loaded_modules:
        raise RuntimeError("No SQLModel modules were imported for Alembic.")
    if not SQLModel.metadata.tables:
        raise RuntimeError(
            "SQLModel metadata is empty after loading modules. "
            "Check that your model classes declare table=True."
        )
    return loaded_modules


def get_url() -> str:
    override = os.getenv("ALEMBIC_DATABASE_URI")
    if override:
        return override
    return str(settings.SQLALCHEMY_DATABASE_URI)


def run_migrations_offline() -> None:
    ensure_models_registered()
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    ensure_models_registered()
    configuration = config.get_section(config.config_ini_section).copy()
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

