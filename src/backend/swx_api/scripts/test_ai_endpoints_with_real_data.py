#!/usr/bin/env python3
"""
AI Endpoints Test with Real Database Data
------------------------------------------
Tests all AI endpoints with real data from the database.
Validates that endpoints use actual employee data and generate real predictions.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import httpx
import json

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from swx_api.core.database.db import AsyncSessionLocal
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.models.skill_models import EmployeeRecord
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 180.0  # Increased timeout for AI endpoints

# Test results
test_results = {
    "database_connection": {},
    "real_data_found": {},
    "endpoints": {},
    "azure_usage": {},
    "prediction_quality": {},
    "summary": {}
}


async def get_real_employees(session: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get real employee IDs and data from database, preferring non-test employees."""
    try:
        # First try to get non-TEST employees
        statement = select(EmployeeRecord).where(
            EmployeeRecord.employee_id.notlike('TEST%')
        ).limit(limit)
        result = await session.execute(statement)
        employees = result.scalars().all()
        
        # If no non-TEST employees found, get any employees
        if not employees:
            statement = select(EmployeeRecord).limit(limit)
            result = await session.execute(statement)
            employees = result.scalars().all()
        
        real_data = []
        for emp in employees:
            emp_dict = {
                "employee_id": emp.employee_id,
                "department": emp.department or "Unknown",
                "skills": emp.skills or [],
                "personal_number": getattr(emp, "personal_number", None),
            }
            real_data.append(emp_dict)
        
        logger.info(f"Found {len(real_data)} employees in database (first 3: {[e['employee_id'] for e in real_data[:3]]})")
        return real_data
    
    except Exception as e:
        logger.error(f"Failed to get real employees: {e}")
        return []


async def get_real_departments(session: AsyncSession) -> List[str]:
    """Get unique departments from database."""
    try:
        statement = select(EmployeeRecord.department).distinct()
        result = await session.execute(statement)
        departments = [row[0] for row in result.fetchall() if row[0]]
        logger.info(f"Found {len(departments)} unique departments: {departments[:5]}")
        return departments[:5]  # Return first 5
    except Exception as e:
        logger.error(f"Failed to get departments: {e}")
        return []


async def test_database_connection():
    """Test 1: Verify database connection and data availability."""
    print("\n" + "="*80)
    print("TEST 1: Database Connection & Real Data Availability")
    print("="*80)
    
    try:
        async with AsyncSessionLocal() as session:
            # Check employee count
            repo = EmployeeRepository()
            total_employees = await session.execute(select(EmployeeRecord))
            employee_list = total_employees.scalars().all()
            employee_count = len(employee_list)
            
            test_results["database_connection"] = {
                "status": "SUCCESS" if employee_count > 0 else "FAIL",
                "total_employees": employee_count,
                "message": f"Found {employee_count} employees in database"
            }
            
            print(f"✓ Database connection: OK")
            print(f"✓ Total employees in database: {employee_count}")
            
            if employee_count == 0:
                print("⚠ WARNING: No employees found in database!")
                print("  Run ingestion script first: docker compose exec backend python3 /app/swx_api/scripts/ingest_skoda_datasets.py")
                return False
            
            # Get sample employees
            employees = await get_real_employees(session, limit=5)
            departments = await get_real_departments(session)
            
            test_results["real_data_found"] = {
                "employees": len(employees),
                "sample_employee_ids": [e["employee_id"] for e in employees[:3]],
                "departments": departments,
                "status": "SUCCESS" if employees else "FAIL"
            }
            
            print(f"✓ Sample employees found: {len(employees)}")
            print(f"  Employee IDs: {', '.join([e['employee_id'] for e in employees[:3]])}")
            print(f"✓ Departments found: {', '.join(departments[:3])}")
            
            return True, employees, departments
    
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        test_results["database_connection"] = {
            "status": "FAIL",
            "error": str(e)
        }
        return False, [], []


