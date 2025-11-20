"""
ETL Pipeline for Employee Learning & Development Data
Loads XLSX files, validates, normalizes, and outputs clean Parquet files
"""

import pandas as pd
import numpy as np
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pyarrow as pa
import pyarrow.parquet as pq
import difflib
import unicodedata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL Pipeline for processing employee learning data"""

    def __init__(self, input_dir: str = "./data", output_dir: str = "./data/clean"):
        # Resolve paths relative to the repository root (srcs parent) when given as relative paths.
        repo_root = Path(__file__).parent.parent.resolve()

        def _resolve(p: str) -> Path:
            pth = Path(p)
            if pth.is_absolute():
                return pth.expanduser().resolve()
            return (repo_root / p).expanduser().resolve()

        self.input_dir = _resolve(input_dir)
        self.output_dir = _resolve(output_dir)

        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory resolved and ensured: {self.output_dir}")
        except Exception as e:
            logger.error(f"Unable to create output directory {self.output_dir}: {e}")
            raise

        self.file_configs = {
            "employees": {
                "filename": "ERP_SK1. Start_month – SE.xlsx",
                "expected_columns": [
                    "employee_id",
                    "personal_number",
                    "sa_org_hierarchy.objid",
                    "profession",
                    "planned_profession",
                    "planned_position",
                    "education_category",
                    "education_field",
                    "education_level"
                ]
            },
            "degreed_events": {
                "filename": "Degreed.xlsx",
                "expected_columns": [
                    "employee_id",
                    "completed_date",
                    "content_id",
                    "content_title",
                    "content_provider",
                    "content_url",
                    "completion_is_verified",
                    "estimated_learning_minutes"
                ]
            },
            "degreed_content_catalog": {
                "filename": "Degreed_Content_Catalog.xlsx",
                "expected_columns": [
                    "content_id",
                    "title",
                    "provider",
                    "content_type",
                    "url",
                    "language",
                    "estimated_learning_minutes",
                ]
            },
            "org_structure": {
                "filename": "RLS.sa_org_hierarchy - SE.xlsx",
                "expected_columns": [
                    "objid",
                    "paren",
                    "short",
                    "stxtc",
                    "stxtd",
                    "stxte"
                ]
            },
            "skill_dictionary": {
                "filename": "Skills_File_11_05_2025_142355.xlsx",
                "expected_columns": [
                    "skillid",
                    "name",
                    "description",
                    "plans",
                    "source",
                    "endorsed"
                ]
            },
            "skill_mapping": {
                "filename": "Skill_mapping.xlsx",
                "expected_columns": [
                    "course_id",
                    "course_title",
                    "topic",
                    "department",
                    "skill_id",
                    "skill_name"
                ]
            },
            "qualifications": {
                "filename": "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx",
                "expected_columns": [
                    "personal_number",
                    "start_date",
                    "end_date",
                    "id_q",
                    "name_q"
                ]
            },
            "course_participation": {
                "filename": "ZHRPD_VZD_STA_007.xlsx",
                "expected_columns": [
                    "personal_number",
                    "idobj",
                    "oznaceni_typu_akce",
                    "datum_zahajeni",
                    "datum_ukonceni"
                ]
            },
            "role_qualification_requirements": {
                "filename": "ZPE_KOM_KVAL.xlsx",
                "expected_columns": [
                    "planned_position_id",
                    "id_kvalifikace",
                    "kvalifikace"
                ]
            }
        }
        self.dataframes: Dict[str, pd.DataFrame] = {}

    def to_snake_case(self, text: str) -> str:
        """Convert text to lowercase snake_case"""
        if pd.isna(text):
            return text
        text = str(text).strip()
        text = re.sub(r'[\s\-]+', '_', text)
        text = re.sub(r'[^\w_]', '', text)
        text = re.sub(r'_+', '_', text)
        return text.lower().strip('_')

    def normalize_name(self, name: str) -> str:
        """Normalize person names (title case, strip extra spaces)"""
        if pd.isna(name):
            return name
        name = str(name).strip()
        name = re.sub(r'\s+', ' ', name)
        return name.title()

    def normalize_email(self, email: str) -> str:
        """Normalize email addresses (lowercase, strip spaces)"""
        if pd.isna(email):
            return email
        return str(email).strip().lower()

    def normalize_course_id(self, course_id: str) -> str:
        """Normalize course IDs (uppercase, strip spaces)"""
        if pd.isna(course_id):
            return course_id
        return str(course_id).strip().upper()

    def load_data(self) -> None:
        """Load all XLSX files with fuzzy filename matching for unicode/special chars"""
        logger.info("Starting data loading process...")

        # list available files once
        available_files = [p.name for p in self.input_dir.glob("*") if p.is_file()]
        logger.info(f"  Available files in {self.input_dir}: {available_files}")

        def _normalize_name(s: str) -> str:
            if s is None:
                return ""
            # normalize unicode, replace dash variants with hyphen, collapse whitespace, lowercase
            s = unicodedata.normalize("NFKD", s)
            s = s.replace('\u2013', '-').replace('\u2014', '-')
            s = re.sub(r'[\s\-_]+', ' ', s)
            s = re.sub(r'[^\w\s\.]', '', s)  # keep dot for extensions
            return s.strip().lower()

        for name, config in self.file_configs.items():
            expected_filename = config['filename']
            filepath = self.input_dir / expected_filename

            # if exact exists, use it
            if not filepath.exists():
                # try to find close match among available files
                norm_expected = _normalize_name(expected_filename)
                candidates = []
                for f in available_files:
                    if f.lower().endswith(('.xlsx', '.xls')):
                        candidates.append(f)
                # build normalized mapping
                norm_map = {f: _normalize_name(f) for f in candidates}
                # use difflib to find closest matches on normalized strings
                matches = difflib.get_close_matches(norm_expected, list(norm_map.values()), n=3, cutoff=0.6)
                chosen = None
                if matches:
                    # map back to original filename (first match)
                    for orig, norm in norm_map.items():
                        if norm == matches[0]:
                            chosen = orig
                            break

                if chosen:
                    filepath = self.input_dir / chosen
                    logger.info(f"Loading {expected_filename} -> matched to {chosen}")
                else:
                    logger.warning(f"  File not found: {expected_filename}. No close match in {self.input_dir}. Skipping dataset '{name}'.")
                    continue

            try:
                logger.info(f"Loading {filepath.name}...")
                df = pd.read_excel(filepath, engine='openpyxl')

                # Log original shape
                logger.info(f"  Loaded {len(df)} rows, {len(df.columns)} columns")

                # Store dataframe
                self.dataframes[name] = df

            except FileNotFoundError:
                logger.error(f"  File not found during read: {filepath}")
                # skip missing file instead of raising to allow processing other datasets
                continue
            except Exception as e:
                logger.error(f"  Error loading {filepath.name}: {str(e)}")
                raise

        logger.info(f"Successfully loaded {len(self.dataframes)} datasets")

    def validate_schema(self) -> None:
        """Validate schema and column consistency"""
        logger.info("Validating schemas...")

        for name, config in self.file_configs.items():
            if name not in self.dataframes:
                logger.warning(f"  Skipping validation for missing dataset: {name}")
                continue

            df = self.dataframes[name]

            # Normalize column names (lowercase, strip spaces, replace spaces with underscores)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            actual_cols = list(df.columns)

            # Attempt to map/match prefixed or localized columns to expected columns
            expected_cols = [c.lower().strip() for c in config['expected_columns']]
            rename_map = {}

            # quick substring / suffix matches (handles prefixes like persstat_start_month.x)
            for exp in expected_cols:
                if exp in actual_cols:
                    continue
                # candidates that end with the expected token or contain it
                candidates = [a for a in actual_cols if a.endswith(f".{exp}") or a.endswith(f"_{exp}") or a.endswith(exp) or exp in a]
                if candidates:
                    # prefer exact suffix match, otherwise first candidate
                    chosen = None
                    for c in candidates:
                        if c.split('.')[-1] == exp or c.split('_')[-1] == exp:
                            chosen = c
                            break
                    if not chosen:
                        chosen = candidates[0]
                    rename_map[chosen] = exp
                    continue

                # fuzzy match as fallback
                match = difflib.get_close_matches(exp, actual_cols, n=1, cutoff=0.6)
                if match:
                    rename_map[match[0]] = exp

            if rename_map:
                logger.info(f"  {name}: Renaming columns to expected names: {rename_map}")
                df = df.rename(columns=rename_map)
                self.dataframes[name] = df
                actual_cols = list(df.columns)

            expected_set = set(expected_cols)
            actual_set = set(actual_cols)

            # Check for missing columns
            missing_cols = expected_set - actual_set
            if missing_cols:
                logger.warning(f"  {name}: Missing columns: {missing_cols}")

            # Check for extra columns
            extra_cols = actual_set - expected_set
            if extra_cols:
                logger.info(f"  {name}: Extra columns found: {extra_cols}")

            # Log validation success
            if not missing_cols:
                logger.info(f"  {name}: Schema validation passed ✓")

        logger.info("Schema validation completed")

    def clean_and_normalize(self) -> None:
        """Clean and normalize all datasets"""
        logger.info("Starting data cleaning and normalization...")

        # Clean employees
        if 'employees' in self.dataframes:
            df = self.dataframes['employees']
            logger.info(f"  Cleaning employees ({len(df)} rows)...")

            # normalize employee column names to snake-case-like to ease matching
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            # Ensure employee_id exists: prefer explicit employee_id, then personal_number-like columns
            if 'employee_id' not in df.columns:
                # look for any column that contains 'personal_number' or endswith '_personal_number'
                personal_cols = [c for c in df.columns if 'personal_number' in c]
                if personal_cols:
                    src = personal_cols[0]
                    df['employee_id'] = df[src].astype(str)
                    logger.info(f"    Created employee_id from column: {src}")
                else:
                    # fallback: try any column that looks like an id
                    id_cols = [c for c in df.columns if c.endswith('_id') or c == 'id']
                    if id_cols:
                        df['employee_id'] = df[id_cols[0]].astype(str)
                        logger.info(f"    Created employee_id from column: {id_cols[0]}")
                    else:
                        # last resort: synthetic ids
                        df['employee_id'] = (pd.RangeIndex(start=1, stop=len(df)+1)).astype(str)
                        logger.warning("    employee_id not present; generated synthetic employee_id values")

            # Safe normalization of common fields if present
            if 'name' in df.columns:
                df['name'] = df['name'].apply(self.normalize_name)
            if 'email' in df.columns:
                df['email'] = df['email'].apply(self.normalize_email)
            if 'department' in df.columns:
                df['department'] = df['department'].astype(str).str.strip().str.title()
            if 'role' in df.columns:
                df['role'] = df['role'].astype(str).str.strip().str.title()

            # Remove duplicates safely (guard against missing key)
            if 'employee_id' in df.columns:
                before = len(df)
                df = df.drop_duplicates(subset=['employee_id'], keep='first')
                after = len(df)
                if before != after:
                    logger.info(f"    Removed {before - after} duplicate employees")
            else:
                logger.warning("    Skipping duplicate removal: employee_id still missing")

            self.dataframes['employees'] = df

        # Clean courses
        if 'courses' in self.dataframes:
            df = self.dataframes['courses']
            logger.info(f"  Cleaning courses ({len(df)} rows)...")

            if 'course_id' in df.columns:
                df['course_id'] = df['course_id'].apply(self.normalize_course_id)
            if 'course_name' in df.columns:
                df['course_name'] = df['course_name'].astype(str).str.strip()
            if 'category' in df.columns:
                df['category'] = df['category'].astype(str).str.strip().str.title()

            before = len(df)
            if 'course_id' in df.columns:
                df = df.drop_duplicates(subset=['course_id'], keep='first')
                after = len(df)
                if before != after:
                    logger.info(f"    Removed {before - after} duplicate courses")

            self.dataframes['courses'] = df

        # Clean skill dictionary - convert to snake_case
        if 'skill_dictionary' in self.dataframes:
            df = self.dataframes['skill_dictionary']
            logger.info(f"  Cleaning skill_dictionary ({len(df)} rows)...")

            # handle multiple possible column names for skill name/id
            if 'skill_name' in df.columns:
                original_skills = df['skill_name'].copy()
                df['skill_name'] = df['skill_name'].apply(self.to_snake_case)
                logger.info(f"    Normalized {len(df)} skill names to snake_case")
                sample = pd.DataFrame({
                    'original': original_skills.head(5),
                    'normalized': df['skill_name'].head(5)
                })
                logger.info(f"    Sample transformations:\n{sample.to_string(index=False)}")

            if 'skill_category' in df.columns:
                df['skill_category'] = df['skill_category'].apply(self.to_snake_case)

            if 'skill_id' in df.columns:
                before = len(df)
                df = df.drop_duplicates(subset=['skill_id'], keep='first')
                after = len(df)
                if before != after:
                    logger.info(f"    Removed {before - after} duplicate skills")

            self.dataframes['skill_dictionary'] = df

        # Clean employee_courses (also accept degreed_events as source)
        if 'employee_courses' in self.dataframes or 'degreed_events' in self.dataframes:
            key = 'employee_courses' if 'employee_courses' in self.dataframes else 'degreed_events'
            df = self.dataframes[key]
            logger.info(f"  Cleaning {key} ({len(df)} rows)...")

            # normalize column names
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            if 'course_id' in df.columns:
                df['course_id'] = df['course_id'].apply(self.normalize_course_id)
            if 'status' in df.columns:
                df['status'] = df['status'].astype(str).str.strip().str.lower()

            # Convert date columns
            date_cols = ['enrollment_date', 'completion_date', 'completed_date', 'datum_zahajeni', 'datum_zahajeni', 'datum_ukonceni']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # ensure employee_id exists
            if 'employee_id' not in df.columns:
                personal_cols = [c for c in df.columns if 'personal_number' in c]
                if personal_cols:
                    df['employee_id'] = df[personal_cols[0]].astype(str)
                    logger.info(f"    Created employee_id in {key} from {personal_cols[0]}")

            self.dataframes['employee_courses'] = df

        # Clean course_skill_mapping (also accept skill_mapping as source)
        if 'course_skill_mapping' in self.dataframes or 'skill_mapping' in self.dataframes:
            key = 'course_skill_mapping' if 'course_skill_mapping' in self.dataframes else 'skill_mapping'
            df = self.dataframes[key]
            logger.info(f"  Cleaning {key} ({len(df)} rows)...")

            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            if 'course_id' in df.columns:
                df['course_id'] = df['course_id'].apply(self.normalize_course_id)
            if 'proficiency_level' in df.columns:
                df['proficiency_level'] = df['proficiency_level'].astype(str).str.strip().str.lower()

            self.dataframes['course_skill_mapping'] = df

        # Clean org_structure
        if 'org_structure' in self.dataframes:
            df = self.dataframes['org_structure']
            logger.info(f"  Cleaning org_structure ({len(df)} rows)...")

            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            if 'department' in df.columns:
                df['department'] = df['department'].astype(str).str.strip().str.title()
            if 'location' in df.columns:
                df['location'] = df['location'].astype(str).str.strip().str.title()
            if 'hire_date' in df.columns:
                df['hire_date'] = pd.to_datetime(df['hire_date'], errors='coerce')

            self.dataframes['org_structure'] = df

        # Clean qualifications
        if 'qualifications' in self.dataframes:
            df = self.dataframes['qualifications']
            logger.info(f"  Cleaning qualifications ({len(df)} rows)...")

            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            # create consistent column names if possible
            if 'název_q' in df.columns:
                df = df.rename(columns={'název_q': 'name_q'})

            if 'name_q' in df.columns:
                df['qualification_name'] = df['name_q'].astype(str).str.strip()
            if 'start_date' in df.columns:
                df['start_date'] = pd.to_datetime(df['start_date'], errors='coerce')
            if 'end_date' in df.columns:
                df['end_date'] = pd.to_datetime(df['end_date'], errors='coerce')

            # ensure employee_id if personal_number present
            if 'employee_id' not in df.columns:
                personal_cols = [c for c in df.columns if 'personal_number' in c]
                if personal_cols:
                    df['employee_id'] = df[personal_cols[0]].astype(str)

            self.dataframes['qualifications'] = df

        # Clean participation_history
        if 'participation_history' in self.dataframes or 'course_participation' in self.dataframes:
            key = 'participation_history' if 'participation_history' in self.dataframes else 'course_participation'
            df = self.dataframes[key]
            logger.info(f"  Cleaning {key} ({len(df)} rows)...")

            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            if 'course_id' in df.columns:
                df['course_id'] = df['course_id'].apply(self.normalize_course_id)

            date_cols = ['start_date', 'end_date', 'datum_zahajeni', 'datum_ukonceni']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')

            # ensure employee_id if possible
            if 'employee_id' not in df.columns:
                personal_cols = [c for c in df.columns if 'personal_number' in c]
                if personal_cols:
                    df['employee_id'] = df[personal_cols[0]].astype(str)

            self.dataframes['participation_history'] = df

        # Clean role_qualification_requirements
        if 'role_qualification_requirements' in self.dataframes:
            df = self.dataframes['role_qualification_requirements']
            logger.info(f"  Cleaning role_qualification_requirements ({len(df)} rows)...")

            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

            if 'role_name' in df.columns:
                df['role_name'] = df['role_name'].astype(str).str.strip().str.title()
            if 'required_qualification' in df.columns:
                df['required_qualification'] = df['required_qualification'].astype(str).str.strip()
            if 'is_mandatory' in df.columns:
                try:
                    df['is_mandatory'] = df['is_mandatory'].astype(bool)
                except Exception:
                    df['is_mandatory'] = df['is_mandatory'].astype(str).str.lower().map({'true': True, '1': True}).fillna(False)

            self.dataframes['role_qualification_requirements'] = df

        logger.info("Data cleaning and normalization completed")

    def create_merged_datasets(self) -> None:
        """Create merged datasets per domain and a global unified dataset"""
        logger.info("Creating merged datasets...")

        def _ensure_col(df: pd.DataFrame, target: str, patterns: List[str]) -> pd.DataFrame:
            """Ensure dataframe has target column, try to create from any column that matches patterns"""
            if target in df.columns:
                return df
            for pat in patterns:
                for c in df.columns:
                    if pat in c.lower():
                        df[target] = df[c].astype(str)
                        logger.info(f"    Created {target} from column: {c}")
                        return df
            return df

        # Domain 1: Employee Learning Profile
        logger.info("  Creating employee_learning_profile...")
        # prepare employees
        if 'employees' in self.dataframes:
            self.dataframes['employees'] = _ensure_col(
                self.dataframes['employees'],
                'employee_id',
                ['employee_id', 'personal_number', 'personalno', 'persstat', 'id_p', 'id']
            )
        # prepare employee_courses
        if 'employee_courses' in self.dataframes:
            self.dataframes['employee_courses'] = _ensure_col(
                self.dataframes['employee_courses'],
                'employee_id',
                ['employee_id', 'personal_number', 'personalno', 'persstat', 'id_p', 'id']
            )
            self.dataframes['employee_courses'] = _ensure_col(
                self.dataframes['employee_courses'],
                'course_id',
                ['course_id', 'id_kurzu', 'idobj', 'id_obj', 'id']
            )

        # prepare courses
        if 'courses' in self.dataframes:
            self.dataframes['courses'] = _ensure_col(
                self.dataframes['courses'],
                'course_id',
                ['course_id', 'id_kurzu', 'idobj', 'id_obj', 'id']
            )

        if all(k in self.dataframes for k in ['employees', 'employee_courses', 'courses']):
            emp_df = self.dataframes['employees']
            courses_df = self.dataframes['courses']
            ec_df = self.dataframes['employee_courses']

            # final checks before merge
            if 'employee_id' not in emp_df.columns:
                logger.error("Cannot create employee_learning_profile: 'employee_id' missing in employees")
            elif 'employee_id' not in ec_df.columns:
                logger.error("Cannot create employee_learning_profile: 'employee_id' missing in employee_courses")
            elif 'course_id' not in ec_df.columns and 'course_id' not in courses_df.columns:
                logger.error("Cannot create employee_learning_profile: 'course_id' missing in both employee_courses and courses")
            else:
                emp_learning = emp_df.merge(
                    ec_df,
                    on='employee_id',
                    how='left'
                )
                if 'course_id' in emp_learning.columns and 'course_id' in courses_df.columns:
                    emp_learning = emp_learning.merge(
                        courses_df,
                        on='course_id',
                        how='left',
                        suffixes=('', '_course')
                    )
                else:
                    logger.warning("Skipping course-level merge for employee_learning_profile due to missing course_id")

                if 'org_structure' in self.dataframes:
                    org_df = self.dataframes['org_structure']
                    # try to match on employee_id or objid->employee org mapping if available
                    if 'employee_id' in emp_learning.columns and 'employee_id' in org_df.columns:
                        emp_learning = emp_learning.merge(org_df, on='employee_id', how='left', suffixes=('', '_org'))
                    else:
                        logger.debug("Skipping org_structure merge: no common key found")

                self.dataframes['employee_learning_profile'] = emp_learning
                logger.info(f"    Created employee_learning_profile: {len(emp_learning)} rows")

        # Domain 2: Skills Matrix
        logger.info("  Creating skills_matrix...")
        if all(k in self.dataframes for k in ['courses', 'course_skill_mapping', 'skill_dictionary']):
            c_df = self.dataframes['courses']
            csm_df = self.dataframes['course_skill_mapping']
            sd_df = self.dataframes['skill_dictionary']

            csm_df = _ensure_col(csm_df, 'course_id', ['course_id', 'id_kurzu', 'idobj', 'id'])
            csm_df = _ensure_col(csm_df, 'skill_id', ['skill_id', 'skillid', 'id_k'])
            sd_df = _ensure_col(sd_df, 'skill_id', ['skill_id', 'skillid', 'id'])

            skills_matrix = c_df.merge(
                csm_df,
                on='course_id' if 'course_id' in c_df.columns and 'course_id' in csm_df.columns else None,
                how='left'
            ) if ('course_id' in c_df.columns and 'course_id' in csm_df.columns) else c_df.copy()

            if 'skill_id' in skills_matrix.columns and 'skill_id' in sd_df.columns:
                skills_matrix = skills_matrix.merge(sd_df, on='skill_id', how='left', suffixes=('', '_skill'))
            else:
                logger.warning("Skipping skill dictionary merge for skills_matrix due to missing skill_id")

            self.dataframes['skills_matrix'] = skills_matrix
            logger.info(f"    Created skills_matrix: {len(skills_matrix)} rows")

        # Domain 3: Compliance Tracking
        logger.info("  Creating compliance_tracking...")
        if 'employees' in self.dataframes and 'qualifications' in self.dataframes:
            emp_df = self.dataframes['employees']
            qual_df = self.dataframes['qualifications']

            qual_df = _ensure_col(qual_df, 'employee_id', ['employee_id', 'personal_number', 'id_p', 'id'])
            if 'employee_id' not in emp_df.columns or 'employee_id' not in qual_df.columns:
                logger.warning("Skipping compliance_tracking: employee_id missing in employees or qualifications")
            else:
                compliance = emp_df.merge(qual_df, on='employee_id', how='left')

                if 'role' in compliance.columns:
                    compliance = compliance.merge(
                        self.dataframes['role_qualification_requirements'],
                        left_on='role',
                        right_on='role_name',
                        how='left',
                        suffixes=('', '_req')
                    )

                self.dataframes['compliance_tracking'] = compliance
                logger.info(f"    Created compliance_tracking: {len(compliance)} rows")

        # Global Unified Dataset
        logger.info("  Creating global_unified_dataset...")
        if 'employee_learning_profile' in self.dataframes:
            global_df = self.dataframes['employee_learning_profile'].copy()

            # Add skills information
            if 'skills_matrix' in self.dataframes and 'course_id' in global_df.columns:
                skills_subset = self.dataframes['skills_matrix']
                if 'course_id' in skills_subset.columns:
                    cols = [c for c in ['course_id', 'skill_id', 'skill_name', 'proficiency_level'] if c in skills_subset.columns]
                    global_df = global_df.merge(skills_subset[cols], on='course_id', how='left')

            # Add qualifications
            if 'qualifications' in self.dataframes and 'employee_id' in global_df.columns:
                qual_agg = self.dataframes['qualifications'].copy()
                if 'qualification_name' in qual_agg.columns:
                    qual_agg = qual_agg.groupby('employee_id').agg({
                        'qualification_name': lambda x: ', '.join(x.dropna().astype(str))
                    }).reset_index()
                    qual_agg.columns = ['employee_id', 'all_qualifications']
                    global_df = global_df.merge(qual_agg, on='employee_id', how='left')

            # Add participation history
            if 'participation_history' in self.dataframes and {'employee_id', 'course_id'}.issubset(global_df.columns):
                global_df = global_df.merge(
                    self.dataframes['participation_history'],
                    on=['employee_id', 'course_id'],
                    how='left',
                    suffixes=('', '_participation')
                )

            self.dataframes['global_unified_dataset'] = global_df
            logger.info(f"    Created global_unified_dataset: {len(global_df)} rows, {len(global_df.columns)} columns")

        logger.info("Merged datasets created successfully")

    def save_to_parquet(self) -> None:
        """Save all dataframes to Parquet format"""
        logger.info("Saving cleaned datasets to Parquet...")

        for name, df in self.dataframes.items():
            output_path = self.output_dir / f"{name}.parquet"

            try:
                # Convert to Parquet
                df.to_parquet(output_path, engine='pyarrow', compression='snappy', index=False)

                file_size = output_path.stat().st_size / 1024 / 1024  # MB
                logger.info(f"  Saved {name}.parquet: {len(df)} rows, {len(df.columns)} columns, {file_size:.2f} MB")

            except Exception as e:
                logger.error(f"  Error saving {name}.parquet: {str(e)}")
                raise

        logger.info(f"All datasets saved to {self.output_dir}")

    def run(self) -> None:
        """Execute the complete ETL pipeline"""
        start_time = datetime.now()
        logger.info("="*80)
        logger.info("Starting ETL Pipeline")
        logger.info("="*80)

        try:
            # Step 1: Load data
            self.load_data()

            # Step 2: Validate schema
            self.validate_schema()

            # Step 3: Clean and normalize
            self.clean_and_normalize()

            # Step 4: Create merged datasets
            self.create_merged_datasets()

            # Step 5: Save to Parquet
            self.save_to_parquet()

            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("="*80)
            logger.info("ETL Pipeline Completed Successfully!")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Datasets processed: {len(self.dataframes)}")
            logger.info(f"Output directory: {self.output_dir}")
            logger.info("="*80)

        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
            raise


if __name__ == "__main__":
    # Run the ETL pipeline
    pipeline = ETLPipeline(input_dir="./data", output_dir="./data/clean")
    pipeline.run()