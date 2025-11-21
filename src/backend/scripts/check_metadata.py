#!/usr/bin/env python3
"""
Metadata validation script for SQLModel + Alembic integration.

This script ensures:
  * All SQLModel tables are registered and unique
  * No duplicate table names exist between app/core models
  * Alembic autogenerate runs cleanly against a temporary SQLite database

The script should run inside Docker after dependencies are installed.
"""

from __future__ import annotations

import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import Dict, List, Set, Type

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlmodel import SQLModel

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from swx_api.core.config.settings import settings  # noqa: E402
from swx_api.core.db.model_loader import load_all_models  # noqa: E402


def iter_sqlmodel_classes() -> List[Type[SQLModel]]:
    collected: Set[Type[SQLModel]] = set()
    stack = list(SQLModel.__subclasses__())

    while stack:
        cls = stack.pop()
        if cls in collected:
            continue
        collected.add(cls)
        stack.extend(cls.__subclasses__())

    return [cls for cls in collected if cls.__module__.startswith("swx_api.")]


def ensure_tables_registered() -> Dict[str, List[Type[SQLModel]]]:
    load_all_models()
    if not SQLModel.metadata.tables:
        raise RuntimeError("SQLModel.metadata.tables is empty.")

    table_map: Dict[str, List[Type[SQLModel]]] = {}
    for cls in iter_sqlmodel_classes():
        table_name = getattr(cls, "__tablename__", None)
        if table_name:
            table_map.setdefault(table_name, []).append(cls)
        elif getattr(cls, "__table__", None) is not None:
            table_map.setdefault(cls.__table__.name, []).append(cls)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(f"{cls.__module__}.{cls.__name__} is missing table=True or __tablename__.")

    metadata_tables = set(SQLModel.metadata.tables.keys())
    if metadata_tables != set(table_map.keys()):
        diff_missing = metadata_tables - set(table_map.keys())
        diff_extra = set(table_map.keys()) - metadata_tables
        raise RuntimeError(
            f"Metadata/model mismatch. Missing in model map: {diff_missing}; extra in model map: {diff_extra}"
        )

    for table_name, classes in table_map.items():
        if len(classes) > 1:
            modules = {cls.__module__ for cls in classes}
            raise RuntimeError(
                f"Duplicate table '{table_name}' declared in modules: {modules}"
            )

        module = classes[0].__module__
        if module.startswith("swx_api.app.models") and table_name in SQLModel.metadata.tables:
            continue
        if module.startswith("swx_api.core.models") and table_name in SQLModel.metadata.tables:
            continue

    return table_map


def run_alembic_autogen_smoke() -> None:
    table_map = ensure_tables_registered()

    with tempfile.TemporaryDirectory() as tmpdir:
        sqlite_path = Path(tmpdir) / "metadata_check.db"
        engine = create_engine(f"sqlite:///{sqlite_path}")
        SQLModel.metadata.create_all(engine)
        engine.dispose()

        previous_override = os.environ.get("ALEMBIC_DATABASE_URI")
        os.environ["ALEMBIC_DATABASE_URI"] = f"sqlite:///{sqlite_path}"

        cfg = Config(str(ALEMBIC_INI))

        try:
            with warnings.catch_warnings(record=True) as caught_warnings:
                command.revision(
                    cfg,
                    message="tmp_metadata_check",
                    autogenerate=True,
                    head="head",
                    version_path=tmpdir,
                )

                if caught_warnings:
                    raise RuntimeError(
                        "Warnings emitted during Alembic autogenerate: "
                        + ", ".join(str(warning.message) for warning in caught_warnings)
                    )

                created_files = list(Path(tmpdir).glob("*.py"))
                for file_path in created_files:
                    text = file_path.read_text()
                    if "op." in text or "sa." in text:
                        raise RuntimeError(
                            f"Alembic autogenerate produced statements in {file_path}. "
                            "Run scripts/check_schema_diff.sh to reconcile schema differences."
                        )
        finally:
            if previous_override is not None:
                os.environ["ALEMBIC_DATABASE_URI"] = previous_override
            else:
                os.environ.pop("ALEMBIC_DATABASE_URI", None)


def main() -> None:
    table_map = ensure_tables_registered()
    print(f"Validated {len(table_map)} SQLModel tables.")
    run_alembic_autogen_smoke()
    print("Alembic autogenerate smoke-check succeeded.")


if __name__ == "__main__":
    main()