async def test_endpoint_with_validation(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    payload: Optional[Dict] = None,
    expected_fields: List[str] = None,
    description: str = ""
) -> Dict[str, Any]:
    """Test an endpoint and validate response quality."""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status_code": None,
        "success": False,
        "azure_used": False,
        "has_predictions": False,
        "response_time": None,
        "error": None,
        "validation": {}
    }
    
    try:
        print(f"\n  Testing {method} {endpoint}...")
        if description:
            print(f"    {description}")
        
        start_time = datetime.now()
        
        if method == "GET":
            response = await client.get(f"{BASE_URL}{endpoint}", timeout=TIMEOUT)
        else:
            # Handle query params in endpoint URL for what-if
            if "?" in endpoint:
                url = f"{BASE_URL}{endpoint}"
                response = await client.post(
                    url,
                    json=payload or {},
                    timeout=TIMEOUT
                )
            else:
                response = await client.post(
                    f"{BASE_URL}{endpoint}",
                    json=payload or {},
                    timeout=TIMEOUT
                )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        result["status_code"] = response.status_code
        result["response_time"] = elapsed
        
        if response.status_code == 200:
            try:
                data = response.json()
                result["success"] = True
                
                # Check if Azure was used (not fallback)
                if isinstance(data, dict):
                    # Check nested data field
                    actual_data = data.get("data", data)
                    if isinstance(actual_data, dict):
                        ai_mode = actual_data.get("ai_mode", "unknown")
                        result["azure_used"] = ai_mode == "azure"
                        
                        # Validate response has meaningful content
                        if expected_fields:
                            missing_fields = []
                            has_content = True
                            
                            for field in expected_fields:
                                field_value = actual_data.get(field)
                                if field_value is None or field_value == "" or field_value == []:
                                    missing_fields.append(field)
                                    has_content = False
                                elif isinstance(field_value, str):
                                    # Check if it's not a fallback message
                                    if "unavailable" in field_value.lower() or "fallback" in field_value.lower():
                                        has_content = False
                            
                            result["has_predictions"] = has_content
                            result["validation"]["missing_fields"] = missing_fields
                            result["validation"]["has_content"] = has_content
                        
                        # Check for actual prediction content
                        summary = actual_data.get("summary", "") or ""
                        assistant = actual_data.get("assistant", "") or ""
                        plan_overview = actual_data.get("plan_overview", "") or ""
                        narrative = actual_data.get("narrative", "") or ""
                        
                        # Any meaningful content indicates predictions
                        meaningful_text = summary or assistant or plan_overview or narrative
                        if meaningful_text:
                            text_lower = str(meaningful_text).lower()
                            # Check if it's not a fallback message
                            if (len(meaningful_text) > 50 and 
                                "unavailable" not in text_lower and 
                                "fallback" not in text_lower and
                                "heuristic" not in text_lower and
                                "empty response" not in text_lower):
                                result["has_predictions"] = True
                        
                        # Also check for structured predictions (not empty lists)
                        if not result["has_predictions"]:
                            # Check for recommendations, courses, strengths, etc.
                            for field in ["recommendations", "courses", "strengths", "development_areas", "insights"]:
                                if field in actual_data:
                                    field_value = actual_data[field]
                                    if isinstance(field_value, list) and len(field_value) > 0:
                                        result["has_predictions"] = True
                                        break
                                    elif isinstance(field_value, dict) and len(field_value) > 0:
                                        result["has_predictions"] = True
                                        break
                        
                        # Log key fields for inspection
                        if "summary" in actual_data:
                            summary_preview = str(actual_data["summary"])[:100]
                            result["validation"]["summary_preview"] = summary_preview
                            print(f"    ✓ Status: 200, Time: {elapsed:.2f}s, Azure: {result['azure_used']}")
                            print(f"    Summary preview: {summary_preview}...")
                        else:
                            print(f"    ✓ Status: 200, Time: {elapsed:.2f}s, Azure: {result['azure_used']}")
                    else:
                        print(f"    ⚠ Status: 200, but unexpected response format")
                else:
                    print(f"    ⚠ Status: 200, but response is not a dictionary")
            
            except json.JSONDecodeError as e:
                result["error"] = f"Invalid JSON response: {e}"
                print(f"    ✗ Invalid JSON response")
        
        else:
            result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
            print(f"    ✗ Status: {response.status_code}")
            if response.status_code == 404:
                print(f"      Error: Endpoint not found")
            elif response.status_code == 422:
                print(f"      Error: Validation error")
            else:
                print(f"      Error: {response.text[:100]}")
    
    except httpx.TimeoutException:
        result["error"] = "Request timeout"
        print(f"    ✗ Timeout after {TIMEOUT}s")
    except Exception as e:
        result["error"] = str(e)
        print(f"    ✗ Error: {e}")
    
    return result


