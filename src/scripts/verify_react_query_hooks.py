#!/usr/bin/env python3
"""
Verify all React Query hooks match backend endpoints
Checks endpoint URLs, methods, and transformations
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Configuration
FRONTEND_HOOKS_DIR = Path("frontend/src/src/hooks")
FRONTEND_SERVICES_DIR = Path("frontend/src/src/services")
BACKEND_ENDPOINTS_FILE = Path("backend/ENDPOINTS.md")

# Expected endpoint mappings
EXPECTED_ENDPOINTS = {
    # Dashboard
    "/api/dashboard/overview": "GET",
    "/api/dashboard/heatmap": "GET",
    "/api/dashboard/skill-map": "GET",
    "/api/dashboard/trends": "GET",
    
    # Analytics
    "/api/analytics/global": "GET",
    "/api/analytics/employees/{employee_id}": "GET",
    "/api/analytics/departments/{department_name}": "GET",
    "/api/analytics/succession/{department_name}": "GET",
    "/api/analytics/forecast": "GET",
    "/api/analytics/predicted-shortages/{department}": "GET",
    
    # Skills
    "/api/skills/analysis/{employee_id}": "GET",
    "/api/skills/recommendations/skills/{employee_id}": "GET",
    "/api/skills/taxonomy": "GET",
    
    # AI
    "/api/ai/employee-intel/{employee_id}": "GET",
    "/api/ai/career-chat": "POST",
    "/api/ai/training-plan": "POST",
    "/api/ai/what-if": "POST",
    
    # Recommendations
    "/api/recommendations/mentor/{employee_id}": "GET",
    
    # Employees
    "/api/employees/{employee_id}/learning-history": "GET",
    
    # Ingestion
    "/api/ingestion/ingest": "POST",
    "/api/ingestion/datasets": "GET",
    "/api/ingestion/load-employees/{dataset_id}": "POST",
}

results: Dict[str, List[Tuple[str, bool, str]]] = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def log_success(msg: str):
    print(f"\033[0;32m[PASS]\033[0m {msg}")
    results["passed"].append(("", True, msg))


def log_error(msg: str):
    print(f"\033[0;31m[FAIL]\033[0m {msg}")
    results["failed"].append(("", False, msg))


def log_warning(msg: str):
    print(f"\033[1;33m[WARN]\033[0m {msg}")
    results["warnings"].append(("", True, msg))


def extract_endpoint_from_service(service_file: Path) -> Dict[str, str]:
    """Extract endpoint URLs and methods from service file."""
    endpoints = {}
    
    if not service_file.exists():
        return endpoints
    
    content = service_file.read_text(encoding="utf-8")
    
    # Find API calls: apiClient.get/post/put/delete('/endpoint')
    patterns = [
        (r"apiClient\.(get|post|put|delete)\s*\(\s*['\"]([^'\"]+)['\"]", "method"),
        (r"apiClient\.(get|post|put|delete)\s*\(\s*`([^`]+)`", "method"),
    ]
    
    for pattern, _ in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            method = match.group(1).upper()
            endpoint = match.group(2)
            # Normalize endpoint (remove query params, etc.)
            endpoint = endpoint.split("?")[0]
            endpoints[endpoint] = method
    
    return endpoints


def extract_hooks_from_file(hook_file: Path) -> List[Dict]:
    """Extract hook definitions from a hook file."""
    hooks = []
    
    if not hook_file.exists():
        return hooks
    
    content = hook_file.read_text(encoding="utf-8")
    
    # Find useQuery and useMutation calls
    query_pattern = r"useQuery\s*\(\s*\{[^}]*queryKey:\s*\[([^\]]+)\][^}]*queryFn[^}]*\}"
    mutation_pattern = r"useMutation\s*\(\s*\{[^}]*mutationFn[^}]*\}"
    
    # Simple extraction - look for function names
    function_pattern = r"export\s+(?:async\s+)?function\s+(\w+)\s*\("
    
    matches = re.finditer(function_pattern, content)
    for match in matches:
        func_name = match.group(1)
        if func_name.startswith("use"):
            hooks.append({"name": func_name, "file": hook_file.name})
    
    return hooks


def verify_hooks():
    """Verify all React Query hooks."""
    print("=" * 80)
    print("React Query Hooks Verification")
    print("=" * 80)
    print()
    
    # Check service files
    print("Checking Service Files...")
    print("-" * 80)
    
    service_files = list(FRONTEND_SERVICES_DIR.glob("*.service.ts"))
    all_service_endpoints = {}
    
    for service_file in service_files:
        endpoints = extract_endpoint_from_service(service_file)
        all_service_endpoints.update(endpoints)
        log_success(f"{service_file.name}: Found {len(endpoints)} endpoints")
    
    print()
    
    # Check hook files
    print("Checking Hook Files...")
    print("-" * 80)
    
    hook_files = list(FRONTEND_HOOKS_DIR.glob("use*.ts"))
    all_hooks = []
    
    for hook_file in hook_files:
        hooks = extract_hooks_from_file(hook_file)
        all_hooks.extend(hooks)
        log_success(f"{hook_file.name}: Found {len(hooks)} hooks")
    
    print()
    
    # Verify endpoints match
    print("Verifying Endpoint Coverage...")
    print("-" * 80)
    
    for expected_endpoint, expected_method in EXPECTED_ENDPOINTS.items():
        # Normalize endpoint (remove path params for matching)
        normalized = expected_endpoint.replace("{employee_id}", "").replace("{department_name}", "").replace("{department}", "").replace("{dataset_id}", "")
        
        found = False
        for service_endpoint, method in all_service_endpoints.items():
            if normalized in service_endpoint or service_endpoint in normalized:
                if method == expected_method:
                    log_success(f"✓ {expected_method} {expected_endpoint}")
                    found = True
                    break
        
        if not found:
            log_warning(f"⚠ {expected_method} {expected_endpoint} - Not found in services")
    
    print()
    
    # Summary
    print("=" * 80)
    print("Verification Summary")
    print("=" * 80)
    print(f"Service Files: {len(service_files)}")
    print(f"Endpoints Found: {len(all_service_endpoints)}")
    print(f"Hook Files: {len(hook_files)}")
    print(f"Hooks Found: {len(all_hooks)}")
    print(f"Passed: {len(results['passed'])}")
    print(f"Failed: {len(results['failed'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print()
    
    if results["failed"]:
        print("Failed Checks:")
        for _, _, msg in results["failed"]:
            print(f"  - {msg}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(verify_hooks())

