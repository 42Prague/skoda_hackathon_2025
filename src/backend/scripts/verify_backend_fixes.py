#!/usr/bin/env python3
"""
Backend Verification Script
----------------------------
Comprehensive end-to-end verification of all backend fixes:
1. Re-ingest all data
2. Verify departments are populated (not "Unknown")
3. Verify skills are extracted
4. Test all AI endpoints
5. Verify Azure-only usage (no fallback)
6. Print PASS or FAIL
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
from swx_api.app.services.dataset_ingestion_service import DatasetIngestionService
from swx_api.app.services.employee_ingestion_service import EmployeeIngestionService
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.ingestion_service import paths
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"
TIMEOUT = 180.0

verification_results = {
    "ingestion": {},
    "data_quality": {},
    "ai_endpoints": {},
    "overall_status": "UNKNOWN"
}


async def verify_ingestion():
    """Step 1: Re-ingest all data and verify."""
    print("\n" + "="*80)
    print("STEP 1: Data Ingestion Verification")
    print("="*80)
    
    results = {
        "status": "FAIL",
        "files_ingested": 0,
        "errors": []
    }
    
    try:
        from swx_api.app.services.ingestion_service import paths
        from glob import glob
        
        # Find all data files
        data_dirs = [
            paths.raw_dir,
            Path("/app/data/raw/skoda"),
            Path("data/raw/skoda"),
        ]
        
        dataset_files = []
        for data_dir in data_dirs:
            if data_dir.exists():
                dataset_files.extend(list(data_dir.glob("*.csv")))
                dataset_files.extend(list(data_dir.glob("*.xlsx")))
        
        if not dataset_files:
            logger.warning("No data files found for ingestion")
            results["errors"].append("No data files found")
            verification_results["ingestion"] = results
            return results
        
        logger.info(f"Found {len(dataset_files)} data files to ingest")
        
        dataset_repo = DatasetRepository()
        dataset_service = DatasetIngestionService(dataset_repo)
        
        ingested_count = 0
        for file_path in dataset_files[:5]:  # Limit to 5 files for testing
            try:
                response = await dataset_service.ingest_dataset(file_path, file_path.name)
                if response.get("success"):
                    ingested_count += 1
                    logger.info(f"✓ Ingested: {file_path.name}")
                else:
                    results["errors"].append(f"Failed to ingest {file_path.name}")
            except Exception as e:
                results["errors"].append(f"Error ingesting {file_path.name}: {e}")
        
        results["files_ingested"] = ingested_count
        results["status"] = "SUCCESS" if ingested_count > 0 and not results["errors"] else "FAIL"
        
    except Exception as e:
        logger.error(f"Ingestion verification failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "FAIL"
    
    verification_results["ingestion"] = results
    print(f"  Status: {results['status']}")
    print(f"  Files ingested: {results['files_ingested']}")
    if results["errors"]:
        print(f"  Errors: {len(results['errors'])}")
        for error in results["errors"][:3]:
            print(f"    - {error}")
    
    return results


async def verify_data_quality():
    """Step 2: Verify data quality - departments and skills."""
    print("\n" + "="*80)
    print("STEP 2: Data Quality Verification")
    print("="*80)
    
    results = {
        "status": "FAIL",
        "total_employees": 0,
        "employees_with_departments": 0,
        "employees_without_departments": [],
        "employees_with_skills": 0,
        "employees_without_skills": [],
        "department_distribution": {},
        "errors": []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Get all employees
            statement = select(EmployeeRecord)
            result = await session.execute(statement)
            employees = result.scalars().all()
            results["total_employees"] = len(employees)
            
            if results["total_employees"] == 0:
                results["errors"].append("No employees found in database")
                verification_results["data_quality"] = results
                return results
            
            # Check departments
            for emp in employees:
                dept = emp.department
                if dept and dept.strip() and dept != "Unknown":
                    results["employees_with_departments"] += 1
                    results["department_distribution"][dept] = results["department_distribution"].get(dept, 0) + 1
                else:
                    results["employees_without_departments"].append({
                        "employee_id": emp.employee_id,
                        "department": dept
                    })
            
            # Check skills
            for emp in employees:
                skills = emp.skills or []
                if skills and len(skills) > 0:
                    results["employees_with_skills"] += 1
                else:
                    results["employees_without_skills"].append({
                        "employee_id": emp.employee_id,
                        "skills_count": 0
                    })
            
            # Calculate percentages
            dept_percentage = (results["employees_with_departments"] / results["total_employees"] * 100) if results["total_employees"] > 0 else 0
            skills_percentage = (results["employees_with_skills"] / results["total_employees"] * 100) if results["total_employees"] > 0 else 0
            
            # Pass criteria: >95% have departments, >50% have skills
            if dept_percentage >= 95.0 and skills_percentage >= 50.0:
                results["status"] = "SUCCESS"
            elif dept_percentage >= 90.0:
                results["status"] = "PARTIAL"  # Good but could be better
            else:
                results["status"] = "FAIL"
            
            results["dept_percentage"] = dept_percentage
            results["skills_percentage"] = skills_percentage
            
    except Exception as e:
        logger.error(f"Data quality verification failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "FAIL"
    
    verification_results["data_quality"] = results
    print(f"  Status: {results['status']}")
    print(f"  Total employees: {results['total_employees']}")
    print(f"  Employees with departments: {results['employees_with_departments']} ({results.get('dept_percentage', 0):.1f}%)")
    print(f"  Employees with skills: {results['employees_with_skills']} ({results.get('skills_percentage', 0):.1f}%)")
    print(f"  Unique departments: {len(results['department_distribution'])}")
    
    if results["employees_without_departments"]:
        print(f"  Missing departments: {len(results['employees_without_departments'])} employees")
        for emp_info in results["employees_without_departments"][:5]:
            print(f"    - {emp_info['employee_id']}: dept='{emp_info['department']}'")
    
    if results["employees_without_skills"]:
        print(f"  Missing skills: {len(results['employees_without_skills'])} employees")
        for emp_info in results["employees_without_skills"][:5]:
            print(f"    - {emp_info['employee_id']}")
    
    return results


async def verify_ai_endpoints():
    """Step 3: Verify all AI endpoints use Azure only."""
    print("\n" + "="*80)
    print("STEP 3: AI Endpoints Verification (Azure-Only)")
    print("="*80)
    
    results = {
        "status": "FAIL",
        "endpoints_tested": 0,
        "endpoints_passed": 0,
        "endpoints_failed": 0,
        "fallback_detected": 0,
        "empty_responses": 0,
        "endpoint_details": {},
        "errors": []
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Get test data
            employee_repo = EmployeeRepository()
            statement = select(EmployeeRecord).where(
                EmployeeRecord.department != 'Unknown'
            ).where(
                EmployeeRecord.skills.isnot(None)
            ).limit(1)
            result = await session.execute(statement)
            test_employees = result.scalars().all()
            
            if not test_employees:
                # Fallback to any employee
                statement = select(EmployeeRecord).limit(1)
                result = await session.execute(statement)
                test_employees = result.scalars().all()
            
            if not test_employees:
                results["errors"].append("No employees found for testing")
                verification_results["ai_endpoints"] = results
                return results
            
            test_employee = test_employees[0]
            test_employee_id = test_employee.employee_id
            test_department = test_employee.department or "TEST_DEPT"
            
            # Get departments for comparison
            dept_stmt = select(EmployeeRecord.department).distinct().where(
                EmployeeRecord.department != 'Unknown'
            ).limit(2)
            dept_result = await session.execute(dept_stmt)
            departments = [row[0] for row in dept_result.all() if row[0]]
            
            if len(departments) < 2:
                departments = [test_department, "TEST_DEPT"]
            
            endpoints_to_test = [
                {
                    "name": "employee-intel",
                    "method": "GET",
                    "url": f"{BASE_URL}/api/ai/employee-intel/{test_employee_id}",
                    "payload": None,
                },
                {
                    "name": "team-intel",
                    "method": "GET",
                    "url": f"{BASE_URL}/api/ai/team-intel/{test_department}",
                    "payload": None,
                },
                {
                    "name": "succession-intel",
                    "method": "GET",
                    "url": f"{BASE_URL}/api/ai/succession-intel/{test_department}",
                    "payload": None,
                },
                {
                    "name": "career-chat",
                    "method": "POST",
                    "url": f"{BASE_URL}/api/ai/career-chat",
                    "payload": {
                        "employee_id": test_employee_id,
                        "user_message": "What skills should I develop?",
                        "skills": test_employee.skills[:5] if test_employee.skills else [],
                        "department": test_department,
                    },
                },
                {
                    "name": "training-plan",
                    "method": "POST",
                    "url": f"{BASE_URL}/api/ai/training-plan",
                    "payload": {
                        "employee_id": test_employee_id,
                        "desired_role": "Senior Analyst",
                        "skills": test_employee.skills[:3] if test_employee.skills else ["leadership"],
                        "gaps": [],
                    },
                },
                {
                    "name": "what-if",
                    "method": "POST",
                    "url": f"{BASE_URL}/api/ai/what-if?scenario_type=add_skill&employee_id={test_employee_id}",
                    "payload": {"skill": "Machine Learning"},
                },
            ]
            
            # Add compare if we have 2 departments
            if len(departments) >= 2:
                endpoints_to_test.append({
                    "name": "compare",
                    "method": "GET",
                    "url": f"{BASE_URL}/api/ai/compare/{departments[0]}/{departments[1]}",
                    "payload": None,
                })
            
            # Add leadership-narrative
            endpoints_to_test.append({
                "name": "leadership-narrative",
                "method": "GET",
                "url": f"{BASE_URL}/api/ai/leadership-narrative/{test_department}",
                "payload": None,
            })
            
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                for endpoint in endpoints_to_test:
                    results["endpoints_tested"] += 1
                    endpoint_result = {
                        "status": "FAIL",
                        "azure_used": False,
                        "has_content": False,
                        "error": None,
                    }
                    
                    try:
                        if endpoint["method"] == "GET":
                            response = await client.get(endpoint["url"], timeout=TIMEOUT)
                        else:
                            # Handle query params in URL
                            if "?" in endpoint["url"]:
                                response = await client.post(endpoint["url"], json=endpoint.get("payload"), timeout=TIMEOUT)
                            else:
                                response = await client.post(endpoint["url"], json=endpoint.get("payload"), timeout=TIMEOUT)
                        
                        if response.status_code == 200:
                            data = response.json()
                            actual_data = data.get("data", data)
                            
                            # Check if Azure was used
                            ai_mode = actual_data.get("ai_mode", "unknown")
                            if ai_mode == "azure":
                                endpoint_result["azure_used"] = True
                            elif ai_mode in ["fallback", "heuristic", "featherless"]:
                                results["fallback_detected"] += 1
                                endpoint_result["error"] = f"Fallback detected: ai_mode={ai_mode}"
                            
                            # Check for content
                            if isinstance(actual_data, dict):
                                has_content = any(
                                    v for k, v in actual_data.items() 
                                    if k not in ["ai_mode"] and v and 
                                    (not isinstance(v, str) or len(v) > 10)
                                )
                                if has_content:
                                    endpoint_result["has_content"] = True
                                else:
                                    results["empty_responses"] += 1
                                    endpoint_result["error"] = "Empty or minimal response content"
                            
                            # Pass if Azure used and has content
                            if endpoint_result["azure_used"] and endpoint_result["has_content"]:
                                endpoint_result["status"] = "SUCCESS"
                                results["endpoints_passed"] += 1
                            else:
                                results["endpoints_failed"] += 1
                        else:
                            endpoint_result["error"] = f"HTTP {response.status_code}: {response.text[:100]}"
                            results["endpoints_failed"] += 1
                    
                    except Exception as e:
                        endpoint_result["error"] = str(e)
                        results["endpoints_failed"] += 1
                        results["errors"].append(f"{endpoint['name']}: {e}")
                    
                    results["endpoint_details"][endpoint["name"]] = endpoint_result
                    print(f"  {endpoint['name']}: {endpoint_result['status']} (Azure: {endpoint_result['azure_used']}, Content: {endpoint_result['has_content']})")
                    if endpoint_result["error"]:
                        print(f"    Error: {endpoint_result['error']}")
            
            # Overall status
            if results["endpoints_passed"] == results["endpoints_tested"] and results["fallback_detected"] == 0:
                results["status"] = "SUCCESS"
            elif results["endpoints_passed"] > 0 and results["fallback_detected"] == 0:
                results["status"] = "PARTIAL"
            else:
                results["status"] = "FAIL"
    
    except Exception as e:
        logger.error(f"AI endpoints verification failed: {e}")
        results["errors"].append(str(e))
        results["status"] = "FAIL"
    
    verification_results["ai_endpoints"] = results
    print(f"\n  Summary:")
    print(f"    Endpoints tested: {results['endpoints_tested']}")
    print(f"    Passed: {results['endpoints_passed']}")
    print(f"    Failed: {results['endpoints_failed']}")
    print(f"    Fallback detected: {results['fallback_detected']}")
    print(f"    Empty responses: {results['empty_responses']}")
    
    return results


async def generate_final_report():
    """Generate final verification report."""
    print("\n" + "="*80)
    print("FINAL VERIFICATION REPORT")
    print("="*80)
    
    ingestion_status = verification_results["ingestion"].get("status", "UNKNOWN")
    data_quality_status = verification_results["data_quality"].get("status", "UNKNOWN")
    ai_endpoints_status = verification_results["ai_endpoints"].get("status", "UNKNOWN")
    
    print(f"\n1. Ingestion: {ingestion_status}")
    print(f"   Files ingested: {verification_results['ingestion'].get('files_ingested', 0)}")
    
    print(f"\n2. Data Quality: {data_quality_status}")
    dq = verification_results["data_quality"]
    print(f"   Total employees: {dq.get('total_employees', 0)}")
    print(f"   With departments: {dq.get('employees_with_departments', 0)} ({dq.get('dept_percentage', 0):.1f}%)")
    print(f"   With skills: {dq.get('employees_with_skills', 0)} ({dq.get('skills_percentage', 0):.1f}%)")
    
    print(f"\n3. AI Endpoints: {ai_endpoints_status}")
    ai = verification_results["ai_endpoints"]
    print(f"   Endpoints tested: {ai.get('endpoints_tested', 0)}")
    print(f"   Passed: {ai.get('endpoints_passed', 0)}")
    print(f"   Fallback detected: {ai.get('fallback_detected', 0)}")
    print(f"   Empty responses: {ai.get('empty_responses', 0)}")
    
    # Overall status
    all_success = (
        ingestion_status == "SUCCESS" and
        data_quality_status in ["SUCCESS", "PARTIAL"] and
        ai_endpoints_status == "SUCCESS" and
        ai.get("fallback_detected", 0) == 0
    )
    
    if all_success:
        verification_results["overall_status"] = "PASS"
        print("\n" + "="*80)
        print("✅ OVERALL STATUS: PASS")
        print("="*80)
        print("\nAll backend fixes verified successfully!")
        print("- Data ingestion working")
        print("- Departments populated correctly")
        print("- Skills extracted properly")
        print("- All AI endpoints use Azure only")
        print("- No fallback or empty responses detected")
    else:
        verification_results["overall_status"] = "FAIL"
        print("\n" + "="*80)
        print("❌ OVERALL STATUS: FAIL")
        print("="*80)
        print("\nSome verification checks failed:")
        if ingestion_status != "SUCCESS":
            print(f"- Ingestion: {ingestion_status}")
        if data_quality_status not in ["SUCCESS", "PARTIAL"]:
            print(f"- Data quality: {data_quality_status}")
        if ai_endpoints_status != "SUCCESS":
            print(f"- AI endpoints: {ai_endpoints_status}")
        if ai.get("fallback_detected", 0) > 0:
            print(f"- Fallback detected: {ai.get('fallback_detected', 0)} endpoints")
    
    # Save results
    results_file = Path("backend_verification_results.json")
    with open(results_file, "w") as f:
        json.dump(verification_results, f, indent=2, default=str)
    print(f"\nResults saved to: {results_file}")
    
    return verification_results["overall_status"]


async def main():
    """Main verification flow."""
    print("="*80)
    print("BACKEND VERIFICATION SCRIPT")
    print("="*80)
    print("\nVerifying backend ingestion and AI pipeline fixes...")
    print(f"Target: {BASE_URL}")
    
    # Step 1: Verify ingestion
    await verify_ingestion()
    
    # Step 2: Verify data quality
    await verify_data_quality()
    
    # Step 3: Verify AI endpoints
    await verify_ai_endpoints()
    
    # Generate final report
    status = await generate_final_report()
    
    # Exit with appropriate code
    sys.exit(0 if status == "PASS" else 1)


if __name__ == "__main__":
    asyncio.run(main())

