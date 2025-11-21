import sys
import warnings
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends

from swx_api.core.config.settings import settings
# Authentication removed - Skill Coach only
from swx_api.core.utils.loader import dynamic_import, load_all_modules

from swx_api.core.utils.helper import to_pascal_case

# Force UTF-8 encoding for Windows (fix Unicode errors)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Initialize the main API router
router = APIRouter()

ALLOWED_ROUTE_MODULES = {
    "swx_api.app.routes.skills_route",
    "swx_api.app.routes.ingestion_route",
    "swx_api.app.routes.recommendations_route",
    "swx_api.app.routes.analytics_route",
    "swx_api.app.routes.dashboard_route",
    "swx_api.app.routes.career_coach_route",
    "swx_api.app.routes.training_plan_route",
    "swx_api.app.routes.leadership_narrative_route",
    "swx_api.app.routes.predictive_analytics_route",
    "swx_api.app.routes.ai_route",
    "swx_api.app.routes.hackathon_routes",
}

# Track which modules have been loaded to prevent duplication
loaded_modules_set = set()


def router_module(
        module, full_module_name: str, main_router: APIRouter, version: Optional[str] = None
):
    if not full_module_name.startswith("swx_api.core.routes") and full_module_name not in ALLOWED_ROUTE_MODULES:
        print(f"⏩ Skipping non-MVP module: {full_module_name}")
        return
    if full_module_name in loaded_modules_set:
        print(f"⏩ Skipping already loaded module: {full_module_name}")
        return
    loaded_modules_set.add(full_module_name)

    if not hasattr(module, "router"):
        print(f"⚠️ WARNING: Module '{full_module_name}' does not have a 'router' attribute.")
        return

    module_parts = full_module_name.split(".")
    try:
        idx = module_parts.index("routes")
        route_parts = module_parts[idx + 1:]
    except ValueError:
        print(f"⚠️ WARNING: Could not determine route structure for '{full_module_name}'")
        return

    if not route_parts:
        print(f"⚠️ WARNING: No route parts found for module '{full_module_name}'")
        return

    user_defined_prefix = getattr(module.router, "prefix", "").strip()

    if not user_defined_prefix:
        subfolders = route_parts[:-1]
        route_file = route_parts[-1].replace("_route", "").replace("_routes", "")
        if subfolders and subfolders[-1].lower() == route_file.lower():
            default_prefix = "/" + "/".join(subfolders)
        else:
            default_prefix = "/" + "/".join(subfolders + [route_file])
        user_defined_prefix = default_prefix
        print(f"⚠️ No prefix set in {full_module_name}. Using default prefix: {user_defined_prefix}")

    if not user_defined_prefix.startswith("/"):
        user_defined_prefix = "/" + user_defined_prefix

    # Normalize route paths
    normalized_prefix = user_defined_prefix.rstrip("/")
    for route in module.router.routes:
        if route.path.startswith(normalized_prefix + "/") or route.path == normalized_prefix:
            new_path = route.path[len(normalized_prefix):]
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            route.path = new_path or "/"

    module.router.prefix = ""
    if user_defined_prefix.startswith(settings.ROUTE_PREFIX):
        include_prefix = user_defined_prefix
    else:
        include_prefix = f"{settings.ROUTE_PREFIX.rstrip('/')}{user_defined_prefix}"

    # Admin protection removed - Skill Coach only (no auth needed)

    # ✅ Generate clean, deduplicated OpenAPI tag
    tag_parts = [p for p in include_prefix.split("/") if p not in {"api", "v1", "v2"}]

    # Remove consecutive duplicates (e.g. user/user/api_keys → user/api_keys)
    deduped_parts = []
    prev = None
    for part in tag_parts:
        if part != prev:
            deduped_parts.append(part)
        prev = part

    base_tag = to_pascal_case("_".join(deduped_parts))
    tag_prefix = "Core" if full_module_name.startswith("swx_api.core") else "User"

    # Avoid "UserUserX" or "CoreCoreX" tags
    if base_tag.startswith(tag_prefix):
        tag = base_tag
    else:
        tag = f"{tag_prefix}{base_tag}"

    try:
        main_router.include_router(module.router, prefix=include_prefix, tags=[tag])
        print(f"✅ Registered route: '{full_module_name}' → '{include_prefix}' with tag '{tag}'")
    except Exception as e:
        print(f"❌ ERROR: Failed to register router from '{full_module_name}': {e}")


# -------------------------------------------------------------------
# Load Core Routes from swx_api/core/routes
# -------------------------------------------------------------------
core_routes_dict = dynamic_import("swx_api/core/routes", "swx_api.core.routes", recursive=True)
if core_routes_dict:
    for full_module_name, module in core_routes_dict.items():
        router_module(module, full_module_name, router)
else:
    print("⚠️ No core routes found in swx_api/core/routes.")


# -------------------------------------------------------------------
# Load Versioned Routes (e.g. v1, v2)
# -------------------------------------------------------------------
def load_versioned_routes(router: APIRouter):
    versioned_routes_exist = False
    for version in settings.API_VERSIONS:
        routes_path = Path(f"swx_api/app/routes/{version}")
        if not routes_path.exists():
            print(f"⚠️ No routes found for `{version}`. Skipping...")
            continue

        api_routes_dict = dynamic_import(
            f"swx_api/app/routes/{version}",
            f"swx_api.app.routes.{version}",
            recursive=True,
        )
        if not api_routes_dict:
            warnings.warn(f"⚠️ No API routes found in `{routes_path}`.", stacklevel=2)
            continue

        versioned_routes_exist = True
        for module_name, module in api_routes_dict.items():
            full_module_name = f"swx_api.app.routes.{version}.{module_name}"
            router_module(module, full_module_name, router, version=version)

    if not versioned_routes_exist:
        print("🔄 No versioned routes found! Only core and non-versioned routes will be available.")


# -------------------------------------------------------------------
# Load Non-Versioned User Routes
# -------------------------------------------------------------------
def load_user_routes(router: APIRouter):
    routes_path = Path("swx_api/app/routes")
    if not routes_path.exists():
        print("⚠️ No user-defined API routes found. Skipping...")
        return

    user_routes_dict = dynamic_import(
        "swx_api/app/routes", "swx_api.app.routes", recursive=True
    )
    if not user_routes_dict:
        warnings.warn(f"⚠️ No user-defined API routes found in `{routes_path}`.", stacklevel=2)
        return

    for module_name, module in user_routes_dict.items():
        full_module_name = (
            module_name if module_name.startswith("swx_api.")
            else f"swx_api.app.routes.{module_name}"
        )
        router_module(module, full_module_name, router)


# -------------------------------------------------------------------
# Execute loaders
# -------------------------------------------------------------------
load_versioned_routes(router)
load_user_routes(router)

# Load all models, services, repositories (optional utilities)
load_all_modules()