async def test_all_ai_endpoints(employees: List[Dict], departments: List[str]):
    """Test 2: Test all AI endpoints with real data."""
    print("\n" + "="*80)
    print("TEST 2: AI Endpoints with Real Database Data")
    print("="*80)
    
    if not employees:
        print("⚠ No employees available for testing")
        return
    
    if not departments:
        print("⚠ No departments available for testing")
        return
    
    # Get first REAL employee (not TEST123) with department and skills if possible
    real_employee = None
    for emp in employees:
        if (not emp["employee_id"].startswith("TEST") and 
            emp.get("department") != "Unknown" and 
            len(emp.get("skills", [])) > 0):
            real_employee = emp
            break
    
    # Fallback to employee with department (even if no skills)
    if not real_employee:
        for emp in employees:
            if (not emp["employee_id"].startswith("TEST") and 
                emp.get("department") != "Unknown"):
                real_employee = emp
                break
    
    # Final fallback to any non-TEST employee
    if not real_employee:
        for emp in employees:
            if not emp["employee_id"].startswith("TEST"):
                real_employee = emp
                break
    
    if not real_employee:
        real_employee = employees[0]  # Fallback to first employee
    
    test_employee = real_employee
    test_employee_id = test_employee["employee_id"]
    
    # Get real department from employee or use first available non-Unknown
    test_department = test_employee.get("department", "Unknown")
    if test_department == "Unknown" and departments:
        # Try to find a non-Unknown department
        for dept in departments:
            if dept != "Unknown":
                test_department = dept
                break
        if test_department == "Unknown":
            test_department = departments[0] if departments else "Unknown"
    
    print(f"\nUsing real data:")
    print(f"  Employee ID: {test_employee_id}")
    print(f"  Department: {test_department}")
    print(f"  Skills: {', '.join(test_employee.get('skills', [])[:3]) if test_employee.get('skills') else 'None'}")
    
    endpoints_to_test = []
    
    # 1. Employee Intel
    endpoints_to_test.append({
        "method": "GET",
        "endpoint": f"/api/ai/employee-intel/{test_employee_id}",
        "payload": None,
        "expected_fields": ["summary", "strengths", "development_areas", "readiness_score"],
        "description": f"Employee intelligence for {test_employee_id}"
    })
    
    # 2. Team Intel (skip if department is "Unknown" and we have better options)
    if test_department != "Unknown" or len(departments) <= 1:
        endpoints_to_test.append({
            "method": "GET",
            "endpoint": f"/api/ai/team-intel/{test_department}",
            "payload": None,
            "expected_fields": ["summary", "team_skills", "recommendations"],
            "description": f"Team intelligence for {test_department}"
        })
    
    # 3. Succession Intel (skip if department is "Unknown")
    if test_department != "Unknown":
        endpoints_to_test.append({
            "method": "GET",
            "endpoint": f"/api/ai/succession-intel/{test_department}",
            "payload": None,
            "expected_fields": ["summary", "succession_analysis"],
            "description": f"Succession planning for {test_department} (timeout: 120s)"
        })
    
    # 4. Career Chat
    endpoints_to_test.append({
        "method": "POST",
        "endpoint": "/api/ai/career-chat",
        "payload": {
            "employee_id": test_employee_id,
            "user_message": "What skills should I develop to advance in my career?",
            "skills": test_employee.get("skills", [])[:5] if test_employee.get("skills") else [],
            "department": test_employee.get("department", ""),
            "career_goals": "",
            "context": {}
        },
        "expected_fields": ["response", "suggestions"],
        "description": f"Career chat for {test_employee_id}"
    })
    
    # 5. Training Plan
    endpoints_to_test.append({
        "method": "POST",
        "endpoint": "/api/ai/training-plan",
        "payload": {
            "employee_id": test_employee_id,
            "desired_role": "Senior Analyst",
            "skills": test_employee.get("skills", [])[:3] if test_employee.get("skills") else ["leadership"],
            "gaps": []
        },
        "expected_fields": ["plan", "courses", "recommendations"],
        "description": f"Training plan for {test_employee_id}"
    })
    
    # 6. What-If Analysis (uses query params + body)
    endpoints_to_test.append({
        "method": "POST",
        "endpoint": f"/api/ai/what-if?scenario_type=add_skill&employee_id={test_employee_id}",
        "payload": {
            "skill": "Machine Learning"
        },
        "expected_fields": ["scenario", "impact", "predictions"],
        "description": f"What-if analysis for {test_employee_id}"
    })
    
    # 7. Compare Departments (if we have 2+ real departments)
    real_departments = [d for d in departments if d != "Unknown"]
    if len(real_departments) >= 2:
        endpoints_to_test.append({
            "method": "GET",
            "endpoint": f"/api/ai/compare/{real_departments[0]}/{real_departments[1]}",
            "payload": None,
            "expected_fields": ["comparison", "differences", "insights"],
            "description": f"Compare {real_departments[0]} vs {real_departments[1]}"
        })
    elif len(departments) >= 2:
        # Fallback to any 2 departments
        endpoints_to_test.append({
            "method": "GET",
            "endpoint": f"/api/ai/compare/{departments[0]}/{departments[1]}",
            "payload": None,
            "expected_fields": ["comparison", "differences", "insights"],
            "description": f"Compare {departments[0]} vs {departments[1]}"
        })
    
    # 8. Leadership Narrative
    # Check both /api/ai/leadership-narrative and /api/analytics/leadership-narrative
    if test_department != "Unknown":
        endpoints_to_test.append({
            "method": "GET",
            "endpoint": f"/api/ai/leadership-narrative/{test_department}",
            "payload": None,
            "expected_fields": ["narrative", "insights"],
            "description": f"Leadership narrative for {test_department} (timeout: 120s)"
        })
    
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        endpoint_results = []
        
        for endpoint_config in endpoints_to_test:
            result = await test_endpoint_with_validation(
                client,
                endpoint_config["method"],
                endpoint_config["endpoint"],
                endpoint_config.get("payload"),
                endpoint_config.get("expected_fields"),
                endpoint_config.get("description", "")
            )
            endpoint_results.append(result)
            test_results["endpoints"][endpoint_config["endpoint"]] = result
    
    # Summary
    successful = sum(1 for r in endpoint_results if r["success"])
    azure_used = sum(1 for r in endpoint_results if r["azure_used"])
    has_predictions = sum(1 for r in endpoint_results if r["has_predictions"])
    
    print(f"\n  Summary:")
    print(f"    Endpoints tested: {len(endpoint_results)}")
    print(f"    Successful (200): {successful}/{len(endpoint_results)}")
    print(f"    Using Azure: {azure_used}/{len(endpoint_results)}")
    print(f"    Has predictions: {has_predictions}/{len(endpoint_results)}")
    
    test_results["summary"]["endpoints_tested"] = len(endpoint_results)
    test_results["summary"]["successful"] = successful
    test_results["summary"]["azure_used"] = azure_used
    test_results["summary"]["has_predictions"] = has_predictions


