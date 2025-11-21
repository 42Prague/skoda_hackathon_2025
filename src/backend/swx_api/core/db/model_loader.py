"""
SQLModel Loader
---------------

Provides a single function, ``load_all_models()``, that eagerly imports every
module defining ``SQLModel`` tables so Alembic and the runtime metadata stay in
sync.
"""

from __future__ import annotations

from importlib import import_module
import pkgutil
from typing import Iterable, List, Sequence, Set

from sqlmodel import SQLModel


# Central registry of modules that define SQLModel ``table=True`` classes.
DEFAULT_MODEL_MODULES: Sequence[str] = (
    "swx_api.app.models.skill_models",
    "swx_api.app.models.skoda_models",
)

MODEL_PACKAGES: Sequence[str] = (
    "swx_api.app.models",
    "swx_api.core.models",
)


def discover_model_modules(packages: Sequence[str] = MODEL_PACKAGES) -> List[str]:
    """
    Walk the configured packages and return every importable Python module.

    This provides future-proof auto-discovery when new model files are added.
    """

    discovered: Set[str] = set()
    for package_name in packages:
        try:
            package = import_module(package_name)
        except ModuleNotFoundError:
            continue

        discovered.add(package_name)

        package_path = getattr(package, "__path__", None)
        if not package_path:
            continue

        for module_info in pkgutil.walk_packages(package_path, f"{package_name}."):
            if module_info.ispkg:
                continue
            discovered.add(module_info.name)

    return sorted(discovered)


def load_all_models(extra_modules: Iterable[str] | None = None) -> List[str]:
    """
    Import every SQLModel module so metadata is populated for Alembic.

    Args:
        extra_modules: Optional iterable of dotted import paths to include.

    Returns:
        List of successfully imported module paths.

    Raises:
        ImportError: If any module cannot be imported.
        RuntimeError: If no SQLModel tables are registered after import.
    """

    modules_to_load = list(DEFAULT_MODEL_MODULES)
    modules_to_load.extend(discover_model_modules())
    if extra_modules:
        modules_to_load.extend(extra_modules)

    loaded_modules: List[str] = []
    for module_path in sorted(set(modules_to_load)):
        try:
            import_module(module_path)
        except ImportError as exc:  # pragma: no cover - fail fast
            raise ImportError(
                f"Failed to import '{module_path}' while loading SQLModel models."
            ) from exc
        else:
            loaded_modules.append(module_path)

    if not SQLModel.metadata.tables:
        raise RuntimeError(
            "No SQLModel tables were registered. "
            "Ensure model modules define classes with table=True."
        )

    return loaded_modules


