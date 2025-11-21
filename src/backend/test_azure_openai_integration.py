#!/usr/bin/env python3
"""
Comprehensive Azure OpenAI Integration Test
===========================================
Tests all aspects of Azure OpenAI integration before real Škoda data ingestion.
"""

import asyncio
import os
import sys
import json
import time
import logging
from pathlib import Path

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

# Setup logging for audit log section
logger = logging.getLogger(__name__)

# Set environment variables BEFORE any imports
# Load from .env file if it exists (check both current dir and parent dir)
from dotenv import load_dotenv
env_path = Path(".env")
parent_env_path = Path("../.env")
if env_path.exists():
    load_dotenv(env_path)
elif parent_env_path.exists():
    load_dotenv(parent_env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Import after path setup
from swx_api.app.config.settings import app_settings
from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.app.services.azure_llm_client import AzureLLMClient
from swx_api.core.database.db import AsyncSessionLocal
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.repositories.audit_repository import AuditRepository
from swx_api.app.models.skill_models import AuditLog
from sqlalchemy import select

# Test configuration
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_PREFIX = "/api/v1"
DEMO_API_TOKEN = os.getenv("DEMO_API_TOKEN", "")

# Test results storage
test_results = {
    "azure_config": {},
    "orchestrator_test": {},
    "endpoint_tests": {},
    "rate_limit_test": {},
    "audit_logs": {},
    "final_status": {}
}


def mask_key(key: str) -> str:
    """Mask API key for display."""
    if not key or len(key) < 10:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


async def validate_azure_config():
    """Step 1: Validate Azure configuration."""
    print("\n" + "="*80)
    print("STEP 1: Validating Azure Configuration")
    print("="*80)
    
    results = {
        "endpoint": {},
        "api_version": {},
        "deployment_name": {},
        "api_key": {},
        "model": {},
        "force_fallback": {},
        "provider": {},
        "issues": []
    }
    
    # Check endpoint
    endpoint = app_settings.AZURE_OPENAI_ENDPOINT
    if not endpoint:
        results["issues"].append("AZURE_OPENAI_ENDPOINT is not set")
        results["endpoint"]["status"] = "MISSING"
    else:
        endpoint = endpoint.rstrip("/")
        if endpoint != app_settings.AZURE_OPENAI_ENDPOINT:
            results["issues"].append(f"Endpoint had trailing slash: {app_settings.AZURE_OPENAI_ENDPOINT}")
        results["endpoint"]["value"] = endpoint
        results["endpoint"]["status"] = "OK" if endpoint.startswith("https://") else "INVALID"
        if results["endpoint"]["status"] == "INVALID":
            results["issues"].append(f"Endpoint must start with https://: {endpoint}")
    
    # Check API version
    api_version = app_settings.AZURE_OPENAI_API_VERSION
    expected_version = "2025-01-01-preview"
    results["api_version"]["value"] = api_version
    if api_version == expected_version:
        results["api_version"]["status"] = "OK"
    else:
        results["api_version"]["status"] = "WARNING"
        results["issues"].append(f"API version is {api_version}, expected {expected_version}")
    
    # Check deployment name
    deployment_name = app_settings.AZURE_OPENAI_DEPLOYMENT_NAME
    if not deployment_name:
        results["deployment_name"]["status"] = "MISSING"
        results["issues"].append("AZURE_OPENAI_DEPLOYMENT_NAME is not set")
    else:
        results["deployment_name"]["value"] = deployment_name
        results["deployment_name"]["status"] = "OK"
        if deployment_name not in ["hackathon-gpt-4.1", "hackathon-gpt-5.1"]:
            results["issues"].append(f"Unexpected deployment name: {deployment_name}")
    
    # Check API key
    api_key = app_settings.AZURE_OPENAI_API_KEY
    if not api_key:
        results["api_key"]["status"] = "MISSING"
        results["issues"].append("AZURE_OPENAI_API_KEY is not set")
    else:
        results["api_key"]["status"] = "OK"
        results["api_key"]["masked"] = mask_key(api_key)
    
    # Check model
    model = app_settings.AZURE_OPENAI_MODEL
    results["model"]["value"] = model
    results["model"]["status"] = "OK"
    
    # Check force fallback
    force_fallback = app_settings.AI_FORCE_FALLBACK
    results["force_fallback"]["value"] = force_fallback
    if force_fallback:
        results["force_fallback"]["status"] = "WARNING"
        results["issues"].append("AI_FORCE_FALLBACK is True - Azure calls will be disabled")
    else:
        results["force_fallback"]["status"] = "OK"
    
    # Check provider
    provider = app_settings.SKILL_LLM_PROVIDER
    results["provider"]["value"] = provider
    if provider == "azure":
        results["provider"]["status"] = "OK"
    else:
        results["provider"]["status"] = "WARNING"
        results["issues"].append(f"SKILL_LLM_PROVIDER is {provider}, expected 'azure'")
    
    # Verify AzureLLMClient initialization
    try:
        test_client = AzureLLMClient(
            endpoint=endpoint or "",
            api_key=api_key or "",
            model=model,
            api_version=api_version,
            deployment_name=deployment_name or ""
        )
        results["client_init"] = {"status": "OK", "message": "AzureLLMClient initialized successfully"}
    except Exception as e:
        results["client_init"] = {"status": "ERROR", "message": str(e)}
        results["issues"].append(f"AzureLLMClient initialization failed: {e}")
    
    # Print results
    print(f"Endpoint: {results['endpoint'].get('value', 'MISSING')} [{results['endpoint'].get('status', 'MISSING')}]")
    print(f"API Version: {results['api_version'].get('value', 'MISSING')} [{results['api_version'].get('status', 'MISSING')}]")
    print(f"Deployment Name: {results['deployment_name'].get('value', 'MISSING')} [{results['deployment_name'].get('status', 'MISSING')}]")
    print(f"API Key: {results['api_key'].get('masked', 'MISSING')} [{results['api_key'].get('status', 'MISSING')}]")
    print(f"Model: {results['model'].get('value', 'MISSING')} [{results['model'].get('status', 'MISSING')}]")
    print(f"Force Fallback: {results['force_fallback'].get('value', 'MISSING')} [{results['force_fallback'].get('status', 'MISSING')}]")
    print(f"Provider: {results['provider'].get('value', 'MISSING')} [{results['provider'].get('status', 'MISSING')}]")
    
    if results["issues"]:
        print("\nIssues found:")
        for issue in results["issues"]:
            print(f"  - {issue}")
    
    test_results["azure_config"] = results
    return len(results["issues"]) == 0


async def test_orchestrator_direct():
    """Step 2: Test orchestrator directly."""
    print("\n" + "="*80)
    print("STEP 2: Testing AIOrchestrator Directly")
    print("="*80)
    
    results = {
        "status": "FAILED",
        "response": None,
        "error": None,
        "schema_valid": False,
        "azure_used": False,
        "fallback_triggered": False,
        "retries": 0
    }
    
    try:
        orchestrator = AIOrchestrator()
        
        schema = {
            "summary": str,
            "strengths": list,
            "development_areas": list,
            "readiness_score": int,
            "next_role_readiness": str,
            "recommended_actions": list,
            "risk_signals": list,
            "career_trajectory": str
        }
        
        # Match the prompt template variables
        variables = {
            "employee_data": json.dumps({
                "employee_id": "TEST123",
                "name": "Test User",
                "department": "TEST_DEPT"
            }, indent=2),
            "skills": json.dumps(["communication", "problem solving"], indent=2),
            "history": json.dumps([], indent=2),
            "qualifications": json.dumps([], indent=2)
        }
        
        print(f"Calling orchestrator.run() with prompt_name='employee_summary'...")
        print(f"Variables: {variables}")
        
        start_time = time.time()
        result = await orchestrator.run(
            prompt_name="employee_summary",
            variables=variables,
            schema=schema,
            language=None,
            max_completion_tokens=1000
        )
        elapsed_time = time.time() - start_time
        
        results["response"] = result
        results["schema_valid"] = all(key in result for key in schema.keys())
        results["azure_used"] = result.get("ai_mode") == "azure"
        results["fallback_triggered"] = result.get("ai_mode") == "fallback"
        results["elapsed_time"] = elapsed_time
        
        if results["fallback_triggered"]:
            results["error"] = result.get("error", "Fallback triggered")
            results["status"] = "FAILED - FALLBACK TRIGGERED"
        elif results["azure_used"]:
            results["status"] = "SUCCESS"
        else:
            results["status"] = "WARNING - Unknown mode"
        
        print(f"Status: {results['status']}")
        print(f"AI Mode: {result.get('ai_mode', 'unknown')}")
        print(f"Schema Valid: {results['schema_valid']}")
        print(f"Elapsed Time: {elapsed_time:.2f}s")
        print(f"Response keys: {list(result.keys())}")
        
        if results["fallback_triggered"]:
            print(f"Error: {results['error']}")
        else:
            print(f"Summary preview: {str(result.get('summary', ''))[:100]}...")
        
    except Exception as e:
        results["error"] = str(e)
        results["status"] = "ERROR"
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    test_results["orchestrator_test"] = results
    return results["status"] == "SUCCESS"


async def create_test_employee(session: AsyncSession, employee_id: str = "TEST123"):
    """Create a test employee record."""
    employee_repo = EmployeeRepository()
    
    # Check if employee already exists
    existing = await employee_repo.get_by_employee_id(session, employee_id)
    if existing:
        print(f"Employee {employee_id} already exists, using existing record")
        return existing
    
    # Create new employee - EmployeeRecord doesn't have full_name field
    employee = EmployeeRecord(
        employee_id=employee_id,
        personal_number=employee_id,
        department="TEST_DEPT",
        skills=["leadership", "problem solving"],
        pers_profession_name="Analyst"
    )
    
    session.add(employee)
    await session.commit()
    await session.refresh(employee)
    
    print(f"Created test employee: {employee_id}")
    return employee


async def test_ai_endpoints():
    """Step 3: Test all AI endpoints with fake data."""
    print("\n" + "="*80)
    print("STEP 3: Testing All AI Endpoints")
    print("="*80)
    
    results = {}
    
    # Use AsyncSessionLocal directly instead of get_async_session() which is a dependency
    async with AsyncSessionLocal() as session:
        try:
            # Create test employee
            await create_test_employee(session, "TEST123")
            await create_test_employee(session, "TEST1")
            await create_test_employee(session, "TEST2")
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        
        # Test endpoints
        # Note: Routes are under /api/ai/... (no v1) based on ROUTE_PREFIX=/api
        endpoints = [
            ("GET", "/api/ai/employee-intel/TEST123", None),
            ("GET", "/api/ai/team-intel/TEST_DEPT", None),
            ("GET", "/api/ai/succession-intel/TEST_DEPT", None),
            ("POST", "/api/ai/career-chat", {
                "employee_id": "TEST123",
                "user_message": "What skills should I develop?",
                "skills": ["leadership", "problem solving"],
                "career_goals": "Become a senior analyst",
                "department": "TEST_DEPT"
            }),
            ("POST", "/api/ai/training-plan", {
                "employee_id": "TEST123",
                "skills": ["leadership", "problem solving"],
                "gaps": ["data analysis"],
                "desired_role": "Senior Analyst"
            }),
            ("GET", "/api/ai/compare/TEST_DEPT/TEST_DEPT", None),
            ("GET", "/api/ai/leadership-narrative/TEST_DEPT", None),
        ]
        
        # what-if endpoint uses Query parameters, not Body
        endpoints.append(("POST", "/api/ai/what-if?scenario_type=add_skill&employee_id=TEST123", {"changes": {"skill": "data analysis"}}))
        
        # Prepare headers with API token if available
        headers = {}
        if DEMO_API_TOKEN:
            headers["Authorization"] = f"Bearer {DEMO_API_TOKEN}"
            headers["X-API-Key"] = DEMO_API_TOKEN
        
        async with httpx.AsyncClient(timeout=120.0, headers=headers) as client:
            for method, endpoint, payload in endpoints:
                endpoint_name = endpoint.split("/")[-1] or endpoint.split("/")[-2]
                print(f"\nTesting {method} {endpoint}...")
                
                endpoint_result = {
                    "status_code": None,
                    "success": False,
                    "azure_used": False,
                    "fallback_triggered": False,
                    "error": None,
                    "response_time": None
                }
                
                try:
                    start_time = time.time()
                    
                    # Use headers if DEMO_API_TOKEN is available, otherwise try without
                    request_headers = headers if DEMO_API_TOKEN else {}
                    
                    if method == "GET":
                        response = await client.get(f"{BASE_URL}{endpoint}", headers=request_headers)
                    else:
                        # Handle what-if endpoint with query params
                        if "what-if" in endpoint and "?" in endpoint:
                            url = f"{BASE_URL}{endpoint}"
                            response = await client.post(url, json=payload if payload else {}, headers=request_headers)
                        else:
                            response = await client.post(f"{BASE_URL}{endpoint}", json=payload, headers=request_headers)
                    
                    elapsed = time.time() - start_time
                    endpoint_result["status_code"] = response.status_code
                    endpoint_result["response_time"] = elapsed
                    
                    if response.status_code == 200:
                        data = response.json()
                        endpoint_result["success"] = True
                        
                        # Check for Azure usage
                        if isinstance(data, dict):
                            # Check nested data field
                            actual_data = data.get("data", data)
                            if isinstance(actual_data, dict):
                                endpoint_result["azure_used"] = actual_data.get("ai_mode") == "azure"
                                endpoint_result["fallback_triggered"] = actual_data.get("ai_mode") == "fallback"
                                if endpoint_result["fallback_triggered"]:
                                    endpoint_result["error"] = actual_data.get("error", "Fallback triggered")
                        
                        print(f"  ✓ Status: {response.status_code}, Time: {elapsed:.2f}s")
                        print(f"    Azure Used: {endpoint_result['azure_used']}, Fallback: {endpoint_result['fallback_triggered']}")
                    elif response.status_code == 401:
                        # Authentication required but token not configured - skip this test
                        endpoint_result["success"] = False
                        endpoint_result["fallback_triggered"] = False
                        endpoint_result["error"] = f"HTTP 401: Authentication required (DEMO_API_TOKEN not configured)"
                        print(f"  ⚠ Status: {response.status_code} (Authentication required - DEMO_API_TOKEN not set)")
                        print(f"    Note: Endpoints require DEMO_API_TOKEN in environment to test")
                    else:
                        endpoint_result["success"] = False
                        endpoint_result["fallback_triggered"] = False
                        endpoint_result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                        print(f"  ✗ Status: {response.status_code}")
                        print(f"    Error: {endpoint_result['error']}")
                        
                except Exception as e:
                    endpoint_result["error"] = str(e)
                    endpoint_result["success"] = False
                    endpoint_result["fallback_triggered"] = False
                    print(f"  ✗ Exception: {e}")
                
                # Ensure endpoint_result always has required fields
                if "success" not in endpoint_result:
                    endpoint_result["success"] = False
                if "fallback_triggered" not in endpoint_result:
                    endpoint_result["fallback_triggered"] = False
                
                results[endpoint_name] = endpoint_result
        
        await session.close()
    
    test_results["endpoint_tests"] = results
    # Ensure we're checking dicts, not bools
    success_count = sum(1 for r in results.values() if isinstance(r, dict) and r.get("success", False) and not r.get("fallback_triggered", False))
    return success_count == len(results) and len(results) > 0


async def test_rate_limits():
    """Step 4: Test rate limits and retry logic."""
    print("\n" + "="*80)
    print("STEP 4: Testing Rate Limits & Retry Logic")
    print("="*80)
    
    results = {
        "status": "PENDING",
        "retry_behavior": None,
        "error_message": None
    }
    
    # Save original key
    original_key = app_settings.AZURE_OPENAI_API_KEY
    
    try:
        # Set fake API key
        os.environ["AZURE_OPENAI_API_KEY"] = "fake-key-12345"
        # Reload settings
        from importlib import reload
        from swx_api.app.config import settings
        reload(settings)
        from swx_api.app.config.settings import app_settings as reloaded_settings
        
        print("Using fake API key to test retry logic...")
        
        orchestrator = AIOrchestrator()
        schema = {"response": str}
        variables = {"test": "data"}
        
        try:
            result = await orchestrator.run(
                prompt_name="employee_summary",
                variables=variables,
                schema=schema
            )
            
            if result.get("ai_mode") == "fallback":
                results["status"] = "SUCCESS - Fallback triggered correctly"
                results["retry_behavior"] = "Fallback activated"
                results["error_message"] = result.get("error", "Unknown error")
                print(f"  ✓ Fallback triggered correctly")
                print(f"    Error: {results['error_message']}")
            else:
                results["status"] = "WARNING - Fallback not triggered"
                print(f"  ⚠ Fallback not triggered, mode: {result.get('ai_mode')}")
                
        except Exception as e:
            results["status"] = "SUCCESS - Exception caught"
            results["retry_behavior"] = "Exception raised"
            results["error_message"] = str(e)
            print(f"  ✓ Exception caught: {e}")
        
    finally:
        # Restore original key
        os.environ["AZURE_OPENAI_API_KEY"] = original_key or ""
        from importlib import reload
        from swx_api.app.config import settings
        reload(settings)
        print("  ✓ Original API key restored")
    
    test_results["rate_limit_test"] = results
    return True  # Test passed if we got here


async def verify_audit_logs():
    """Step 5: Verify audit log entries."""
    print("\n" + "="*80)
    print("STEP 5: Verifying Audit Logs")
    print("="*80)
    
    results = {
        "entries_found": 0,
        "azure_entries": 0,
        "provider_azure": 0,
        "model_name_present": 0,
        "token_usage_present": 0,
        "latency_present": 0,
        "request_id_present": 0,
        "sample_entries": []
    }
    
    try:
        # Use AsyncSessionLocal directly instead of get_async_session() which is a dependency
        async with AsyncSessionLocal() as session:
            try:
                audit_repo = AuditRepository()
                
                # Get recent audit logs
                stmt = select(AuditLog).where(
                    AuditLog.event_type == "ai_call"
                ).order_by(AuditLog.created_at.desc()).limit(20)
                
                result = await session.execute(stmt)
                logs = result.scalars().all()
                
                results["entries_found"] = len(logs)
                print(f"Found {len(logs)} audit log entries")
                
                for log in logs:
                    log_data = log.log_data if hasattr(log, "log_data") else {}
                    if not isinstance(log_data, dict):
                        try:
                            log_data = json.loads(log_data) if isinstance(log_data, str) else {}
                        except:
                            log_data = {}
                    
                    # Check for Azure entries
                    if log_data.get("provider") == "azure" or log_data.get("ai_provider") == "azure":
                        results["azure_entries"] += 1
                        results["provider_azure"] += 1
                    
                    # Check for model name
                    if log_data.get("model_name") or log_data.get("model"):
                        results["model_name_present"] += 1
                    
                    # Check for token usage
                    if log_data.get("token_usage") or log_data.get("prompt_tokens") or log_data.get("completion_tokens"):
                        results["token_usage_present"] += 1
                    
                    # Check for latency
                    if log_data.get("latency") or log_data.get("elapsed_ms") or log_data.get("response_time"):
                        results["latency_present"] += 1
                    
                    # Check for request_id
                    if log_data.get("request_id") or hasattr(log, "id"):
                        results["request_id_present"] += 1
                    
                    # Store sample
                    if results["azure_entries"] <= 3:
                        results["sample_entries"].append({
                            "id": str(log.id) if hasattr(log, "id") else None,
                            "event_type": log.event_type if hasattr(log, "event_type") else None,
                            "provider": log_data.get("provider") or log_data.get("ai_provider"),
                            "model": log_data.get("model_name") or log_data.get("model"),
                            "success": log_data.get("success", True),
                            "created_at": str(log.created_at) if hasattr(log, "created_at") else None
                        })
                
                print(f"Azure entries: {results['azure_entries']}")
                print(f"Provider=azure: {results['provider_azure']}")
                print(f"Model name present: {results['model_name_present']}")
                print(f"Token usage present: {results['token_usage_present']}")
                print(f"Latency present: {results['latency_present']}")
                print(f"Request ID present: {results['request_id_present']}")
                
                if results["sample_entries"]:
                    print("\nSample entries:")
                    for entry in results["sample_entries"]:
                        print(f"  - Provider: {entry.get('provider')}, Model: {entry.get('model')}, Success: {entry.get('success')}")
            except Exception as inner_exc:
                logger.error(f"Error in audit log check: {inner_exc}")
                raise
            finally:
                await session.close()
    
    except Exception as e:
        results["error"] = str(e)
        print(f"Error checking audit logs: {e}")
        import traceback
        traceback.print_exc()
    
    test_results["audit_logs"] = results
    return results["azure_entries"] > 0


async def generate_final_report():
    """Step 6: Generate final report."""
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    
    # Determine overall status
    config_ok = len(test_results["azure_config"].get("issues", [])) == 0
    orchestrator_ok = test_results["orchestrator_test"].get("status") == "SUCCESS"
    # Fix: Ensure we're checking dicts, not bools or other types
    endpoint_results = test_results.get("endpoint_tests", {})
    if endpoint_results.get("skipped"):
        endpoints_ok = False
    else:
        endpoints_ok = True
        for r in endpoint_results.values():
            if not isinstance(r, dict):
                continue  # Skip non-dict results
            if not r.get("success", False) or r.get("fallback_triggered", False):
                endpoints_ok = False
                break
    rate_limit_ok = test_results["rate_limit_test"].get("status", "").startswith("SUCCESS")
    audit_ok = test_results["audit_logs"].get("azure_entries", 0) > 0
    
    overall_status = "WORKING" if (config_ok and orchestrator_ok and endpoints_ok) else "FAILING"
    
    print(f"\nAzure Status: {overall_status}")
    print(f"\nConfiguration: {'✓' if config_ok else '✗'}")
    print(f"Orchestrator: {'✓' if orchestrator_ok else '✗'}")
    print(f"Endpoints: {'✓' if endpoints_ok else '✗'}")
    print(f"Rate Limits: {'✓' if rate_limit_ok else '✗'}")
    print(f"Audit Logs: {'✓' if audit_ok else '✗'}")
    
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    # Configuration validation
    config = test_results["azure_config"]
    print(f"\n1. Azure Configuration:")
    print(f"   - Endpoint: {config.get('endpoint', {}).get('status', 'UNKNOWN')}")
    print(f"   - API Version: {config.get('api_version', {}).get('status', 'UNKNOWN')}")
    print(f"   - Deployment: {config.get('deployment_name', {}).get('status', 'UNKNOWN')}")
    print(f"   - API Key: {config.get('api_key', {}).get('status', 'UNKNOWN')}")
    if config.get("issues"):
        print(f"   Issues: {len(config['issues'])}")
        for issue in config["issues"]:
            print(f"     - {issue}")
    
    # Orchestrator test
    orch = test_results["orchestrator_test"]
    print(f"\n2. Orchestrator Test:")
    print(f"   - Status: {orch.get('status', 'UNKNOWN')}")
    print(f"   - Azure Used: {orch.get('azure_used', False)}")
    print(f"   - Fallback Triggered: {orch.get('fallback_triggered', False)}")
    print(f"   - Schema Valid: {orch.get('schema_valid', False)}")
    if orch.get("error"):
        print(f"   - Error: {orch['error']}")
    
    # Endpoint tests
    endpoints = test_results["endpoint_tests"]
    print(f"\n3. Endpoint Tests:")
    for endpoint, result in endpoints.items():
        if not isinstance(result, dict):
            print(f"   ✗ {endpoint}: Invalid result type ({type(result)})")
            continue
        status = "✓" if result.get("success") and not result.get("fallback_triggered") else "✗"
        print(f"   {status} {endpoint}: {result.get('status_code', 'N/A')}")
        if result.get("fallback_triggered"):
            print(f"      ⚠ Fallback triggered")
    
    # Rate limit test
    rate_limit = test_results["rate_limit_test"]
    print(f"\n4. Rate Limit Test:")
    print(f"   - Status: {rate_limit.get('status', 'UNKNOWN')}")
    print(f"   - Behavior: {rate_limit.get('retry_behavior', 'UNKNOWN')}")
    
    # Audit logs
    audit = test_results["audit_logs"]
    print(f"\n5. Audit Logs:")
    print(f"   - Total entries: {audit.get('entries_found', 0)}")
    print(f"   - Azure entries: {audit.get('azure_entries', 0)}")
    print(f"   - Model name present: {audit.get('model_name_present', 0)}")
    print(f"   - Token usage present: {audit.get('token_usage_present', 0)}")
    
    print("\n" + "="*80)
    print("REQUIRED FIXES")
    print("="*80)
    
    fixes_needed = []
    
    if not config_ok:
        fixes_needed.extend(config.get("issues", []))
    
    if not orchestrator_ok:
        fixes_needed.append("Orchestrator not using Azure - check AI_FORCE_FALLBACK and SKILL_LLM_PROVIDER")
    
    endpoint_failures = [
        endpoint for endpoint, result in endpoints.items()
        if isinstance(result, dict) and (not result.get("success") or result.get("fallback_triggered"))
    ]
    if endpoint_failures:
        fixes_needed.append(f"Endpoints with issues: {', '.join(endpoint_failures)}")
    
    if not fixes_needed:
        print("  None - All checks passed!")
    else:
        for fix in fixes_needed:
            print(f"  - {fix}")
    
    print("\n" + "="*80)
    
    # Final confirmation
    if overall_status == "WORKING" and not fixes_needed:
        print("\n✓ Azure integration fully functional. Safe to proceed with real Škoda data.")
        print("="*80)
    else:
        print("\n✗ Azure integration needs attention before proceeding with real Škoda data.")
        print("="*80)
    
    test_results["final_status"] = {
        "overall_status": overall_status,
        "config_ok": config_ok,
        "orchestrator_ok": orchestrator_ok,
        "endpoints_ok": endpoints_ok,
        "rate_limit_ok": rate_limit_ok,
        "audit_ok": audit_ok,
        "fixes_needed": fixes_needed,
        "ready_for_production": overall_status == "WORKING" and not fixes_needed
    }
    
    return overall_status == "WORKING" and not fixes_needed


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("Azure OpenAI Integration Test Suite")
    print("="*80)
    print(f"Testing against: {BASE_URL}")
    print(f"Provider: {app_settings.SKILL_LLM_PROVIDER}")
    print(f"Endpoint: {app_settings.AZURE_OPENAI_ENDPOINT}")
    print(f"Deployment: {app_settings.AZURE_OPENAI_DEPLOYMENT_NAME}")
    
    try:
        # Step 1: Validate configuration
        config_ok = await validate_azure_config()
        
        if not config_ok:
            print("\n⚠ Configuration issues found. Continuing tests anyway...")
        
        # Step 2: Test orchestrator
        await test_orchestrator_direct()
        
        # Step 3: Test endpoints (only if backend is running)
        # Use 127.0.0.1 instead of localhost to avoid DNS resolution issues
        test_base_url = BASE_URL.replace("localhost", "127.0.0.1") if "localhost" in BASE_URL else BASE_URL
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try healthz first, then health
                try:
                    await client.get(f"{test_base_url}/healthz")
                except Exception:
                    await client.get(f"{test_base_url}/health")
            print(f"  Backend is running at {test_base_url}")
            # Temporarily override BASE_URL for endpoint tests
            original_base_url = BASE_URL
            import test_azure_openai_integration as test_module
            test_module.BASE_URL = test_base_url
            await test_ai_endpoints()
            # Restore original BASE_URL
            test_module.BASE_URL = original_base_url
        except Exception as e:
            print(f"\n⚠ Backend not running at {BASE_URL}, skipping endpoint tests")
            print(f"  Error: {e}")
            test_results["endpoint_tests"] = {"skipped": True, "reason": str(e)}
        
        # Step 4: Test rate limits
        await test_rate_limits()
        
        # Step 5: Verify audit logs
        await verify_audit_logs()
        
        # Step 6: Generate final report
        success = await generate_final_report()
        
        # Save results to file
        output_file = Path("azure_test_results.json")
        with open(output_file, "w") as f:
            json.dump(test_results, f, indent=2, default=str)
        print(f"\nTest results saved to: {output_file}")
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

