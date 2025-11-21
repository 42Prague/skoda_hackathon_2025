#!/usr/bin/env python3
"""
Recursive import audit to guarantee every runtime module can be imported inside Docker.

The audit covers:
  - All packages under ``swx_api`` (including routers, models, services, etc.)
  - Every module that contains ``routes`` or ``dependencies`` in its path
  - All settings/config modules
  - Every Alembic revision inside ``migrations.versions``

If any import fails, the script exits with code 1 and reports the failing module.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class AuditResult:
    imported: List[str]
    failures: List[str]


def module_exists(dotted_path: str) -> bool:
    try:
        importlib.import_module(dotted_path)
    except ModuleNotFoundError:
        return False
    else:
        return True


def walk_modules(root_package: str) -> Set[str]:
    """
    Returns every dotted module path found under ``root_package``.
    """

    discovered: Set[str] = set()
    try:
        package = importlib.import_module(root_package)
    except ModuleNotFoundError as exc:
        raise RuntimeError(f"Required package '{root_package}' is missing.") from exc

    discovered.add(package.__name__)

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return discovered

    for module_info in pkgutil.walk_packages(package_path, f"{package.__name__}."):
        discovered.add(module_info.name)

    return discovered


def import_modules(modules: Iterable[str]) -> AuditResult:
    imported: List[str] = []
    failures: List[str] = []

    for module_name in sorted(set(modules)):
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # pragma: no cover
            failures.append(f"{module_name}: {exc}")
        else:
            imported.append(module_name)

    return AuditResult(imported=imported, failures=failures)


def collect_targets() -> Set[str]:
    targets: Set[str] = set()

    targets.update(walk_modules("swx_api"))
    if module_exists("migrations"):
        targets.update(walk_modules("migrations"))
    if module_exists("migrations.versions"):
        targets.update(walk_modules("migrations.versions"))

    return targets


def enforce_subset(modules: Iterable[str], needle: str, description: str) -> None:
    matches = [name for name in modules if needle in name]
    if not matches:
        raise RuntimeError(f"No modules matching '{needle}' were found for {description}.")


def main() -> None:
    modules = collect_targets()
    result = import_modules(modules)

    enforce_subset(result.imported, ".routes", "router imports")
    enforce_subset(result.imported, "dependencies", "dependency providers")
    enforce_subset(result.imported, "config.settings", "settings modules")
    enforce_subset(result.imported, ".models", "SQLModel modules")
    enforce_subset(result.imported, "migrations.versions", "Alembic revisions")

    if result.failures:
        failed = "\n".join(result.failures)
        raise SystemExit(f"Import audit failed:\n{failed}")

    print(f"Import audit succeeded for {len(result.imported)} modules.")


if __name__ == "__main__":
    main()

