#!/usr/bin/env python3
"""
Re-ingest All Data with Fixed Mapping
--------------------------------------
Clears existing employee data and re-ingests everything with correct mapping.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from swx_api.core.database.db import AsyncSessionLocal
from swx_api.app.services.ingestion_service import paths
from swx_api.app.services.dataset_ingestion_service import DatasetIngestionService
from swx_api.app.services.employee_ingestion_service import EmployeeIngestionService
from swx_api.app.repositories.dataset_repository import DatasetRepository
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.models.skill_models import EmployeeRecord, LearningHistory, DatasetRecord
from swx_api.app.models.skoda_models import QualificationRecord, OrgHierarchyRecord, HistoricalEmployeeSnapshot
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def clear_existing_data(session: AsyncSession):
    """Clear existing employee and related data."""
    print("\n" + "="*80)
    print("CLEARING EXISTING DATA")
    print("="*80)
    
    try:
        # Count before deletion
        emp_stmt = select(EmployeeRecord)
        result = await session.execute(emp_stmt)
        employees_before = result.scalars().all()
        emp_count = len(employees_before)
        
        print(f"  Found {emp_count} existing employees")
        print(f"  Clearing employee data...")
        
        # Delete in dependency order
        # 1. Learning history (depends on employees)
        lh_delete = delete(LearningHistory)
        await session.execute(lh_delete)
        print(f"  ✓ Cleared learning history")
        
        # 2. Qualifications (depends on employees)
        qual_delete = delete(QualificationRecord)
        await session.execute(qual_delete)
        print(f"  ✓ Cleared qualifications")
        
        # 3. Org hierarchy (depends on employees)
        org_delete = delete(OrgHierarchyRecord)
        await session.execute(org_delete)
        print(f"  ✓ Cleared org hierarchy")
        
        # 4. Historical snapshots (depends on employees)
        hist_delete = delete(HistoricalEmployeeSnapshot)
        await session.execute(hist_delete)
        print(f"  ✓ Cleared historical snapshots")
        
        # 5. Employees (last)
        emp_delete = delete(EmployeeRecord)
        await session.execute(emp_delete)
        print(f"  ✓ Cleared employees")
        
        # Commit deletions
        await session.commit()
        print(f"\n  ✅ Cleared {emp_count} employees and related data")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to clear existing data: {e}")
        await session.rollback()
        return False


async def discover_and_ingest_datasets():
    """Discover all datasets and ingest them in correct order."""
    print("\n" + "="*80)
    print("DISCOVERING AND INGESTING DATASETS")
    print("="*80)
    
    results = {
        "files_discovered": 0,
        "files_ingested": 0,
        "employees_loaded": 0,
        "errors": []
    }
    
    try:
        # Initialize services
        dataset_repo = DatasetRepository()
        employee_repo = EmployeeRepository()
        dataset_service = DatasetIngestionService(dataset_repo)
        employee_service = EmployeeIngestionService(employee_repo)
        
        # Discover files
        from swx_api.app.services.ingestion_service import paths
        from glob import glob
        
        # Find all data files
        data_dirs = [
            paths.raw_dir,
            Path("/app/data/raw/skoda"),
            Path("/app/data/raw"),
            Path("data/raw/skoda"),
        ]
        
        dataset_files = []
        for data_dir in data_dirs:
            if data_dir and data_dir.exists():
                dataset_files.extend(list(data_dir.glob("*.csv")))
                dataset_files.extend(list(data_dir.glob("*.xlsx")))
                dataset_files.extend(list(data_dir.glob("*.xls")))
        
        if not dataset_files:
            print(f"  ⚠ No data files found in: {data_dirs}")
            results["errors"].append("No data files found")
            return results
        
        results["files_discovered"] = len(dataset_files)
        print(f"\n  Found {len(dataset_files)} data files")
        
        # Sort by dependency order
        def infer_purpose(file_path: Path) -> str:
            """Infer dataset purpose from filename."""
            name_lower = file_path.stem.lower()
            
            if any(kw in name_lower for kw in ["org", "hierarchy", "sa_org"]):
                return "org_hierarchy"
            elif any(kw in name_lower for kw in ["skill", "kompetence", "mapping"]):
                return "skill_mapping"
            elif any(kw in name_lower for kw in ["qualification", "vzd", "kval"]):
                return "qualifications"
            elif any(kw in name_lower for kw in ["degreed", "training", "course", "participation", "zhrpd_vzd_sta_007"]):
                return "training_history"
            elif any(kw in name_lower for kw in ["employee", "pers", "hr", "people", "erp", "start_month"]):
                return "employee_data"
            else:
                return "unknown"
        
        dependency_order = {
            "org_hierarchy": 1,
            "skill_mapping": 2,
            "qualifications": 3,
            "training_history": 4,
            "employee_data": 5,
            "unknown": 99
        }
        
        # Group files by purpose
        files_by_purpose = {}
        for file_path in dataset_files:
            purpose = infer_purpose(file_path)
            files_by_purpose.setdefault(purpose, []).append(file_path)
        
        # Print discovery results
        for purpose in sorted(files_by_purpose.keys(), key=lambda p: dependency_order.get(p, 99)):
            files = files_by_purpose[purpose]
            print(f"  {purpose}: {len(files)} files")
            for f in files[:3]:
                print(f"    - {f.name}")
            if len(files) > 3:
                print(f"    ... and {len(files) - 3} more")
        
        # Ingest in dependency order
        async with AsyncSessionLocal() as session:
            for purpose in sorted(files_by_purpose.keys(), key=lambda p: dependency_order.get(p, 99)):
                files = files_by_purpose[purpose]
                
                print(f"\n  Ingesting {purpose} files ({len(files)} files)...")
                
                for file_path in files:
                    try:
                        # Step 1: Ingest dataset
                        response = await dataset_service.ingest_file(
                            session,
                            str(file_path),
                            file_path.name
                        )
                        
                        # Extract dataset_id from response
                        dataset_id = response.get("dataset_id") or file_path.stem
                        normalized_path = response.get("normalized_path", "")
                        results["files_ingested"] += 1
                        print(f"    ✓ Ingested: {file_path.name}")
                        
                        # Step 2: Load employees if this is employee data
                        if purpose == "employee_data":
                            try:
                                # Use dataset_id or filename stem
                                dataset_name_for_loading = dataset_id or file_path.stem
                                
                                # If normalized path exists, use its stem
                                if normalized_path and Path(normalized_path).exists():
                                    dataset_name_for_loading = Path(normalized_path).stem
                                
                                load_result = await employee_service.load_employees_from_dataset(
                                    session=session,
                                    dataset_id=dataset_name_for_loading,
                                    update_existing=True,
                                    use_skoda_adapter=True
                                )
                                employees_loaded = load_result.get("created", 0) + load_result.get("updated", 0)
                                results["employees_loaded"] += employees_loaded
                                print(f"      ✓ Loaded {employees_loaded} employees")
                            except Exception as emp_exc:
                                logger.error(f"Failed to load employees from {file_path.name}: {emp_exc}")
                                results["errors"].append(f"Failed to load employees from {file_path.name}: {emp_exc}")
                                await session.rollback()
                        
                    except Exception as e:
                        logger.error(f"Failed to ingest {file_path.name}: {e}", exc_info=True)
                        results["errors"].append(f"Error ingesting {file_path.name}: {e}")
                        continue
                
                # Commit after each purpose group
                try:
                    await session.commit()
                except Exception as commit_exc:
                    logger.error(f"Failed to commit after {purpose}: {commit_exc}")
                    await session.rollback()
        
        print(f"\n  ✅ Ingestion complete:")
        print(f"     Files ingested: {results['files_ingested']}/{results['files_discovered']}")
        print(f"     Employees loaded: {results['employees_loaded']}")
        if results["errors"]:
            print(f"     Errors: {len(results['errors'])}")
            for error in results["errors"][:5]:
                print(f"       - {error}")
        
    except Exception as e:
        logger.error(f"Dataset discovery/ingestion failed: {e}", exc_info=True)
        results["errors"].append(str(e))
    
    return results


async def verify_ingestion_results():
    """Verify the re-ingested data."""
    print("\n" + "="*80)
    print("VERIFYING INGESTION RESULTS")
    print("="*80)
    
    async with AsyncSessionLocal() as session:
        # Count employees
        emp_stmt = select(EmployeeRecord)
        result = await session.execute(emp_stmt)
        employees = result.scalars().all()
        total_count = len(employees)
        
        print(f"\n  Total employees: {total_count}")
        
        if total_count == 0:
            print(f"  ⚠ No employees found after ingestion")
            return {"status": "FAIL", "total": 0, "with_depts": 0, "with_skills": 0}
        
        # Check departments
        employees_with_depts = 0
        employees_without_depts = []
        department_distribution = {}
        
        for emp in employees:
            dept = emp.department
            if dept and dept.strip() and dept != "Unknown":
                employees_with_depts += 1
                department_distribution[dept] = department_distribution.get(dept, 0) + 1
            else:
                employees_without_depts.append(emp.employee_id)
        
        dept_percentage = (employees_with_depts / total_count * 100) if total_count > 0 else 0
        
        # Check skills
        employees_with_skills = 0
        employees_without_skills = []
        
        for emp in employees:
            skills = emp.skills or []
            if skills and len(skills) > 0:
                employees_with_skills += 1
            else:
                employees_without_skills.append(emp.employee_id)
        
        skills_percentage = (employees_with_skills / total_count * 100) if total_count > 0 else 0
        
        print(f"\n  Departments:")
        print(f"    Employees with departments: {employees_with_depts}/{total_count} ({dept_percentage:.1f}%)")
        print(f"    Unique departments: {len(department_distribution)}")
        if department_distribution:
            print(f"    Top departments:")
            for dept, count in sorted(department_distribution.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"      - {dept}: {count} employees")
        
        if employees_without_depts:
            print(f"    Missing departments: {len(employees_without_depts)} employees")
            for emp_id in employees_without_depts[:5]:
                print(f"      - {emp_id}")
        
        print(f"\n  Skills:")
        print(f"    Employees with skills: {employees_with_skills}/{total_count} ({skills_percentage:.1f}%)")
        
        if employees_without_skills:
            print(f"    Missing skills: {len(employees_without_skills)} employees")
            for emp_id in employees_without_skills[:5]:
                print(f"      - {emp_id}")
        
        # Sample employees
        print(f"\n  Sample employees (first 5):")
        for emp in employees[:5]:
            skill_count = len(emp.skills) if emp.skills else 0
            print(f"    - {emp.employee_id}: dept='{emp.department}', skills={skill_count}")
        
        # Status
        if dept_percentage >= 95.0 and skills_percentage >= 50.0:
            status = "SUCCESS"
        elif dept_percentage >= 90.0:
            status = "PARTIAL"
        else:
            status = "FAIL"
        
        print(f"\n  ✅ Verification Status: {status}")
        
        return {
            "status": status,
            "total": total_count,
            "with_depts": employees_with_depts,
            "dept_percentage": dept_percentage,
            "with_skills": employees_with_skills,
            "skills_percentage": skills_percentage,
            "department_distribution": dict(sorted(department_distribution.items(), key=lambda x: x[1], reverse=True)[:10])
        }


async def main():
    """Main re-ingestion flow."""
    print("="*80)
    print("RE-INGEST ALL DATA WITH FIXED MAPPING")
    print("="*80)
    print("\nThis will:")
    print("1. Clear existing employee data")
    print("2. Discover all data files")
    print("3. Ingest datasets in dependency order")
    print("4. Load employees with correct mapping")
    print("5. Verify results")
    print("\nStarting in 3 seconds...")
    
    import time
    time.sleep(3)
    
    # Step 1: Clear existing data
    async with AsyncSessionLocal() as session:
        cleared = await clear_existing_data(session)
        if not cleared:
            print("\n❌ Failed to clear existing data. Aborting.")
            return
    
    # Step 2: Discover and ingest all datasets
    ingest_results = await discover_and_ingest_datasets()
    
    # Step 3: Verify results
    verification = await verify_ingestion_results()
    
    # Final summary
    print("\n" + "="*80)
    print("RE-INGESTION SUMMARY")
    print("="*80)
    
    print(f"\n1. Data Clearing: ✅ Complete")
    print(f"\n2. Dataset Ingestion:")
    print(f"   Files discovered: {ingest_results['files_discovered']}")
    print(f"   Files ingested: {ingest_results['files_ingested']}")
    print(f"   Employees loaded: {ingest_results['employees_loaded']}")
    if ingest_results["errors"]:
        print(f"   Errors: {len(ingest_results['errors'])}")
    
    print(f"\n3. Data Quality:")
    print(f"   Total employees: {verification['total']}")
    print(f"   With departments: {verification['with_depts']} ({verification.get('dept_percentage', 0):.1f}%)")
    print(f"   With skills: {verification['with_skills']} ({verification.get('skills_percentage', 0):.1f}%)")
    
    if verification["status"] == "SUCCESS":
        print(f"\n✅ RE-INGESTION SUCCESSFUL")
        print(f"   All data re-ingested with correct mapping")
        print(f"   Departments and skills extracted properly")
    elif verification["status"] == "PARTIAL":
        print(f"\n⚠️  RE-INGESTION PARTIAL SUCCESS")
        print(f"   Most data correct, but some issues remain")
    else:
        print(f"\n❌ RE-INGESTION FAILED")
        print(f"   Data quality targets not met")
        print(f"   Check errors above and fix extraction logic")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())

