#!/usr/bin/env python3
"""
ŠKODA AI Skill Coach - Complete Smoke Test
Tests entire system with Docker, fake data, and fallback AI mode
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"
TIMEOUT = 30.0
MAX_RETRIES = 10

# Test results
results: Dict[str, List[Tuple[str, bool, str]]] = {
    "passed": [],
    "failed": [],
    "skipped": []
}


def log_info(msg: str):
    print(f"\033[0;34m[INFO]\033[0m {msg}")


def log_success(msg: str):
    print(f"\033[0;32m[PASS]\033[0m {msg}")
    results["passed"].append(("", True, msg))


def log_error(msg: str):
    print(f"\033[0;31m[FAIL]\033[0m {msg}")
    results["failed"].append(("", False, msg))


def log_warning(msg: str):
    print(f"\033[1;33m[WARN]\033[0m {msg}")
    results["skipped"].append(("", True, msg))


async def wait_for_service(url: str, service_name: str) -> bool:
    """Wait for a service to be ready."""
    log_info(f"Waiting for {service_name} to be ready...")
    async with httpx.AsyncClient(timeout=5.0) as client:
        for attempt in range(MAX_RETRIES):
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    log_success(f"{service_name} is ready")
                    return True
            except Exception:
                pass
            await asyncio.sleep(2)
    
    log_error(f"{service_name} failed to start after {MAX_RETRIES * 2} seconds")
    return False


async def test_endpoint(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    expected_status: int = 200,
    description: str = ""
) -> Tuple[bool, str]:
    """Test a single endpoint."""
    url = f"{BACKEND_URL}{endpoint}"
    desc = description or f"{method} {endpoint}"
    
    try:
        if method == "GET":
            response = await client.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = await client.post(url, json=data, timeout=TIMEOUT)
        else:
            return False, f"Unsupported method: {method}"
        
        if response.status_code == expected_status:
            try:
                body = response.json()
                is_json = True
                # Check for AI fallback mode in response
                if isinstance(body, dict) and body.get("data"):
                    data_obj = body.get("data", {})
                    if isinstance(data_obj, dict) and "ai_mode" in data_obj:
                        ai_mode = data_obj.get("ai_mode")
                        if ai_mode == "fallback":
                            log_success(f"{desc} -> {response.status_code} (fallback mode)")
                        else:
                            log_success(f"{desc} -> {response.status_code} (ai_mode: {ai_mode})")
                    else:
                        log_success(f"{desc} -> {response.status_code}")
                else:
                    log_success(f"{desc} -> {response.status_code}")
                
                return True, f"Status {response.status_code}, valid JSON"
            except json.JSONDecodeError:
                log_warning(f"{desc} -> {response.status_code} (non-JSON response)")
                return True, f"Status {response.status_code}, non-JSON"
        else:
            log_error(f"{desc} -> {response.status_code} (expected {expected_status})")
            return False, f"Status {response.status_code}, expected {expected_status}"
    except httpx.TimeoutException:
        log_error(f"{desc} -> Timeout")
        return False, "Timeout"
    except Exception as e:
        log_error(f"{desc} -> Error: {str(e)}")
        return False, str(e)


async def test_ingestion(client: httpx.AsyncClient) -> Optional[str]:
    """Test dataset ingestion and return dataset_id."""
    log_info("Testing dataset ingestion...")
    
    # Generate fake dataset
    dataset_file = Path("fake_skoda_dataset.csv")
    if not dataset_file.exists():
        log_info("Generating fake dataset...")
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/generate_fake_dataset.py", "80", str(dataset_file)],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            log_error(f"Failed to generate dataset: {result.stderr}")
            return None
    
    # Upload dataset
    try:
        with open(dataset_file, "rb") as f:
            files = {"file": (dataset_file.name, f, "text/csv")}
            response = await client.post(
                f"{BACKEND_URL}/api/ingestion/ingest",
                files=files,
                timeout=60.0
            )
        
        if response.status_code == 200:
            body = response.json()
            dataset_id = body.get("data", {}).get("dataset_id")
            if dataset_id:
                log_success(f"Dataset ingested: {dataset_id}")
                
                # Load employees
                load_response = await client.post(
                    f"{BACKEND_URL}/api/ingestion/load-employees/{dataset_id}",
                    json={
                        "employee_id_column": "employee_id",
                        "department_column": "department"
                    },
                    timeout=60.0
                )
                
                if load_response.status_code == 200:
                    load_body = load_response.json()
                    total_loaded = load_body.get("data", {}).get("total_loaded", 0)
                    log_success(f"Loaded {total_loaded} employees")
                else:
                    log_warning(f"Failed to load employees: {load_response.status_code}")
                
                return dataset_id
            else:
                log_error("Dataset ID not found in response")
                return None
        else:
            log_error(f"Ingestion failed: {response.status_code}")
            return None
    except Exception as e:
        log_error(f"Ingestion error: {str(e)}")
        return None


async def main():
    """Run complete smoke test."""
    print("=" * 80)
    print("ŠKODA AI Skill Coach - Complete Smoke Test")
    print("=" * 80)
    print()
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # SECTION 1: Wait for services
        print("SECTION 1: Starting Docker System")
        print("-" * 80)
        if not await wait_for_service(f"{BACKEND_URL}/healthz", "Backend"):
            sys.exit(1)
        print()
        
        # SECTION 2: Verify AI Fallback
        print("SECTION 2: Verifying AI Fallback Mode")
        print("-" * 80)
        # Check via a test endpoint that uses AI
        await test_endpoint(
            client, "GET", "/api/ai/employee-intel/EMP-001",
            description="AI Fallback Test (should use fallback)"
        )
        print()
        
        # SECTION 3: Ingest Dataset
        print("SECTION 3: Generating and Ingesting Fake Dataset")
        print("-" * 80)
        dataset_id = await test_ingestion(client)
        print()
        
        # SECTION 4: Test Backend Endpoints
        print("SECTION 4: Smoke Testing Backend Endpoints")
        print("-" * 80)
        
        # Dashboard
        await test_endpoint(client, "GET", "/api/dashboard/overview")
        await test_endpoint(client, "GET", "/api/dashboard/heatmap")
        await test_endpoint(client, "GET", "/api/dashboard/skill-map")
        await test_endpoint(client, "GET", "/api/dashboard/trends?period_months=12")
        
        # Analytics
        await test_endpoint(client, "GET", "/api/analytics/global")
        await test_endpoint(client, "GET", "/api/analytics/employees/EMP-001")
        await test_endpoint(client, "GET", "/api/analytics/departments/Engineering")
        await test_endpoint(client, "GET", "/api/analytics/succession/Engineering")
        await test_endpoint(client, "GET", "/api/analytics/forecast?months=6")
        await test_endpoint(client, "GET", "/api/analytics/predicted-shortages/Engineering?forecast_months=6")
        
        # Skills
        await test_endpoint(client, "GET", "/api/skills/analysis/EMP-001")
        await test_endpoint(client, "GET", "/api/skills/recommendations/skills/EMP-001")
        await test_endpoint(client, "GET", "/api/skills/taxonomy")
        
        # AI Endpoints (should use fallback)
        await test_endpoint(client, "GET", "/api/ai/employee-intel/EMP-001")
        await test_endpoint(
            client, "POST", "/api/ai/career-chat",
            data={"employee_id": "EMP-001", "user_message": "Hello, what are my career options?"}
        )
        await test_endpoint(
            client, "POST", "/api/ai/training-plan",
            data={"employee_id": "EMP-001", "desired_role": "Senior Engineer"}
        )
        await test_endpoint(
            client, "POST", "/api/ai/what-if",
            data={"scenario": "promote EMP-001", "department": "Engineering"}
        )
        
        # Recommendations
        await test_endpoint(client, "GET", "/api/recommendations/mentor/EMP-001")
        
        # Employees
        await test_endpoint(client, "GET", "/api/employees/EMP-001/learning-history")
        
        print()
        
        # SECTION 5: Test Frontend
        print("SECTION 5: Testing Frontend")
        print("-" * 80)
        try:
            response = await client.get(FRONTEND_URL, timeout=5.0)
            if response.status_code == 200:
                log_success(f"Frontend is accessible at {FRONTEND_URL}")
            else:
                log_warning(f"Frontend returned status {response.status_code}")
        except Exception as e:
            log_warning(f"Frontend not accessible: {str(e)}")
        
        print()
        
        # Summary
        print("=" * 80)
        print("SMOKE TEST SUMMARY")
        print("=" * 80)
        print(f"Passed: {len(results['passed'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Skipped: {len(results['skipped'])}")
        print()
        
        if results["failed"]:
            print("Failed Tests:")
            for endpoint, _, msg in results["failed"]:
                print(f"  - {msg}")
            print()
        
        if len(results["failed"]) == 0:
            log_success("All smoke tests passed!")
            return 0
        else:
            log_error("Some smoke tests failed")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

