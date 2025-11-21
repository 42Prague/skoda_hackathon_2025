"""
Async Employee Ingestion Service
---------------------------------
Service layer for loading employees from datasets into the database.
Uses async repositories for all DB operations.
Supports Škoda dataset format.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import anyio
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from swx_api.app.models.skill_models import EmployeeRecord, LearningHistory
from swx_api.app.models.skoda_models import (
    QualificationRecord,
    OrgHierarchyRecord,
    HistoricalEmployeeSnapshot
)
from swx_api.app.repositories.employee_repository import EmployeeRepository
from swx_api.app.services.ingestion_service import (
    load_employees_from_dataset as load_employees_from_dataset_sync,
    paths,
    detect_skoda_schema
)
from swx_api.app.services.skoda_data_adapter import SkodaDataAdapter
from swx_api.app.services.multilingual_normalization_service import remove_diacritics
from swx_api.app.services.historical_data_loader import HistoricalDataLoader
from swx_api.core.middleware.logging_middleware import logger


class EmployeeIngestionService:
    """Async service for ingesting employees from datasets."""
    
    def __init__(self, employee_repo: EmployeeRepository):
        """
        Initialize service with employee repository.
        
        Args:
            employee_repo: Employee repository instance
        """
        self.employee_repo = employee_repo
        self.skoda_adapter = SkodaDataAdapter()
        self.historical_loader = HistoricalDataLoader()
    
    async def load_employees_from_dataset(
        self,
        session: AsyncSession,
        dataset_id: str,
        employee_id_column: str = "employee_id",
        department_column: str = "department",
        skills_column: Optional[str] = None,
        update_existing: bool = True,
        use_skoda_adapter: Optional[bool] = None
    ) -> Dict[str, int]:
        """
        Load employee records from an ingested dataset into the database.
        
        Args:
            session: Async database session
            dataset_id: Dataset ID (filename without extension)
            employee_id_column: Column name for employee ID (ignored if Škoda format)
            department_column: Column name for department (ignored if Škoda format)
            skills_column: Optional column name for skills (ignored if Škoda format)
            update_existing: If True, update existing employee records; if False, skip them
            use_skoda_adapter: Force use of Škoda adapter (None = auto-detect)
        """
        # Find dataset file
        dataset_path = paths.normalized_dir / f"{dataset_id}.csv"
        if not dataset_path.exists():
            datasets = list(paths.normalized_dir.glob(f"{dataset_id}.*"))
            if datasets:
                dataset_path = datasets[0]
            else:
                raise ValueError(f"Dataset not found: {dataset_id}")
        
        # Detect Škoda format
        import pandas as pd
        df = pd.read_csv(dataset_path, encoding="utf-8-sig", nrows=1)
        is_skoda = use_skoda_adapter if use_skoda_adapter is not None else detect_skoda_schema(df)
        
        # Load employees from dataset
        supplemental_config: Dict[str, Any] = {}
        if is_skoda:
            supplemental_config = self._build_supplemental_config()
        
        employees = await anyio.to_thread.run_sync(
            load_employees_from_dataset_sync,
            dataset_path,
            employee_id_column,
            department_column,
            skills_column,
            is_skoda,
            supplemental_config,
        )
        
        if not employees:
            raise ValueError("No employees found in dataset")
        
        # Load into database using async repository
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for emp_data in employees:
            employee_id = emp_data.get("employee_id") or emp_data.get("personal_number")
            if not employee_id:
                continue
            
            # Check if employee exists
            existing = await self.employee_repo.get_by_employee_id(session, employee_id)
            
            if existing:
                if update_existing:
                    # Update existing record with Škoda fields
                    existing.department = emp_data.get("department", existing.department)
                    existing.skills = emp_data.get("skills", existing.skills)
                    # Use meta_data (the actual field) instead of metadata (the alias)
                    if "metadata" in emp_data:
                        existing.meta_data = emp_data.get("metadata", existing.meta_data or {})
                    
                    if is_skoda:
                        self._apply_skoda_fields(existing, emp_data)
                    
                    existing.updated_at = datetime.utcnow()  # Timezone-naive for TIMESTAMP WITHOUT TIME ZONE
                    await self.employee_repo.update(session, existing)
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Create new record
                # Use meta_data (the actual field) instead of metadata (the alias)
                employee_record = EmployeeRecord(
                    employee_id=employee_id,
                    department=emp_data.get("department", "Unknown"),
                    skills=emp_data.get("skills"),
                    meta_data=emp_data.get("metadata", {}),
                )
                
                if is_skoda:
                    self._apply_skoda_fields(employee_record, emp_data)
                
                await self.employee_repo.create(session, employee_record)
                created_count += 1
            
            # Save qualifications if Škoda format
            if is_skoda and emp_data.get("qualifications"):
                await self._save_qualifications(session, employee_id, emp_data.get("qualifications", []))
            
            # Save org hierarchy if Škoda format
            if is_skoda and emp_data.get("metadata", {}).get("org_hierarchy"):
                await self._save_org_hierarchy(session, employee_id, emp_data.get("metadata", {}).get("org_hierarchy", {}))
            
            # Save learning history if present
            if emp_data.get("course_history"):
                await self._save_learning_history(session, employee_id, emp_data.get("course_history", []))
        
        await session.commit()
        
        return {
            "total_loaded": len(employees),
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
        }
    
    async def _save_qualifications(
        self,
        session: AsyncSession,
        employee_id: str,
        qualifications: List[Dict[str, Any]]
    ):
        """Save qualification records."""
        for qual_data in qualifications:
            try:
                qual_record = QualificationRecord(
                    employee_id=employee_id,
                    qualification_id=qual_data.get("qualification_id", ""),
                    qualification_name_cz=qual_data.get("qualification_name_cz", ""),
                    qualification_name_en=qual_data.get("qualification_name_en", ""),
                    mandatory=qual_data.get("mandatory", False),
                    obtained_date=qual_data.get("obtained_date"),
                    expiry_date=qual_data.get("expiry_date"),
                    status=qual_data.get("status", "active"),
                )
                session.add(qual_record)
            except Exception as e:
                logger.warning(f"Failed to save qualification: {e}")
                continue
    
    async def _save_learning_history(
        self,
        session: AsyncSession,
        employee_id: str,
        course_history: List[Dict[str, Any]]
    ):
        """Persist learning history derived from Degreed/participation feeds."""
        seen: set[tuple[str, Optional[str]]] = set()
        
        for course in course_history:
            course_name = course.get("course_name") or course.get("Title")
            if not course_name:
                continue
            content_id = str(course.get("course_id") or course.get("Content ID") or "")
            key = (content_id or course_name, course.get("end_date"))
            if key in seen:
                continue
            seen.add(key)
            
            start_dt = self._parse_optional_datetime(course.get("start_date"))
            end_dt = self._parse_optional_datetime(course.get("end_date"))
            hours = course.get("hours")
            if hours is None:
                verified_minutes = course.get("verified_minutes")
                estimated_minutes = course.get("estimated_minutes")
                minutes_source = verified_minutes or estimated_minutes
                hours = round(float(minutes_source) / 60.0, 2) if minutes_source else None
            
            try:
                learning_record = LearningHistory(
                    employee_id=employee_id,
                    course_name=course_name,
                    provider=course.get("provider") or course.get("Content Provider"),
                    course_type=course.get("course_type") or course.get("Type"),
                    content_id=content_id or None,
                    content_url=course.get("content_url") or course.get("Content URL"),
                    start_date=start_dt,
                    end_date=end_dt,
                    hours=hours,
                    verified_minutes=course.get("verified_minutes"),
                    estimated_minutes=course.get("estimated_minutes"),
                    verified=course.get("verified"),
                    completion_points=course.get("completion_points"),
                    user_rating=course.get("user_rating"),
                    completion_status=course.get("completion_status", "completed"),
                    skills_covered=course.get("skills_covered"),
                    certificate_url=course.get("certificate_url"),
                )
                session.add(learning_record)
            except Exception as exc:
                logger.warning(f"Failed to save learning history for {employee_id}: {exc}")
                continue

    def _apply_skoda_fields(self, record: EmployeeRecord, data: Dict[str, Any]):
        """Copy Škoda-specific fields from adapter output to SQLModel instance."""
        record.personal_number = data.get("personal_number")
        record.persstat_start_month_abc = data.get("persstat_start_month_abc")
        record.pers_organization_branch = data.get("pers_organization_branch")
        record.pers_profession_id = data.get("pers_profession_id")
        record.pers_profession_name = data.get("pers_profession_name")
        record.pers_job_family_id = data.get("pers_job_family_id")
        record.s1_org_hierarchy = data.get("s1_org_hierarchy")
        record.s2_org_hierarchy = data.get("s2_org_hierarchy")
        record.s3_org_hierarchy = data.get("s3_org_hierarchy")
        record.s4_org_hierarchy = data.get("s4_org_hierarchy")
        record.ob_codes = data.get("ob_codes")
        record.education_branch_id = data.get("education_branch_id")
        record.education_branch_name = data.get("education_branch_name")
        record.education_branch_group_id = data.get("education_branch_group_id")
        record.education_branch_group_name = data.get("education_branch_group_name")
        record.education_category_id = data.get("education_category_id")
        record.education_category_name = data.get("education_category_name")
        record.field_of_study_id = data.get("field_of_study_id")
        record.field_of_study_name = data.get("field_of_study_name")
        record.field_of_study_code = data.get("field_of_study_code")
        record.coordinator_group_id = data.get("coordinator_group_id")
        record.planned_profession_id = data.get("planned_profession_id")
        record.planned_profession_name = data.get("planned_profession_name")
        record.planned_position_id = data.get("planned_position_id")
        record.planned_position_name = data.get("planned_position_name")
        record.hr_contact_name = data.get("hr_contact_name")

    def _build_supplemental_config(self) -> Dict[str, Any]:
        """Load supplemental Škoda datasets ingested separately."""
        config: Dict[str, Any] = {}
        
        degreed_df = self._load_dataframe(["Degreed", "degreed"])
        if degreed_df is not None:
            config["degreed_records"] = self._build_degreed_records(degreed_df)
        
        skill_mapping_df = self._load_dataframe(["Skill_mapping", "skill_mapping"])
        if skill_mapping_df is not None:
            skill_map, object_map = self._build_skill_mapping(skill_mapping_df)
            if skill_map:
                config["skill_mapping"] = skill_map
            if object_map:
                config["object_mapping"] = object_map
        
        org_lookup_df = self._load_dataframe(["RLS.sa_org_hierarchy", "sa_org_hierarchy"])
        if org_lookup_df is not None:
            org_lookup = self._build_org_hierarchy_lookup(org_lookup_df)
            if org_lookup:
                config["org_hierarchy_lookup"] = org_lookup
        
        qualification_events_df = self._load_dataframe(["ZHRPD_VZD_STA_016_RE_RHRHAZ00", "ZHRPD_VZD_STA_016"])
        qualification_catalog_df = self._load_dataframe(["ZPE_KOM_KVAL"])
        if qualification_events_df is not None:
            config["external_qualifications"] = self._build_external_qualifications(
                qualification_events_df,
                qualification_catalog_df
            )
        
        course_participation_df = self._load_dataframe(["ZHRPD_VZD_STA_007"])
        if course_participation_df is not None:
            participation_records = self._build_course_participation_records(
                course_participation_df,
                config.get("object_mapping", {})
            )
            if participation_records:
                degreed_records = config.setdefault("degreed_records", {})
                for employee_id, entries in participation_records.items():
                    degreed_records.setdefault(employee_id, []).extend(entries)
        
        return config

    def _find_dataset_file(self, patterns: List[str]) -> Optional[Path]:
        """Locate normalized dataset file by trying multiple naming conventions."""
        for pattern in patterns:
            base_name = pattern.strip()
            candidates = [
                paths.normalized_dir / f"{base_name}.csv",
                paths.normalized_dir / f"{base_name}.xlsx",
                paths.normalized_dir / base_name,
            ]
            for candidate in candidates:
                if candidate.exists():
                    return candidate
        
        for pattern in patterns:
            matches = list(paths.normalized_dir.glob(f"*{pattern}*.csv"))
            if matches:
                return matches[0]
        return None

    def _load_dataframe(self, patterns: List[str]) -> Optional[pd.DataFrame]:
        """Load normalized CSV/XLSX if present."""
        file_path = self._find_dataset_file(patterns)
        if not file_path:
            return None
        try:
            if file_path.suffix.lower() == ".xlsx":
                return pd.read_excel(file_path)
            return pd.read_csv(file_path, encoding="utf-8-sig")
        except Exception as exc:
            logger.warning(f"Failed to load supplemental dataset {file_path}: {exc}")
            return None

    def _build_degreed_records(self, df: pd.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
        """Group Degreed rows by employee ID."""
        records: Dict[str, List[Dict[str, Any]]] = {}
        for _, row in df.iterrows():
            employee_id = str(row.get("Employee ID") or row.get("employee_id") or "").strip()
            if not employee_id:
                continue
            row_dict = row.to_dict()
            records.setdefault(employee_id, []).append(row_dict)
        return records

    def _build_skill_mapping(
        self,
        df: pd.DataFrame
    ) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
        """Build skill mapping and object metadata dictionaries."""
        skill_mapping: Dict[str, str] = {}
        object_mapping: Dict[str, Dict[str, Any]] = {}
        
        for _, row in df.iterrows():
            skill_name = str(row.get("Skill v EN") or row.get("skill_en") or "").strip()
            skill_id = str(row.get("ID skillu") or row.get("skill_id") or "").strip()
            if skill_name and skill_id:
                skill_mapping[skill_name] = skill_id
            
            object_id = str(row.get("ID objektu") or row.get("IDOBJ") or "").strip()
            if object_id:
                object_mapping[object_id] = {
                    "object_short": row.get("Zkratka objektu"),
                    "object_name": row.get("Oznaceni objektu") or row.get("Označení objektu"),
                    "catalog_code": row.get("Katalog"),
                    "topic": row.get("Tema") or row.get("Téma"),
                    "group": row.get("Skupina"),
                    "skill_id": skill_id,
                    "skill_name_en": skill_name,
                    "valid_from": row.get("Pocat.datum"),
                    "valid_to": row.get("Koncove datum"),
                }
        return skill_mapping, object_mapping

    def _build_org_hierarchy_lookup(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Create lookup for org hierarchy objid metadata."""
        lookup: Dict[str, Dict[str, Any]] = {}
        for _, row in df.iterrows():
            obj_id = str(row.get("objid") or row.get("OBJID") or row.get("sa_org_hierarchy.objid") or "").strip()
            if not obj_id:
                continue
            lookup[obj_id] = {
                "parent_node_id": str(row.get("paren") or row.get("PAREN") or "").strip() or None,
                "short_code": row.get("short") or row.get("SHORT"),
                "name_cz": row.get("stxtc") or row.get("STXTC"),
                "name_en": row.get("stxtd") or row.get("STXTD"),
                "description": row.get("stxte") or row.get("STXTE"),
            }
        return lookup

    def _build_external_qualifications(
        self,
        qualifications_df: pd.DataFrame,
        fm_catalog_df: Optional[pd.DataFrame],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Map qualification events per employee."""
        fm_lookup: Dict[str, str] = {}
        if fm_catalog_df is not None:
            for _, row in fm_catalog_df.iterrows():
                qual_name = str(row.get("Kvalifikace") or "").strip()
                fm_number = str(row.get("Cislo FM") or row.get("Číslo FM") or "").strip()
                if qual_name and fm_number:
                    fm_lookup[qual_name.lower()] = fm_number
        
        qualifications: Dict[str, List[Dict[str, Any]]] = {}
        for _, row in qualifications_df.iterrows():
            employee_id = str(row.get("ID P") or row.get("ID_P") or "").strip()
            if not employee_id:
                continue
            qualification_name = str(row.get("Nazev Q") or row.get("Název Q") or "").strip()
            qualification_id = str(row.get("ID Q") or row.get("ID_Q") or "").strip() or f"QUAL_{qualification_name}"
            fm_number = fm_lookup.get(qualification_name.lower())
            
            record = {
                "qualification_id": qualification_id,
                "qualification_name_cz": qualification_name,
                "qualification_name_en": remove_diacritics(qualification_name) if qualification_name else "",
                "mandatory": False,
                "obtained_date": self._parse_optional_datetime(row.get("Pocat.datum") or row.get("Počát.datum")),
                "expiry_date": self._parse_optional_datetime(row.get("Koncove datum") or row.get("Koncové datum")),
                "status": "active",
                "fm_number": fm_number,
            }
            qualifications.setdefault(employee_id, []).append(record)
        return qualifications

    def _build_course_participation_records(
        self,
        df: pd.DataFrame,
        object_mapping: Dict[str, Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Convert course participation spreadsheet into Degreed-style records."""
        records: Dict[str, List[Dict[str, Any]]] = {}
        for _, row in df.iterrows():
            employee_id = str(row.get("ID ucastnika") or row.get("ID účastníka") or "").strip()
            if not employee_id:
                continue
            object_id = str(row.get("IDOBJ") or row.get("ID obj") or "").strip()
            object_meta = object_mapping.get(object_id, {})
            course_name = object_meta.get("object_name") or row.get("Oznaceni typu akce") or row.get("Označení typu akce")
            
            record = {
                "Employee ID": employee_id,
                "Content ID": object_id,
                "Title": course_name,
                "Content": course_name,
                "Type": row.get("Typ akce") or object_meta.get("group"),
                "Content Provider": object_meta.get("catalog_code"),
                "Completion is Verified": "Y",
                "Completion User Rating": None,
                "Completion Points": None,
                "Content URL": None,
                "Verified Learning Minutes": None,
                "Estimated Learning Minutes": None,
                "Completed Date": row.get("Datum ukonceni") or row.get("Datum ukončení"),
                "start_date": row.get("Datum zahajeni") or row.get("Datum zahájení"),
                "end_date": row.get("Datum ukonceni") or row.get("Datum ukončení"),
            }
            records.setdefault(employee_id, []).append(record)
        return records

    def _parse_optional_datetime(self, value: Any) -> Optional[datetime]:
        """Best-effort datetime parser for spreadsheet values. Returns timezone-naive datetime."""
        if value in (None, "", "NaN"):
            return None
        try:
            timestamp = pd.to_datetime(value, errors="coerce")
            if pd.isna(timestamp):
                return None
            dt = timestamp.to_pydatetime()
            # Remove timezone info if present (database uses TIMESTAMP WITHOUT TIME ZONE)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except Exception:
            return None
    
    async def _save_org_hierarchy(
        self,
        session: AsyncSession,
        employee_id: str,
        org_hierarchy: Dict[str, str]
    ):
        """Save org hierarchy records."""
        for level in range(1, 5):
            level_key = f"level_{level}"
            hierarchy_name = org_hierarchy.get(level_key, "")
            
            if hierarchy_name:
                try:
                    hierarchy_record = OrgHierarchyRecord(
                        employee_id=employee_id,
                        level=level,
                        hierarchy_path=org_hierarchy.get("full_path", ""),
                        hierarchy_name_cz=hierarchy_name,
                        hierarchy_name_en=org_hierarchy.get("name_en") or hierarchy_name,
                        node_id=org_hierarchy.get("node_id"),
                        parent_node_id=org_hierarchy.get("parent_node_id"),
                        short_code=org_hierarchy.get("short_code"),
                        description=org_hierarchy.get("description"),
                    )
                    session.add(hierarchy_record)
                except Exception as e:
                    logger.warning(f"Failed to save org hierarchy level {level}: {e}")
                    continue
    
    async def load_historical_data(
        self,
        session: AsyncSession,
        base_path: Path,
        years: List[int]
    ) -> Dict[str, int]:
        """Load 12 years of historical data."""
        snapshots = await self.historical_loader.load_historical_data(base_path, years)
        saved_count = await self.historical_loader.save_historical_snapshots(session, snapshots)
        
        return {
            "total_snapshots": len(snapshots),
            "saved": saved_count,
            "failed": len(snapshots) - saved_count
        }