async def validate_prediction_quality():
    """Test 3: Validate prediction quality."""
    print("\n" + "="*80)
    print("TEST 3: Prediction Quality Validation")
    print("="*80)
    
    quality_checks = {
        "azure_usage": 0,
        "fallback_detected": 0,
        "empty_responses": 0,
        "meaningful_content": 0
    }
    
    for endpoint, result in test_results["endpoints"].items():
        if result["success"]:
            if result["azure_used"]:
                quality_checks["azure_usage"] += 1
            else:
                quality_checks["fallback_detected"] += 1
            
            if result["has_predictions"]:
                quality_checks["meaningful_content"] += 1
            else:
                quality_checks["empty_responses"] += 1
    
    print(f"\n  Quality Checks:")
    print(f"    Using Azure OpenAI: {quality_checks['azure_usage']}")
    print(f"    Fallback detected: {quality_checks['fallback_detected']}")
    print(f"    Meaningful content: {quality_checks['meaningful_content']}")
    print(f"    Empty/minimal responses: {quality_checks['empty_responses']}")
    
    test_results["prediction_quality"] = quality_checks


async def generate_final_report():
    """Generate final test report."""
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    
    db_status = test_results["database_connection"].get("status", "UNKNOWN")
    employee_count = test_results["database_connection"].get("total_employees", 0)
    
    print(f"\n1. Database Connection: {db_status}")
    print(f"   Employees in database: {employee_count}")
    
    if test_results["real_data_found"]:
        print(f"\n2. Real Data Available:")
        print(f"   Sample employees: {test_results['real_data_found'].get('employees', 0)}")
        print(f"   Departments: {len(test_results['real_data_found'].get('departments', []))}")
    
    summary = test_results["summary"]
    print(f"\n3. Endpoint Tests:")
    print(f"   Endpoints tested: {summary.get('endpoints_tested', 0)}")
    print(f"   Successful: {summary.get('successful', 0)}/{summary.get('endpoints_tested', 0)}")
    print(f"   Using Azure: {summary.get('azure_used', 0)}/{summary.get('endpoints_tested', 0)}")
    print(f"   Has predictions: {summary.get('has_predictions', 0)}/{summary.get('endpoints_tested', 0)}")
    
    quality = test_results["prediction_quality"]
    print(f"\n4. Prediction Quality:")
    print(f"   Azure usage: {quality.get('azure_usage', 0)}")
    print(f"   Fallback detected: {quality.get('fallback_detected', 0)}")
    print(f"   Meaningful content: {quality.get('meaningful_content', 0)}")
    
    # Overall status
    all_successful = summary.get('successful', 0) == summary.get('endpoints_tested', 0)
    using_azure = quality.get('azure_usage', 0) > 0
    has_predictions = quality.get('meaningful_content', 0) > 0
    
    if all_successful and using_azure and has_predictions:
        print(f"\n✅ OVERALL STATUS: SUCCESS")
        print(f"   All endpoints working with real data")
        print(f"   Azure OpenAI being used for predictions")
        print(f"   Predictions contain meaningful content")
    elif all_successful:
        print(f"\n⚠️  OVERALL STATUS: PARTIAL SUCCESS")
        print(f"   Endpoints working but some issues detected:")
        if not using_azure:
            print(f"     - Azure not being used (fallback mode)")
        if not has_predictions:
            print(f"     - Responses lack meaningful predictions")
    else:
        print(f"\n❌ OVERALL STATUS: FAILURES DETECTED")
        print(f"   Some endpoints failed - check errors above")
    
    # Save results to file
    results_file = Path("ai_endpoints_test_results.json")
    with open(results_file, "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\n  Results saved to: {results_file}")


async def main():
    """Main test execution."""
    print("="*80)
    print("AI Endpoints Test with Real Database Data")
    print("="*80)
    print(f"\nTarget: {BASE_URL}")
    print(f"Timeout: {TIMEOUT}s per request")
    
    # Test 1: Database connection
    success, employees, departments = await test_database_connection()
    
    if not success or not employees:
        print("\n❌ Cannot proceed without database data")
        print("   Run ingestion first: docker compose exec backend python3 /app/swx_api/scripts/ingest_skoda_datasets.py")
        return
    
    # Test 2: AI endpoints with real data
    await test_all_ai_endpoints(employees, departments)
    
    # Test 3: Validate prediction quality
    await validate_prediction_quality()
    
    # Final report
    await generate_final_report()


if __name__ == "__main__":
    asyncio.run(main())

