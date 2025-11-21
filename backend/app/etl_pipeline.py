import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Set
import pandas as pd
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    def normalize(col: str) -> str:
        # Convert to string in case of non-string column names
        col = str(col).lower()
        # Replace spaces and special chars with underscores
        col = re.sub(r'[^\w\s]', '_', col)
        col = re.sub(r'\s+', '_', col)
        # Collapse multiple underscores
        col = re.sub(r'_+', '_', col)
        # Strip leading/trailing underscores
        col = col.strip('_')
        return col

    df.columns = [normalize(col) for col in df.columns]
    return df


def _log_schema_diff(df: pd.DataFrame, expected_cols: Set[str], dataset_name: str):
    actual_cols = set(df.columns)
    missing = expected_cols - actual_cols
    extra = actual_cols - expected_cols

    if missing:
        logger.warning(f"{dataset_name}: Missing expected columns: {missing}")
    if extra:
        logger.info(f"{dataset_name}: Extra columns found: {extra}")

    logger.info(f"{dataset_name}: Loaded {len(df)} rows, {len(df.columns)} columns")


def load_excel_safe(file_path: Path, sheet_name: Optional[str] = None) -> Optional[pd.DataFrame]:
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    try:
        if sheet_name:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(file_path)

        df = _normalize_column_names(df)
        logger.info(f"Loaded {file_path.name} (sheet: {sheet_name or 'default'})")
        return df

    except Exception as e:
        logger.error(f"Failed to load {file_path.name}: {e}")
        return None


def clean_employees(df: pd.DataFrame) -> pd.DataFrame:
    expected = {
        'personal_number', 'org_unit', 'profession',
        'planned_profession', 'planned_position'
    }
    _log_schema_diff(df, expected, "Employees")

    # Normalize personal_number to string
    if 'personal_number' in df.columns:
        df['personal_number'] = df['personal_number'].astype(str).str.strip()

    # Remove duplicates based on personal_number
    if 'personal_number' in df.columns:
        df = df.drop_duplicates(subset=['personal_number'], keep='first')

    return df


def clean_course_participation(df: pd.DataFrame) -> pd.DataFrame:
    expected = {
        'personal_number', 'idobj', 'datum_zahajeni', 'datum_ukonceni'
    }
    _log_schema_diff(df, expected, "Course Participation")

    # Map actual columns to expected names
    column_mapping = {
        'id_ucastnika': 'personal_number',
        'datum_zahajeni': 'datum_zahajeni',
        'datum_ukonceni': 'datum_ukonceni',
        'oznaceni_typu_akce': 'oznaceni_typu_akce'
    }
    df = df.rename(columns=column_mapping)

    # Normalize personal_number
    if 'personal_number' in df.columns:
        df['personal_number'] = df['personal_number'].astype(str).str.strip()

    # Parse dates
    for date_col in ['datum_zahajeni', 'datum_ukonceni']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    return df


def clean_qualifications(df: pd.DataFrame) -> pd.DataFrame:
    expected = {'personal_number', 'id_q', 'name_q', 'start_date', 'end_date'}
    _log_schema_diff(df, expected, "Qualifications")

    # Map actual columns to expected names
    column_mapping = {
        'id_p': 'personal_number',
        'nazev_q': 'name_q',
        'pocat_datum': 'start_date',
        'koncove_datum': 'end_date'
    }
    df = df.rename(columns=column_mapping)

    # Normalize personal_number
    if 'personal_number' in df.columns:
        df['personal_number'] = df['personal_number'].astype(str).str.strip()

    # Parse dates
    for date_col in ['start_date', 'end_date']:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Flag indefinite qualifications
    if 'end_date' in df.columns:
        df['is_indefinite'] = df['end_date'].dt.year >= 9999

    return df


