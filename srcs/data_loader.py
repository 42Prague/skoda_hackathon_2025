import os
import re
import unicodedata
from typing import Dict, Any, List, Tuple

import pandas as pd


class DataLoader:
    """
    Loads and normalizes heterogeneous HR datasets so downstream code can rely on
    consistent column names (snake_case, ASCII) regardless of the original Excel headers.

    Schema:
      - employees: ERP_SK1.Start_month - SE.xlsx
      - internal_courses: ZHRPD_VZD_STA_007.xlsx
      - degreed completions: Degreed.xlsx
      - degreed_content: Degreed_Content_Catalog.xlsx
      - degreed_skill_dict: Skills_File_11_05_2025_142355.xlsx
      - skill_mapping + hr_skill_dict: Skill_mapping.xlsx (sheets "mapping" and "Skills_1.25")
      - emp_qualifications: ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx
      - pos_requirements: ZPE_KOM_KVAL.xlsx
      - org_hierarchy: RLS.sa_org_hierarchy - SE.xlsx
    """

    # --------- FILE NAMES --------- #

    FILE_MAP: Dict[str, str] = {
        "employees": "ERP_SK1.Start_month - SE.xlsx",
        "internal_courses": "ZHRPD_VZD_STA_007.xlsx",
        "degreed": "Degreed.xlsx",
        # Skill_mapping.xlsx contains 2 sheets: Skills_1.25 and mapping
        "skill_mapping": "Skill_mapping.xlsx",
        "emp_qualifications": "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx",
        "pos_requirements": "ZPE_KOM_KVAL.xlsx",
        "org_hierarchy": "RLS.sa_org_hierarchy - SE.xlsx",
    }

    OPTIONAL_FILE_MAP: Dict[str, str] = {
        "degreed_content": "Degreed_Content_Catalog.xlsx",
        "degreed_skill_dict": "Skills_File_11_05_2025_142355.xlsx",
    }

    # --------- PERSONAL_NUMBER ALIASES --------- #

    PERSONAL_NUMBER_ALIASES: List[str] = [
        "personal_number",
        "personal_no",
        "personalno",
        "personal_nr",
        "pernr",
        "per_nr",
        "pers_nr",
        "personalnummer",
        "osobni_cislo",
        "osobni_cislo1",
        "personal_id",
        "persstat_start_month_personal_number",
        "id_ucastnika",
        "id_p",
        "employee_id",
    ]

    # --------- COLUMN ALIASES --------- #

    COLUMN_ALIASES: Dict[str, Dict[str, List[str]]] = {
        # ===== EMPLOYEES =====
        "employees": {
            "personal_number": PERSONAL_NUMBER_ALIASES,
            "name": [
                "persstat_start_month_user_name",
                "user_name",
            ],
            "profession_id": [
                "persstat_start_month_profession_id",
            ],
            "profession_name": [
                "persstat_start_month_profession",
            ],
            "planned_position_id": [
                "persstat_start_month_planned_position_id",
                "planned_position_id",
                "planned_position",
                "planned_positionid",
                "position_id",
                "job_role_id",
            ],
            "position_name": [
                "persstat_start_month_planned_position",
                "persstat_start_month_planned_profession",
                "persstat_start_month_profession",
                "position_name",
                "position",
                "job_title",
                "profession",
                "planned_profession",
            ],
            "org_unit_id": [
                "sa_org_hierarchy_objid"
                "org_unit_id",
                "org_unit",
                "orgunit",
                "organizational_unit",
            ],
            "basic_branch_of_education_group": [
                "persstat_start_month_basic_branch_of_education_group",
            ],
            "basic_branch_of_education_group2": [
                "persstat_start_month_basic_branch_of_education_grou2",
            ],
            "basic_branch_of_education_id": [
                "persstat_start_month_basic_branch_of_education_id",
            ],
            "basic_branch_of_education_name": [
                "persstat_start_month_basic_branch_of_education_name",
            ],
            "education_category_id": [
                "persstat_start_month_education_category_id",
            ],
            "education_category_name": [
                "persstat_start_month_education_category_name",
            ],
            "field_of_study_id": [
                "persstat_start_month_field_of_study_id",
            ],
            "field_of_study_name": [
                "persstat_start_month_field_of_study_name",
            ],
            "field_of_study_code_ispv": [
                "persstat_start_month_field_of_stude_code_ispv",
            ],
        },

        # ===== INTERNAL COURSES =====
        "internal_courses": {
            "personal_number": PERSONAL_NUMBER_ALIASES,
            "event_type": [
                "typ_akce",
            ],
            "event_name": [
                "oznaceni_typu_akce",
                "nazev_kurzu",
            ],
            "idobj": [
                "idobj",
                "id_objektu",
            ],
            "start_date": [
                "datum_zahajeni",
                "zacatek",
                "start_date",
            ],
            "end_date": [
                "datum_ukonceni",
                "datum_ukonceni_kurzu",
                "end_date",
            ],
        },

        # ===== DEGREED LEARNING =====
        "degreed": {
            "employee_id": [
                "employee_id",
            ],
            "personal_number": PERSONAL_NUMBER_ALIASES,
            "content_id": [
                "content_id",
            ],
            "content_title": [
                "content_title",
                "title",
            ],
            "content_type": [
                "content_type",
                "type",
            ],
            "content_provider": [
                "content_provider",
                "provider",
            ],
            "completion_date": [
                "completed_date",
                "completion_date",
            ],
            "completion_is_verified": [
                "completion_is_verified",
            ],
            "completion_user_rating": [
                "completion_user_rating",
            ],
            "completion_points": [
                "completion_points",
            ],
            "content_url": [
                "content_url",
                "url",
            ],
            "verified_learning_minutes": [
                "verified_learning_minutes",
            ],
            "estimated_learning_minutes": [
                "estimated_learning_minutes",
            ],
        },

        # ===== DEGREED CONTENT CATALOG =====
        "degreed_content": {
            "title": ["titel", "title", "content_title"],
            "content_id": ["content_id"],
            "content_type": ["type", "content_type"],
            "internal_id": ["internal_id"],
            "summary": ["summary"],
            "url": ["url"],
            "provider": ["provider", "content_provider"],
            "internal_external": ["internal_external_content", "internal_external"],
            "content_estimated_learning_minutes": [
                "content_estimated_learning_minutes",
                "estimated_learning_minutes",
            ],
            "thumbnail_url": ["thumbnail_url"],
            "thumbs_up": ["thumbs_up"],
            "thumbs_down": ["thumbs_down"],
            "language": ["language"],
            "plans": ["plans"],
            "pathways": ["pathways"],
            # Categories
            "category_1": ["category_1"],
            "category_2": ["category_2"],
            "category_3": ["category_3"],
            "category_4": ["category_4"],
            "category_5": ["category_5"],
            "category_6": ["category_6"],
            "category_7": ["category_7"],
            "category_8": ["category_8"],
            "category_9": ["category_9"],
            "category_10": ["category_10"],
            "category_11": ["category_11"],
            "category_12": ["category_12"],
            "category_13": ["category_13"],
            "category_14": ["category_14"],
            "category_15": ["category_15"],
            # Groups
            "group_1": ["group_1"],
            "group_2": ["group_2"],
            "group_3": ["group_3"],
            "group_4": ["group_4"],
            "group_5": ["group_5"],
            "group_6": ["group_6"],
            "group_7": ["group_7"],
            "group_8": ["group_8"],
            "group_9": ["group_9"],
            "group_10": ["group_10"],
            "group_11": ["group_11"],
            "group_12": ["group_12"],
            "group_13": ["group_13"],
            "group_14": ["group_14"],
            "group_15": ["group_15"],
        },

        # ===== SKILL MAPPING =====
        "skill_mapping": {
            "content_id": ["id_objektu", "idobj"],
            "object_short_name": ["zkratka_objektu"],
            "object_name": ["oznaceni_objektu"],
            "valid_from": ["pocat_datum", "pocat_dat", "pocatni_datum"],
            "valid_to": ["koncove_datum", "konec_datum"],
            "catalog": ["katalog"],
            "topic": ["tema"],
            "group": ["skupina"],
            "skill_id": ["id_skillu", "skill_id"],
            "skill_name": ["skill_v_en"],
        },

        # ===== HR SKILL DICTIONARY =====
        "hr_skill_dict": {
            "skill_id": ["skill_id"],
            "skill_name": ["skill_en", "skill", "skill_en_"],
        },

        # ===== DEGREED SKILL DICTIONARY =====
        "degreed_skill_dict": {
            "skill_id": ["skillid", "skill_id"],
            "skill_name": ["name"],
            "description": ["description"],
        },

        # ===== EMP QUALIFICATIONS =====
        "emp_qualifications": {
            "personal_number": PERSONAL_NUMBER_ALIASES,
            "qualification_id": ["id_q", "id_kvalifikace"],
            "qualification_name": ["nazev_q", "kvalifikace"],
            "valid_from": ["pocat_datum"],
            "valid_to": ["koncove_datum"],
        },

        # ===== POSITION REQUIREMENTS =====
        "pos_requirements": {
            "planned_position_id": ["cislo_fm", "planned_position_id"],
            "qualification_id": ["id_kvalifikace", "id_q"],
            "qualification_name": ["kvalifikace", "nazev_q"],
            "is_mandatory": ["is_mandatory", "mandatory", "povinne"],
        },

        # ===== ORG HIERARCHY =====
        "org_hierarchy": {
            "objid": [
                "objid",
                "org_unit_id",
                "organizational_unit",
                "sa_org_hierarchy_objid",
            ],
            "paren": [
                "paren",
                "parent",
                "parent_id",
                "sa_org_hierarchy_paren",
            ],
            "stxte": [
                "stxte",
                "department",
                "name_en",
                "sa_org_hierarchy_stxte",
                "sa_org_hierarchy_stxtc",
                "sa_org_hierarchy_stxtd",
            ],
        },
    }

    # --------- INIT --------- #

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.data: Dict[str, pd.DataFrame] = {}

    # --------- PUBLIC: LOAD ALL --------- #

    def load_all(self) -> Dict[str, pd.DataFrame]:
        """Loads all required datasets into a dictionary with normalized schemas."""
        # Mandatory files
        for key, filename in self.FILE_MAP.items():
            if key == "skill_mapping":
                mapping_df, hr_skill_df = self._load_skill_mapping_bundle(filename)
                self.data["skill_mapping"] = self._prepare_dataframe("skill_mapping", mapping_df)
                if not hr_skill_df.empty:
                    self.data["hr_skill_dict"] = self._prepare_dataframe("hr_skill_dict", hr_skill_df)
                continue

            raw = self._load_file(filename, suppress_warning=False)
            self.data[key] = self._prepare_dataframe(key, raw)

        # Optional files
        for key, filename in self.OPTIONAL_FILE_MAP.items():
            raw = self._load_file(filename, suppress_warning=True)
            if not raw.empty:
                self.data[key] = self._prepare_dataframe(key, raw)

        return self.data

    # --------- INTERNAL: FILE IO --------- #

    def _load_file(self, filename: str, suppress_warning: bool = False) -> pd.DataFrame:
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            # Try CSV if XLSX not found
            if filename.endswith(".xlsx"):
                csv_path = path.replace(".xlsx", ".csv")
                if os.path.exists(csv_path):
                    return pd.read_csv(csv_path)

            if not suppress_warning:
                print(f"Warning: File {filename} not found in {self.data_dir}. Returning empty DataFrame.")
            return pd.DataFrame()

        try:
            if filename.endswith(".csv"):
                df = pd.read_csv(path)
            elif filename.endswith(".xlsx"):
                df = pd.read_excel(path)
            else:
                df = pd.read_csv(path)
            return df
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return pd.DataFrame()

    def _load_skill_mapping_bundle(self, filename: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Skill_mapping.xlsx contains 2 sheets:
          - Skills_1.25  -> hr_skill_dict
          - mapping      -> skill_mapping
        """
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            print(f"Warning: Skill mapping file {filename} not found in {self.data_dir}.")
            return pd.DataFrame(), pd.DataFrame()

        try:
            xls = pd.ExcelFile(path)
            sheet_names = {name.lower(): name for name in xls.sheet_names}

            mapping_sheet = sheet_names.get("mapping")
            skills_sheet = None
            
            for key, name in sheet_names.items():
                if "skills" in key:
                    skills_sheet = name
                    break

            mapping_df = pd.read_excel(xls, mapping_sheet) if mapping_sheet else pd.DataFrame()
            hr_skill_df = pd.read_excel(xls, skills_sheet) if skills_sheet else pd.DataFrame()
            return mapping_df, hr_skill_df

        except Exception as e:
            print(f"Error loading Skill_mapping bundle from {filename}: {e}")
            return pd.DataFrame(), pd.DataFrame()

    # --------- INTERNAL: PREPARE DF --------- #

    def _prepare_dataframe(self, key: str, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and apply alias mappings for a dataset."""
        if df.empty:
            return df

        df = df.copy()
        df.columns = [self._normalize_column_name(col) for col in df.columns]

        alias_map = self.COLUMN_ALIASES.get(key, {})
        if alias_map:
            df = self._apply_aliases(df, alias_map)

        df = self._postprocess_dataset(key, df)
        return df

    def _postprocess_dataset(self, key: str, df: pd.DataFrame) -> pd.DataFrame:
        """Dataset-specific cleanups to guarantee required columns exist."""
        if key in {"employees", "internal_courses", "degreed", "emp_qualifications"}:
            df = self._ensure_personal_number(df)

        if key == "pos_requirements" and "is_mandatory" in df.columns:
            df["is_mandatory"] = df["is_mandatory"].fillna(False).astype(bool)

        return df

    # --------- PERSONAL NUMBER HANDLING --------- #

    def _ensure_personal_number(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure personal_number exists and is string-normalized.
        """
        cols = list(df.columns)

        if "personal_number" not in df.columns:
            cand = next((c for c in cols if "personal_number" in c), None)
            if cand:
                df["personal_number"] = df[cand]
            else:
                fallback_col = next(
                    (col for col in ["employee_id", "id", "employeeid"] if col in df.columns),
                    None,
                )
                if fallback_col:
                    df["personal_number"] = df[fallback_col]

        if "personal_number" in df.columns:
            df["personal_number"] = (
                df["personal_number"]
                .apply(self._normalize_identifier_value)
                .astype("string")
            )

        return df

    # --------- INTERNAL: ALIASES & NORMALIZATION --------- #

    def _apply_aliases(self, df: pd.DataFrame, alias_map: Dict[str, List[str]]) -> pd.DataFrame:
        """Rename columns according to alias map: first match wins."""
        rename_dict = {}
        for canonical, aliases in alias_map.items():
            for alias in aliases:
                if alias in df.columns:
                    rename_dict[alias] = canonical
                    break
        if rename_dict:
            df = df.rename(columns=rename_dict)
        return df

    @staticmethod
    def _normalize_column_name(name: Any) -> str:
        """Convert column headers to ASCII snake_case."""
        normalized = (
            unicodedata.normalize("NFKD", str(name))
            .encode("ascii", "ignore")
            .decode("ascii")
        )
        normalized = normalized.lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")
        return normalized

    @staticmethod
    def _normalize_identifier_value(value: Any) -> str:
        """Normalize numeric-like identifiers (e.g. '123.0' -> '123')."""
        if pd.isna(value):
            return ""
        value_str = str(value).strip()
        if value_str.lower() == "nan":
            return ""
        if re.match(r"^\d+\.0$", value_str):
            value_str = value_str[:-2]
        return value_str