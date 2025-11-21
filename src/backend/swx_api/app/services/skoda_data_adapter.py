"""
Škoda Data Adapter
------------------
Transforms raw Škoda CSV files into internal employee models.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from swx_api.app.services.multilingual_normalization_service import MultilingualNormalizationService
from swx_api.core.middleware.logging_middleware import logger


SKODA_COLUMN_MAPPING = {
    "personal_number": "employee_id",
    "persstat_start_month_abc": "start_date",
    "pers_organization_branch": "organization_branch",
    "pers_profession_id": "profession_id",
    "pers_job_family_id": "job_family_id",
    "s1_org_hierarchy": "org_hierarchy_level_1",
    "s2_org_hierarchy": "org_hierarchy_level_2",
    "s3_org_hierarchy": "org_hierarchy_level_3",
    "s4_org_hierarchy": "org_hierarchy_level_4",
}

REQUIRED_SKODA_COLUMNS = [
    "personal_number",
    "persstat_start_month_abc",
    "pers_organization_branch",
]

QUALIFICATION_COLUMN_PATTERNS = [
    r"qualification",
    r"certification",
    r"certifikace",
    r"kvalifikace",
]

COURSE_HISTORY_COLUMN_PATTERNS = [
    r"course",
    r"kurz",
    r"training",
    r"školení",
    r"learning",
    r"učení",
]


class SkodaDataAdapter:
    """Adapter for transforming Škoda CSV data."""
    
    def __init__(self):
        self.normalization_service = MultilingualNormalizationService()
        self.course_catalog: Dict[str, Dict[str, Any]] = {}
        self.skill_mapping: Dict[str, str] = {}
        self.object_mapping: Dict[str, Dict[str, Any]] = {}
        self.org_hierarchy_lookup: Dict[str, Dict[str, Any]] = {}
        self.degreed_records: Dict[str, List[Dict[str, Any]]] = {}
        self.external_qualifications: Dict[str, List[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Dataset preloaders
    # ------------------------------------------------------------------
    
    def parse_skoda_csv(self, file_path: Path) -> pd.DataFrame:
        """Parse Škoda CSV with proper encoding."""
        try:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding="latin-1")
            except Exception as e:
                logger.error(f"Failed to parse CSV {file_path}: {e}")
                raise ValueError(f"Cannot parse CSV file: {e}")
        
        return df
    
    def validate_skoda_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate required Škoda columns exist."""
        missing = []
        for col in REQUIRED_SKODA_COLUMNS:
            if col not in df.columns:
                missing.append(col)
        
        return {
            "valid": len(missing) == 0,
            "missing_columns": missing,
            "total_columns": len(df.columns),
            "total_rows": len(df)
        }
    
    def transform_persstat_start_month_abc(self, value: str) -> Optional[datetime]:
        """Transform '2023-01' to datetime."""
        if pd.isna(value) or not value:
            return None
        
        value_str = str(value).strip()
        
        patterns = [
            (r"^(\d{4})-(\d{2})$", lambda m: datetime(int(m.group(1)), int(m.group(2)), 1)),
            (r"^(\d{4})/(\d{2})$", lambda m: datetime(int(m.group(1)), int(m.group(2)), 1)),
            (r"^(\d{2})\.(\d{4})$", lambda m: datetime(int(m.group(2)), int(m.group(1)), 1)),
        ]
        
        for pattern, converter in patterns:
            match = re.match(pattern, value_str)
            if match:
                try:
                    return converter(match)
                except ValueError:
                    continue
        
        return None
    
    def transform_org_hierarchy(self, row: pd.Series) -> Dict[str, str]:
        """Transform s1-s4 fields to structured hierarchy."""
        hierarchy = {}
        
        for level in range(1, 5):
            col_name = f"s{level}_org_hierarchy"
            value = self._get_column_value(row, col_name, None)
            if pd.notna(value) and value:
                hierarchy[f"level_{level}"] = str(value).strip()
            else:
                # Try ob{level} as alternative
                ob_value = self._get_column_value(row, f"ob{level}", None)
                if pd.notna(ob_value) and ob_value:
                    hierarchy[f"level_{level}"] = str(ob_value).strip()
                else:
                    hierarchy[f"level_{level}"] = ""
        
        full_path = "/".join([hierarchy[f"level_{i}"] for i in range(1, 5) if hierarchy[f"level_{i}"]])
        hierarchy["full_path"] = full_path
        
        node_id = str(
            self._get_column_value(row, "objid", "")
            or self._get_column_value(row, "org_node_id", "")
            or self._get_column_value(row, "sa_org_hierarchy.objid", "")
            or ""
        ).strip()
        node_info = self.org_hierarchy_lookup.get(node_id or "", {})
        hierarchy["node_id"] = node_id or None
        hierarchy["parent_node_id"] = node_info.get("parent_node_id")
        hierarchy["short_code"] = node_info.get("short_code")
        hierarchy["description"] = node_info.get("description")
        if node_info:
            hierarchy.setdefault("name_cz", node_info.get("name_cz"))
            hierarchy.setdefault("name_en", node_info.get("name_en"))
        
        return hierarchy
    
    def extract_qualifications(self, row: pd.Series) -> List[Dict[str, Any]]:
        """Extract qualifications from row."""
        qualifications = []
        
        for col in row.index:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in QUALIFICATION_COLUMN_PATTERNS):
                value = row.get(col)
                if pd.notna(value) and str(value).strip():
                    qual_id = f"QUAL_{col}"
                    qual_name = str(value).strip()
                    
                    normalized = self.normalization_service.normalize_qualification_name(qual_name)
                    
                    qualifications.append({
                        "qualification_id": qual_id,
                        "qualification_name_cz": normalized["cz"] or qual_name,
                        "qualification_name_en": normalized["en"] or qual_name,
                        "mandatory": "mandatory" in col_lower or "povinn" in col_lower,
                        "obtained_date": None,
                        "expiry_date": None,
                        "status": "active"
                    })
        
        return qualifications
    
    def _normalize_ob_fields(self, row: pd.Series) -> Dict[str, Optional[str]]:
        """Normalize OB1-OB8 codes."""
        normalized: Dict[str, Optional[str]] = {}
        for idx in range(1, 9):
            col = f"ob{idx}"
            value = self._get_column_value(row, col, None)
            if pd.notna(value) and value:
                normalized[col] = str(value).strip()
            else:
                normalized[col] = None
        return normalized
    
    def _map_education_fields(self, row: pd.Series) -> Dict[str, Optional[str]]:
        """Map education and study metadata."""
        def _safe(col: str) -> Optional[str]:
            value = self._get_column_value(row, col, None)
            if pd.isna(value) or value is None:
                return None
            return str(value).strip() if value else None
        
        return {
            "education_branch_group_id": _safe("basic_branch_of_education_group"),
            "education_branch_group_name": _safe("basic_branch_of_education_grou2"),
            "education_branch_id": _safe("basic_branch_of_education_id"),
            "education_branch_name": _safe("basic_branch_of_education_name"),
            "education_category_id": _safe("education_category_id"),
            "education_category_name": _safe("education_category_name"),
            "field_of_study_id": _safe("field_of_study_id"),
            "field_of_study_name": _safe("field_of_study_name"),
            "field_of_study_code": _safe("field_of_stude_code_ispv") or _safe("field_of_study_code"),
        }
    
    def _map_degreed_course(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Degreed export row to learning history entry."""
        minutes_to_hours = lambda minutes: round(float(minutes) / 60.0, 2) if minutes else None
        
        title = record.get("Title") or record.get("Content") or ""
        normalized_title = self.normalization_service.normalize_course_name(title)
        content_id = str(record.get("Content ID") or record.get("content_id") or "")
        object_info = self.object_mapping.get(content_id, {})
        if not normalized_title and object_info.get("object_name"):
            normalized_title = self.normalization_service.normalize_course_name(object_info["object_name"])
        provider = record.get("Content Provider") or object_info.get("catalog_code")
        course_type = record.get("Type") or object_info.get("group")
        verified_flag = str(record.get("Completion is Verified", "")).strip().lower() in {"y", "yes", "true", "1"}
        try:
            rating = float(record.get("Completion User Rating", "") or 0.0)
        except ValueError:
            rating = None
        
        return {
            "course_id": content_id,
            "course_name": normalized_title or title,
            "provider": provider or "Unknown",
            "course_type": str(course_type) if course_type else "Unknown",
            "start_date": None,
            "end_date": self._parse_degreed_date(record.get("Completed Date")),
            "hours": minutes_to_hours(record.get("Verified Learning Minutes")),
            "verified_minutes": self._safe_int(record.get("Verified Learning Minutes")),
            "estimated_minutes": self._safe_int(record.get("Estimated Learning Minutes")),
            "verified": verified_flag,
            "completion_points": self._safe_float(record.get("Completion Points")),
            "content_url": record.get("Content URL"),
            "content_id": record.get("Content ID"),
            "user_rating": rating,
            "completion_status": "completed" if verified_flag else "in_progress",
        }

    def _parse_degreed_date(self, raw_value: Any) -> Optional[str]:
        if not raw_value:
            return None
        try:
            dt = pd.to_datetime(raw_value)
            return dt.isoformat()
        except Exception:
            return None

    def _safe_int(self, value: Any) -> Optional[int]:
        try:
            return int(value) if value not in (None, "", "NaN") else None
        except (TypeError, ValueError):
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        try:
            return float(value) if value not in (None, "", "NaN") else None
        except (TypeError, ValueError):
            return None
    
    def extract_course_history(self, row: pd.Series, employee_id: str) -> List[Dict[str, Any]]:
        """Extract course history from row."""
        courses = []
        
        for col in row.index:
            col_lower = str(col).lower()
            if any(pattern in col_lower for pattern in COURSE_HISTORY_COLUMN_PATTERNS):
                value = row.get(col)
                if pd.notna(value) and str(value).strip():
                    course_name = str(value).strip()
                    
                    course_id = f"COURSE_{col}_{employee_id}"
                    
                    skills_covered = []
                    if course_id in self.course_catalog:
                        skills_covered = self.course_catalog[course_id].get("skills_covered", [])
                    
                    courses.append({
                        "course_id": course_id,
                        "course_name": course_name,
                        "provider": "Škoda Academy" if "skoda" in col_lower or "škoda" in col_lower else "External",
                    "course_type": "historical_column",
                        "start_date": None,
                        "end_date": None,
                        "hours": None,
                        "completion_status": "completed",
                        "skills_covered": skills_covered,
                        "certificate_url": None
                    })
        
        # Merge Degreed records if preloaded
        if employee_id in self.degreed_records:
            for record in self.degreed_records[employee_id]:
                courses.append(self._map_degreed_course(record))
        return courses
    
    def derive_skills_from_courses(self, course_history: List[Dict[str, Any]]) -> List[str]:
        """Derive skills from completed courses."""
        skills = []
        
        for course in course_history:
            if course.get("completion_status") == "completed":
                course_id = course.get("course_id", "")
                
                if course_id in self.course_catalog:
                    catalog_entry = self.course_catalog[course_id]
                    skills.extend(catalog_entry.get("skills_covered", []))
                else:
                    skills_covered = course.get("skills_covered", [])
                    if skills_covered:
                        skills.extend(skills_covered)
        
        return list(set(skills))
    
    def normalize_skoda_skills(self, skills_raw: str) -> List[str]:
        """Normalize skills from Škoda format."""
        if pd.isna(skills_raw) or not skills_raw:
            return []
        
        skills_str = str(skills_raw).strip()
        
        if "," in skills_str:
            skills_list = [s.strip() for s in skills_str.split(",") if s.strip()]
        elif ";" in skills_str:
            skills_list = [s.strip() for s in skills_str.split(";") if s.strip()]
        elif "|" in skills_str:
            skills_list = [s.strip() for s in skills_str.split("|") if s.strip()]
        else:
            skills_list = [skills_str] if skills_str else []
        
        normalized_skills = []
        for skill in skills_list:
            normalized = self.normalization_service.normalize_skill_name(skill)
            if normalized:
                normalized_skills.append(normalized)
        
        return list(set(normalized_skills))
    
    def _get_column_value(self, row: pd.Series, column_name: str, default: Any = None) -> Any:
        """Get column value, handling prefixed column names like 'persstat_start_month.personal_number'."""
        # Try exact match first
        if column_name in row.index:
            return row.get(column_name)
        
        # Try with prefix (e.g., 'persstat_start_month.personal_number')
        prefixed = f"persstat_start_month.{column_name}"
        if prefixed in row.index:
            return row.get(prefixed)
        
        # Try any column ending with the column name
        for col in row.index:
            col_str = str(col)
            if col_str.endswith(f".{column_name}") or col_str.endswith(f"_{column_name}"):
                return row.get(col)
        
        return default
    
    def map_to_employee_record(self, row: pd.Series) -> Dict[str, Any]:
        """Map Škoda row to employee record."""
        # Handle prefixed column names (e.g., persstat_start_month.personal_number)
        personal_number = str(self._get_column_value(row, "personal_number", "")).strip()
        if not personal_number:
            raise ValueError("personal_number is required")
        
        # Use helper to get column values with prefix handling
        # Try multiple department sources in order of preference
        organization_branch = None
        
        # 1. Try pers_organization_branch first
        org_branch_val = self._get_column_value(row, "pers_organization_branch", None)
        if org_branch_val and pd.notna(org_branch_val) and str(org_branch_val).strip():
            organization_branch = str(org_branch_val).strip()
        
        # 2. Try organization_branch
        if not organization_branch or organization_branch == "Unknown":
            org_branch_alt = self._get_column_value(row, "organization_branch", None)
            if org_branch_alt and pd.notna(org_branch_alt) and str(org_branch_alt).strip():
                organization_branch = str(org_branch_alt).strip()
        
        # 3. Try department column
        if not organization_branch or organization_branch == "Unknown":
            dept_val = self._get_column_value(row, "department", None)
            if dept_val and pd.notna(dept_val) and str(dept_val).strip():
                organization_branch = str(dept_val).strip()
        
        # 4. Extract from org hierarchy (s1 or s2 level)
        if not organization_branch or organization_branch == "Unknown":
            org_hierarchy = self.transform_org_hierarchy(row)
            # Try s2 first (more specific), then s1 (broader)
            hierarchy_dept = org_hierarchy.get("level_2") or org_hierarchy.get("level_1")
            if hierarchy_dept and hierarchy_dept.strip():
                organization_branch = hierarchy_dept.strip()
            # Also try OB codes if hierarchy doesn't have name
            elif org_hierarchy.get("node_id"):
                node_info = self.org_hierarchy_lookup.get(org_hierarchy.get("node_id"), {})
                org_name = node_info.get("name_cz") or node_info.get("name_en") or node_info.get("short_code")
                if org_name and str(org_name).strip():
                    organization_branch = str(org_name).strip()
        
        # 5. Try any column with "department" or "dept" in name
        if not organization_branch or organization_branch == "Unknown":
            for col in row.index:
                col_lower = str(col).lower()
                if "department" in col_lower or "dept" in col_lower:
                    dept_val = row.get(col)
                    if pd.notna(dept_val) and str(dept_val).strip() and str(dept_val).strip() != "Unknown":
                        organization_branch = str(dept_val).strip()
                        break
        
        # Default to "Unknown" only if all sources failed
        if not organization_branch or organization_branch == "":
            organization_branch = "Unknown"
        
        start_date_str = self._get_column_value(row, "persstat_start_month_abc", None)
        start_date = self.transform_persstat_start_month_abc(start_date_str) if pd.notna(start_date_str) and start_date_str else None
        
        # Extract org hierarchy early (used for department extraction)
        org_hierarchy = self.transform_org_hierarchy(row)
        
        skills = []
        
        skills_column = None
        for col in row.index:
            if "skill" in str(col).lower() or "competenc" in str(col).lower():
                skills_column = col
                break
        
        if skills_column and skills_column in row.index:
            skills_raw = row.get(skills_column)
            skills = self.normalize_skoda_skills(skills_raw)
        
        course_history = self.extract_course_history(row, personal_number)
        derived_skills = self.derive_skills_from_courses(course_history)
        skills.extend(derived_skills)
        
        # Extract skills from qualifications
        qualifications = self.extract_qualifications(row)
        qualifications.extend(self.external_qualifications.get(personal_number, []))
        
        # Extract skills from qualification names (qualifications often represent skills)
        for qual in qualifications:
            qual_name = qual.get("qualification_name_en") or qual.get("qualification_name_cz")
            if qual_name:
                # Try to normalize qualification name as a skill
                normalized_qual_skill = self.normalization_service.normalize_skill_name(qual_name)
                if normalized_qual_skill and normalized_qual_skill not in skills:
                    skills.append(normalized_qual_skill)
        
        # Apply skill mapping if available (normalize skill names using mapping table)
        if self.skill_mapping:
            mapped_skills = []
            for skill in skills:
                # Try exact match first
                if skill in self.skill_mapping:
                    mapped_skill = self.skill_mapping[skill]
                    if mapped_skill and mapped_skill not in mapped_skills:
                        mapped_skills.append(mapped_skill)
                else:
                    # Try case-insensitive match
                    skill_lower = skill.lower()
                    found = False
                    for orig_skill, mapped_skill in self.skill_mapping.items():
                        if orig_skill.lower() == skill_lower:
                            if mapped_skill and mapped_skill not in mapped_skills:
                                mapped_skills.append(mapped_skill)
                            found = True
                            break
                    if not found:
                        # Keep original skill if no mapping found
                        mapped_skills.append(skill)
            skills = mapped_skills
        
        # Remove duplicates and empty values
        skills = [s for s in skills if s and str(s).strip()]
        skills = list(set(skills))
        
        ob_codes = self._normalize_ob_fields(row)
        education_fields = self._map_education_fields(row)
        
        # Helper to safely get and strip string values
        def safe_str(col_name: str, default: str = None) -> Optional[str]:
            val = self._get_column_value(row, col_name, default)
            if pd.isna(val) or val == "":
                return default
            return str(val).strip() if val else default
        
        metadata = {
            "persstat_start_month_abc": str(start_date_str) if pd.notna(start_date_str) and start_date_str else None,
            "pers_profession_id": safe_str("pers_profession_id"),
            "pers_job_family_id": safe_str("pers_job_family_id"),
            "org_hierarchy": org_hierarchy,
            "start_date": start_date.isoformat() if start_date else None,
            "ob_codes": ob_codes,
            "education": education_fields,
        }
        
        return {
            "employee_id": personal_number,
            "personal_number": personal_number,
            "department": organization_branch,
            "persstat_start_month_abc": str(start_date_str) if pd.notna(start_date_str) and start_date_str else None,
            "pers_organization_branch": organization_branch,
            "pers_profession_id": safe_str("pers_profession_id"),
            "pers_profession_name": safe_str("pers_profession") or safe_str("profession"),
            "pers_job_family_id": safe_str("pers_job_family_id"),
            "s1_org_hierarchy": org_hierarchy.get("level_1", ""),
            "s2_org_hierarchy": org_hierarchy.get("level_2", ""),
            "s3_org_hierarchy": org_hierarchy.get("level_3", ""),
            "s4_org_hierarchy": org_hierarchy.get("level_4", ""),
            "ob_codes": ob_codes,
            "education_branch_id": education_fields.get("education_branch_id"),
            "education_branch_name": education_fields.get("education_branch_name"),
            "education_branch_group_id": education_fields.get("education_branch_group_id"),
            "education_branch_group_name": education_fields.get("education_branch_group_name"),
            "education_category_id": education_fields.get("education_category_id"),
            "education_category_name": education_fields.get("education_category_name"),
            "field_of_study_id": education_fields.get("field_of_study_id"),
            "field_of_study_name": education_fields.get("field_of_study_name"),
            "field_of_study_code": education_fields.get("field_of_study_code"),
            "coordinator_group_id": safe_str("coordinator_group_id"),
            "planned_profession_id": safe_str("planned_profession_id"),
            "planned_profession_name": safe_str("planned_profession"),
            "planned_position_id": safe_str("planned_position_id"),
            "planned_position_name": safe_str("planned_position"),
            "hr_contact_name": safe_str("user_name"),
            "skills": skills,
            "metadata": metadata,
            "qualifications": qualifications,
            "course_history": course_history,
        }
    
    def merge_historical_datasets(self, files: List[Path]) -> pd.DataFrame:
        """Merge 12 years of historical data."""
        dfs = []
        
        for file in files:
            try:
                df = self.parse_skoda_csv(file)
                
                year_match = re.search(r'(\d{4})', file.stem)
                if year_match:
                    snapshot_year = int(year_match.group(1))
                else:
                    snapshot_year = datetime.now().year
                
                df["snapshot_year"] = snapshot_year
                df["snapshot_date"] = datetime(snapshot_year, 1, 1)
                
                dfs.append(df)
            except Exception as e:
                logger.warning(f"Failed to load historical file {file}: {e}")
                continue
        
        if not dfs:
            raise ValueError("No valid historical datasets found")
        
        merged_df = pd.concat(dfs, ignore_index=True)
        return merged_df
    
    def load_historical_snapshots(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Load historical snapshots from merged dataframe."""
        snapshots = []
        
        for _, row in df.iterrows():
            try:
                employee_data = self.map_to_employee_record(row)
                snapshot_year = row.get("snapshot_year", datetime.now().year)
                snapshot_date = row.get("snapshot_date", datetime(snapshot_year, 1, 1))
                
                snapshot = {
                    "employee_id": employee_data["employee_id"],
                    "snapshot_date": snapshot_date if isinstance(snapshot_date, datetime) else datetime(snapshot_year, 1, 1),
                    "department": employee_data["department"],
                    "job_family_id": employee_data.get("pers_job_family_id"),
                    "org_hierarchy": {
                        "s1": employee_data.get("s1_org_hierarchy", ""),
                        "s2": employee_data.get("s2_org_hierarchy", ""),
                        "s3": employee_data.get("s3_org_hierarchy", ""),
                        "s4": employee_data.get("s4_org_hierarchy", ""),
                    },
                    "skills": employee_data.get("skills", []),
                    "qualifications": [q.get("qualification_id") for q in employee_data.get("qualifications", [])],
                    "pers_profession_id": employee_data.get("pers_profession_id"),
                    "pers_organization_branch": employee_data.get("pers_organization_branch"),
                }
                
                snapshots.append(snapshot)
            except Exception as e:
                logger.warning(f"Failed to create snapshot for row: {e}")
                continue
        
        return snapshots
    
    def set_course_catalog(self, catalog: Dict[str, Dict[str, Any]]):
        """Set course catalog for skill derivation."""
        self.course_catalog = catalog
    
    def set_skill_mapping(self, mapping: Dict[str, str]):
        """Set skill mapping for normalization."""
        self.skill_mapping = mapping
    
    def set_object_mapping(self, mapping: Dict[str, Dict[str, Any]]):
        """Map IDOBJ columns (course participation) to catalog metadata."""
        self.object_mapping = mapping
    
    def set_org_hierarchy_lookup(self, mapping: Dict[str, Dict[str, Any]]):
        """Map org hierarchy objid → textual labels."""
        self.org_hierarchy_lookup = mapping
    
    def set_degreed_records(self, degreed_rows: Dict[str, List[Dict[str, Any]]]):
        """Attach Degreed completions per employee."""
        self.degreed_records = degreed_rows

    def set_external_qualifications(self, qualifications: Dict[str, List[Dict[str, Any]]]):
        """Attach external qualification records keyed by employee."""
        self.external_qualifications = qualifications