def clean_org_structure(df: pd.DataFrame) -> pd.DataFrame:
    expected = {'objid', 'paren', 'short'}
    _log_schema_diff(df, expected, "Org Structure")

    # Map actual columns to expected names
    column_mapping = {
        'sa_org_hierarchy_objid': 'objid',
        'sa_org_hierarchy_paren': 'paren',
        'sa_org_hierarchy_short': 'short',
        'sa_org_hierarchy_stxte': 'stxte',
        'sa_org_hierarchy_stxtc': 'stxtc',
        'sa_org_hierarchy_stxtd': 'stxtd'
    }
    df = df.rename(columns=column_mapping)

    return df


def clean_skill_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    expected = {'skillid', 'name', 'description'}
    _log_schema_diff(df, expected, "Skill Dictionary")

    # Normalize skillid
    if 'skillid' in df.columns:
        df['skillid'] = df['skillid'].astype(str).str.strip()

    return df


def clean_skill_mapping(mapping_df: pd.DataFrame,
                        skills_df: Optional[pd.DataFrame] = None,
                        elearning_df: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
    result = {}

    if mapping_df is not None:
        expected = {'course_id', 'skill_id', 'skill_name'}
        _log_schema_diff(mapping_df, expected, "Skill Mapping (Mapping sheet)")

        # Map actual columns to expected names
        column_mapping = {
            'id_objektu': 'course_id',
            'id_skillu': 'skill_id',
            'skill_v_en': 'skill_name'
        }
        mapping_df = mapping_df.rename(columns=column_mapping)
        result['mapping'] = mapping_df

    if skills_df is not None:
        _log_schema_diff(skills_df, set(), "Skill Mapping (Skills sheet)")
        result['skills'] = skills_df

    if elearning_df is not None:
        expected = {'title', 'topic', 'department'}
        _log_schema_diff(elearning_df, expected, "Skill Mapping (eLearning sheet)")
        result['elearning'] = elearning_df

    return result


def clean_role_qualifications(df: pd.DataFrame) -> pd.DataFrame:
    expected = {'planned_position_id', 'id_kvalifikace', 'kvalifikace'}
    _log_schema_diff(df, expected, "Role Qualifications")

    # Map actual columns to expected names
    column_mapping = {
        'cislo_fm': 'planned_position_id'
        # Keep id_kvalifikace and kvalifikace as-is if they exist
    }
    df = df.rename(columns=column_mapping)

    return df


def clean_degreed_events(df: pd.DataFrame) -> pd.DataFrame:
    expected = {
        'employee_id', 'content_id', 'content_title',
        'completion_date', 'estimated_learning_minutes'
    }
    _log_schema_diff(df, expected, "Degreed Events")

    # Map actual columns to expected names
    column_mapping = {
        'completed_date': 'completion_date'
    }
    df = df.rename(columns=column_mapping)

    # Normalize employee_id to string
    if 'employee_id' in df.columns:
        df['employee_id'] = df['employee_id'].astype(str).str.strip()

    # Parse completion date
    if 'completion_date' in df.columns:
        df['completion_date'] = pd.to_datetime(df['completion_date'], errors='coerce')

    return df


def clean_degreed_content(df: pd.DataFrame) -> pd.DataFrame:
    expected = {
        'content_id', 'title', 'provider', 'content_type',
        'estimated_learning_minutes'
    }
    _log_schema_diff(df, expected, "Degreed Content Catalog")

    # Extract skill columns (skill_1 to skill_15)
    skill_cols = [col for col in df.columns if re.match(r'skill_\d+', col)]
    group_cols = [col for col in df.columns if re.match(r'group_\d+', col)]

    logger.info(f"Found {len(skill_cols)} skill columns and {len(group_cols)} group columns")

    return df


def merge_employee_learning_profile(employees: pd.DataFrame,
                                     course_participation: pd.DataFrame) -> pd.DataFrame:
    """
    Merge employees with their course participation history.
    """
    if 'personal_number' not in employees.columns:
        logger.error("Cannot merge: employees missing 'personal_number'")
        return employees

    if 'personal_number' not in course_participation.columns:
        logger.error("Cannot merge: course_participation missing 'personal_number'")
        return employees

    merged = employees.merge(
        course_participation,
        on='personal_number',
        how='left',
        suffixes=('', '_course')
    )

    logger.info(f"Employee learning profile: {len(merged)} rows")
    return merged


def merge_skills_matrix(skill_mapping: pd.DataFrame,
                        skill_dictionary: pd.DataFrame) -> pd.DataFrame:
    if 'skill_id' not in skill_mapping.columns:
        logger.warning("skill_mapping missing 'skill_id', returning as-is")
        return skill_mapping

    if 'skillid' not in skill_dictionary.columns:
        logger.warning("skill_dictionary missing 'skillid', returning mapping only")
        return skill_mapping

    merged = skill_mapping.merge(
        skill_dictionary,
        left_on='skill_id',
        right_on='skillid',
        how='left',
        suffixes=('_mapping', '_dict')
    )

    logger.info(f"Skills matrix: {len(merged)} rows")
    return merged


def merge_compliance_tracking(employees: pd.DataFrame,
                               qualifications: pd.DataFrame,
                               role_requirements: pd.DataFrame) -> pd.DataFrame:
    """
    Merge employees with their qualifications and role requirements.
    """
    # First, merge employees with their qualifications
    if 'personal_number' in employees.columns and 'personal_number' in qualifications.columns:
        emp_qual = employees.merge(
            qualifications,
            on='personal_number',
            how='left',
            suffixes=('', '_qual')
        )
    else:
        logger.warning("Cannot merge qualifications: missing 'personal_number'")
        emp_qual = employees

    # Then merge with role requirements
    if 'planned_position' in emp_qual.columns and 'planned_position_id' in role_requirements.columns:
        compliance = emp_qual.merge(
            role_requirements,
            left_on='planned_position',
            right_on='planned_position_id',
            how='left',
            suffixes=('', '_req')
        )
    else:
        logger.warning("Cannot merge role requirements: missing join keys")
        compliance = emp_qual

    logger.info(f"Compliance tracking: {len(compliance)} rows")
    return compliance


def create_global_unified_dataset(employee_learning: pd.DataFrame,
                                   skills_matrix: pd.DataFrame,
                                   compliance: pd.DataFrame,
                                   degreed_events: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    unified = employee_learning.copy()

    if 'idobj' in unified.columns and 'course_id' in skills_matrix.columns:
        unified = unified.merge(
            skills_matrix,
            left_on='idobj',
            right_on='course_id',
            how='left',
            suffixes=('', '_skill')
        )
        logger.info("Merged skills into unified dataset")
    else:
        logger.warning("Cannot merge skills: missing join keys")

    if degreed_events is not None:
        logger.info("Degreed events available but not merged (no clear join key)")

    logger.info(f"Global unified dataset: {len(unified)} rows, {len(unified.columns)} columns")
    return unified


def run_etl_pipeline():
    logger.info("=" * 80)
    logger.info("Starting ETL Pipeline")
    logger.info("=" * 80)

    raw_dir = settings.raw_xlsx_dir
    output_dir = settings.clean_parquet_dir

    # Verify raw directory exists
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        raise RuntimeError(f"Please create {raw_dir} and place Excel files there")

    # === LOAD PHASE ===
    logger.info("Loading Excel files...")

    # Employee master data
    employees_raw = load_excel_safe(raw_dir / "ERP_SK1. Start_month – SE.xlsx")

    # Course participation
    course_participation_raw = load_excel_safe(raw_dir / "ZHRPD_VZD_STA_007.xlsx")

    # Qualifications
    qualifications_raw = load_excel_safe(raw_dir / "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx")

    # Org structure
    org_structure_raw = load_excel_safe(raw_dir / "RLS.sa_org_hierarchy - SE.xlsx")

    # Skills dictionary
    skill_dict_raw = load_excel_safe(raw_dir / "Skills_File_11_05_2025_142355.xlsx")

    # Skill mapping (multiple sheets)
    skill_mapping_file = raw_dir / "Skill_mapping.xlsx"
    skill_mapping_raw = load_excel_safe(skill_mapping_file, settings.skill_mapping_sheet_name)
    skill_mapping_skills_raw = load_excel_safe(skill_mapping_file, settings.skill_mapping_skills_sheet)
    skill_mapping_elearning_raw = load_excel_safe(skill_mapping_file, settings.skill_mapping_elearning_sheet)

    # Role qualifications
    role_qual_raw = load_excel_safe(raw_dir / "ZPE_KOM_KVAL.xlsx")

    # Degreed data
    degreed_events_raw = load_excel_safe(raw_dir / "Degreed.xlsx")
    degreed_content_raw = load_excel_safe(raw_dir / "Degreed_Content_Catalog.xlsx")

    # === CLEAN PHASE ===
    logger.info("Cleaning datasets...")

    datasets = {}

    if employees_raw is not None:
        datasets['employees'] = clean_employees(employees_raw)

    if course_participation_raw is not None:
        datasets['course_participation'] = clean_course_participation(course_participation_raw)

    if qualifications_raw is not None:
        datasets['qualifications'] = clean_qualifications(qualifications_raw)

    if org_structure_raw is not None:
        datasets['org_structure'] = clean_org_structure(org_structure_raw)

    if skill_dict_raw is not None:
        datasets['skill_dictionary'] = clean_skill_dictionary(skill_dict_raw)

    if skill_mapping_raw is not None:
        skill_mapping_cleaned = clean_skill_mapping(
            skill_mapping_raw,
            skill_mapping_skills_raw,
            skill_mapping_elearning_raw
        )
        datasets.update({
            'skill_mapping': skill_mapping_cleaned.get('mapping'),
            'skill_mapping_skills': skill_mapping_cleaned.get('skills'),
            'skill_mapping_elearning': skill_mapping_cleaned.get('elearning')
        })

    if role_qual_raw is not None:
        datasets['role_qualifications'] = clean_role_qualifications(role_qual_raw)

    if degreed_events_raw is not None:
        datasets['degreed_events'] = clean_degreed_events(degreed_events_raw)

    if degreed_content_raw is not None:
        datasets['degreed_content'] = clean_degreed_content(degreed_content_raw)

    # === MERGE PHASE ===
    logger.info("Creating merged datasets...")

    # Employee learning profile
    if 'employees' in datasets and 'course_participation' in datasets:
        datasets['employee_learning_profile'] = merge_employee_learning_profile(
            datasets['employees'],
            datasets['course_participation']
        )

    # Skills matrix
    if 'skill_mapping' in datasets and 'skill_dictionary' in datasets:
        datasets['skills_matrix'] = merge_skills_matrix(
            datasets['skill_mapping'],
            datasets['skill_dictionary']
        )

    # Compliance tracking
    if all(k in datasets for k in ['employees', 'qualifications', 'role_qualifications']):
        datasets['compliance_tracking'] = merge_compliance_tracking(
            datasets['employees'],
            datasets['qualifications'],
            datasets['role_qualifications']
        )

    # Global unified dataset
    if 'employee_learning_profile' in datasets and 'skills_matrix' in datasets:
        datasets['global_unified'] = create_global_unified_dataset(
            datasets['employee_learning_profile'],
            datasets['skills_matrix'],
            datasets.get('compliance_tracking', datasets['employees']),
            datasets.get('degreed_events')
        )

    # === SAVE PHASE ===
    logger.info("Saving Parquet files...")

    for name, df in datasets.items():
        if df is not None:
            output_path = output_dir / f"{name}.parquet"
            df.to_parquet(output_path, index=False)
            logger.info(f"Saved: {output_path.name} ({len(df)} rows)")

    logger.info("=" * 80)
    logger.info("ETL Pipeline Complete")
    logger.info(f"Output directory: {output_dir}")
    logger.info("=" * 80)

    return datasets


if __name__ == "__main__":
    run_etl_pipeline()
