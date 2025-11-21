import pandas as pd
from pathlib import Path
import re


class DataExtractor:
    """
    Unified loader and accessor for all HR/skills/course datasets.

    This class loads all Excel sources on initialization and provides
    convenience methods for:
    - extracting the list of skills completed by a specific user,
    - searching for relevant internal courses,
    - searching for relevant external (Degreed) courses.

    Notes
    -----
    Expected directory structure::

        data/
            Skill_mapping.xlsx
            Degreed.xlsx
            Degreed_Content_Catalog.xlsx
            ERP_SK1.Start_month - SE.xlsx
            RLS.sa_org_hierarchy - SE.xlsx
            ZHRPD_VZD_STA_007.xlsx
            ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx
            ZPE_KOM_KVAL.xlsx

    All datasets are loaded eagerly on class construction.
    """

    def __init__(self, data_dir: Path = Path(".data")):
        """
        Load all required Excel datasets into memory.

        Parameters
        ----------
        data_dir : Path, optional
            Directory containing all HR/skills/course files.
        """
        self._xls_skill_map = pd.ExcelFile(data_dir / "Skill_mapping.xlsx")
        self._mapping_df = pd.read_excel(self._xls_skill_map, sheet_name="Mapping")
        self._skills_df = pd.read_excel(self._xls_skill_map, sheet_name="Skills_1.25")

        # self._degreed_df = pd.read_excel(data_dir / "Degreed.xlsx")
        self._degreed_catalog_df = pd.read_excel(data_dir / "Degreed_Content_Catalog.xlsx")

        self._erp_df = pd.read_excel(data_dir / "ERP_SK1.Start_month - SE.xlsx")
        # self._hierarchy_df = pd.read_excel(data_dir / "RLS.sa_org_hierarchy - SE.xlsx")
        self._zhrpd_007_df = pd.read_excel(data_dir / "ZHRPD_VZD_STA_007.xlsx")
        # self._zhrpd_016_df = pd.read_excel(data_dir / "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx")
        # self._zpe_kom_kval_df = pd.read_excel(data_dir / "ZPE_KOM_KVAL.xlsx")

    def skills_for_user(self, personal_number: int) -> str:
        """
        Return all **unique completed skills** for the given user.

        Parameters
        ----------
        personal_number : int
            ERP personal identifier.

        Returns
        -------
        str
            JSON list of skill names in English, e.g.::

                '["Communication", "Python Basics", ...]'

        Notes
        -----
        Steps performed:
        - Merge ERP personal data with ZHRPD tables (training data).
        - Join with skill mapping table by type of action/object.
        - Join with skill catalog for readable names.
        - Filter rows by personal number.
        """
        # Merge ERP → ZHRPD
        erp_zhrpd_df = self._erp_df.merge(
            self._zhrpd_007_df,
            left_on="persstat_start_month.personal_number",
            right_on="ID účastníka",
            how="left",
            suffixes=("", "_zhrpd")
        )

        # Normalize types for merge
        erp_zhrpd_df["Typ akce"] = (
            erp_zhrpd_df["Typ akce"]
            .astype("Int64").astype(str).str.strip()
        )
        self._mapping_df["ID objektu"] = (
            self._mapping_df["ID objektu"]
            .astype(str).str.strip()
        )

        # Merge with mapping
        erp_zhrpd_map_df = erp_zhrpd_df.merge(
            self._mapping_df,
            left_on="Typ akce",
            right_on="ID objektu",
            how="left",
            suffixes=("", "_map")
        )

        # Normalize skill IDs
        df_map = erp_zhrpd_map_df.copy()
        df_map["ID skillu"] = (
            df_map["ID skillu"]
            .astype(str)
            .str.replace(r"\.0$", "", regex=True)
            .str.strip()
        )

        skills_df = self._skills_df.copy()
        skills_df["Skill ID"] = (
            skills_df["Skill ID"]
            .astype("Int64")
            .astype(str)
            .str.strip()
        )

        # Merge mapping → skills catalog
        user_skills_df = df_map.merge(
            skills_df,
            left_on="ID skillu",
            right_on="Skill ID",
            how="left",
            suffixes=("", "_skill")
        )

        # Filter by personal number
        result = (
            user_skills_df.loc[
                user_skills_df["persstat_start_month.personal_number"] == personal_number,
                ["Skill (EN) "]
            ]
            .dropna(how="all")
            .drop_duplicates()
        )

        return result.to_json()

    def internal_courses(self, keywords: list[str], limit: int = 3) -> list[str]:
        """
        Return up to `limit` random internal corporate courses relevant to given keywords.
        A match occurs only if the keyword appears as a whole word (case-insensitive).
        """
        s = self._mapping_df["Označení objektu"].drop_duplicates()

        if keywords:
            mask = pd.Series(False, index=s.index)
            for kw in keywords:
                kw = kw.strip()
                if not kw:
                    continue
                # whole-word regex: (?i)\bkw\b
                pattern = rf"(?i)\b{re.escape(kw)}\b"
                mask |= s.str.contains(pattern, regex=True, na=False)
            s = s[mask]

        if s.empty:
            return []

        n = min(limit, len(s))
        s = s.sample(n=n)

        return s.apply(lambda x: f"[Int.] {x}").tolist()

    def external_courses(self, keywords: list[str], limit: int = 3) -> list[str]:
        """
        Return up to `limit` random external courses relevant to given keywords.
        A match occurs only if the keyword appears as a whole word (case-insensitive).
        """
        s = self._degreed_catalog_df["Title"].drop_duplicates()

        if keywords:
            mask = pd.Series(False, index=s.index)
            for kw in keywords:
                kw = kw.strip()
                if not kw:
                    continue
                pattern = rf"(?i)\b{re.escape(kw)}\b"
                mask |= s.str.contains(pattern, regex=True, na=False)
            s = s[mask]

        if s.empty:
            return []

        n = min(limit, len(s))
        s = s.sample(n=n)

        return s.apply(lambda x: f"[Ext.] {x}").tolist()
