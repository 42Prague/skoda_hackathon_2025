import pandas as pd
from typing import Iterable, Optional, Dict, Any, List
from datetime import datetime
from collections import Counter


class DataProcessor:
    """
    High-level data logic for the AI Skill Coach prototype.

    Works with real hackathon files:
      - employees: ERP_SK1.Start_month - SE.xlsx
      - internal_courses: ZHRPD_VZD_STA_007.xlsx
      - degreed: Degreed.xlsx
      - degreed_content: Degreed_Content_Catalog.xlsx (optional)
      - skill_mapping: Skill_mapping.xlsx (mapping sheet)
      - skill_dict: Skills_File_11_05_2025_142355.xlsx (optional)
      - emp_qualifications: ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx
      - pos_requirements: ZPE_KOM_KVAL.xlsx
      - org_hierarchy: RLS.sa_org_hierarchy - SE.xlsx
    """

    def __init__(self, data: Dict[str, pd.DataFrame]):
        self.data = data
        self._org_short_map = self._build_org_short_map()

    # ---------------------------------------------------------------------
    # Helper methods
    # ---------------------------------------------------------------------
    def _build_org_short_map(self) -> Dict[str, str]:
        """
        Builds mapping for classifications:
          sa_org_hierarchy.short -> sa_org_hierarchy.stxte
        """
        org = self.data.get("org_hierarchy", pd.DataFrame())
        mapping: Dict[str, str] = {}

        if org.empty:
            return mapping

        org = org.copy()
        short_col = self._find_column(org, ["short", "sa_org_hierarchy_short"])
        label_col = self._find_column(org, ["stxte", "sa_org_hierarchy_stxte"])

        if not short_col or not label_col:
            return mapping

        for _, row in org[[short_col, label_col]].dropna().iterrows():
            code = str(row[short_col]).strip()
            label = str(row[label_col]).strip()
            if code and label and code not in mapping:
                mapping[code] = label

        return mapping

    def _decode_org_classification(self, code: Any) -> Optional[str]:
        """
        Takes a code (e.g. 'S', 'SE') and returns human-readable decoding.
        """
        if code is None or (isinstance(code, float) and pd.isna(code)):
            return None
        code_str = str(code).strip()
        if not code_str:
            return None
        return self._org_short_map.get(code_str)

    @staticmethod
    def _find_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
        """Return the first matching column name from candidates."""
        for col in candidates:
            if col in df.columns:
                return col
        return None

    @staticmethod
    def _norm_id(value: Any) -> str:
        """Normalize ID: '123.0' -> '123', NaN -> ''."""
        if pd.isna(value):
            return ""
        s = str(value).strip()
        if s.lower() == "nan":
            return ""
        if s.endswith(".0") and s[:-2].isdigit():
            s = s[:-2]
        return s

    # ---------------------------------------------------------------------
    # Public API used by app.py
    # ---------------------------------------------------------------------

    def get_employee_profile(self, employee_id: str) -> Dict[str, Any]:
        """
        Constructs employee profile:
          - basic info (position, org unit, department)
          - skill list (from internal courses and Degreed)
        """
        employee_id_norm = self._norm_id(employee_id)

        employees = self.data.get("employees", pd.DataFrame())
        if employees.empty:
            return {}

        pn_col = self._find_column(employees, ["personal_number"])
        if pn_col is None:
            return {}

        employees = employees.copy()
        employees[pn_col] = employees[pn_col].astype(str).str.strip()
        emp_rows = employees[employees[pn_col] == employee_id_norm]

        if emp_rows.empty:
            return {}

        emp = emp_rows.iloc[0]

        profile: Dict[str, Any] = {
            "personal_number": employee_id_norm,
            "employee_id": emp.get("employee_id"),
            "name": f"Employee {employee_id_norm}",
            "org_unit_id": emp.get("org_unit_id"),
            "department": emp.get("department"),
        }

        # --- Professions ---
        profile["current_profession_name"] = emp.get("profession_name")
        profile["current_profession_id"]     = emp.get("profession_id")

        profile["planned_profession_name"] = emp.get("persstat_start_month_planned_profession")
        profile["planned_profession_id"]   = emp.get("persstat_start_month_planned_profession_id")

        # --- Position FM ---
        profile["planned_position_id"]   = emp.get("planned_position_id")
        profile["planned_position_name"] = emp.get("position_name")

        # --- ERP OB1..OB8 ---
        profile["ob1"] = emp.get("persstat_start_month_ob1")
        profile["ob2"] = emp.get("persstat_start_month_ob2")
        profile["ob3"] = emp.get("persstat_start_month_ob3")
        profile["ob5"] = emp.get("persstat_start_month_ob5")
        profile["ob8"] = emp.get("persstat_start_month_ob8")

        profile["ob1_label"] = self._decode_org_classification(profile["ob1"])
        profile["ob2_label"] = self._decode_org_classification(profile["ob2"])
        profile["ob3_label"] = self._decode_org_classification(profile["ob3"])
        profile["ob5_label"] = self._decode_org_classification(profile["ob5"])
        profile["ob8_label"] = self._decode_org_classification(profile["ob8"])

        # --- Education ---
        profile["basic_branch_of_education_name"] = emp.get("basic_branch_of_education_name")
        profile["education_category_name"] = emp.get("education_category_name")
        profile["field_of_study_name"] = emp.get("field_of_study_name")

        # Fetch department from org structure if missing in employees
        if not profile.get("department"):
            org = self.data.get("org_hierarchy", pd.DataFrame())
            if not org.empty and profile.get("org_unit_id"):
                org = org.copy()
                obj_col = self._find_column(org, ["objid", "org_unit_id", "organizational_unit"])
                dept_col = self._find_column(org, ["stxte", "department", "name_en"])
                if obj_col and dept_col:
                    org[obj_col] = org[obj_col].astype(str).str.strip()
                    ou_id = self._norm_id(profile["org_unit_id"])
                    row_match = org[org[obj_col] == ou_id]
                    if not row_match.empty:
                        profile["department"] = str(row_match.iloc[0][dept_col]).strip()

        # -----------------------------------------------------------------
        # Skills: Internal Courses + Degreed
        # -----------------------------------------------------------------
        skills: List[Dict[str, Any]] = []
        
        # Add safety check 'or []' to prevent TypeError
        skills.extend(self._skills_from_internal_courses(employee_id_norm) or [])
        skills.extend(self._skills_from_degreed(profile, employee_id_norm) or [])

        # Deduplicate
        if skills:
            skills_df = pd.DataFrame(skills).fillna("")
            skills_df = skills_df.drop_duplicates(
                subset=["skill", "source", "source_name", "date"], keep="first"
            )
            skills = skills_df.to_dict("records")

        profile["skills"] = skills
        profile["skills_detailed"] = skills

        return profile

    def analyze_gaps(self, employee_id: str) -> Dict[str, Any]:
        """
        Compares employee qualifications with position requirements.
        """
        emp_profile = self.get_employee_profile(employee_id)
        if not emp_profile:
            return {}

        pos_id = self._norm_id(emp_profile.get("planned_position_id"))
        position_name = emp_profile.get("position_name")

        # --------------------- Position Requirements --------------------- #
        reqs = self.data.get("pos_requirements", pd.DataFrame())
        if reqs.empty:
            return {
                "position_id": pos_id,
                "position_name": position_name,
                "total_requirements": 0,
                "met_count": 0,
                "missing_count": 0,
                "completeness_score": 100.0,
                "gaps": [],
                "met": [],
                "error": "No formal requirements data (ZPE_KOM_KVAL) loaded.",
            }

        reqs = reqs.copy()
        req_pos_col = self._find_column(reqs, ["planned_position_id"])
        if req_pos_col is None:
            return {
                "position_id": pos_id,
                "position_name": position_name,
                "total_requirements": 0,
                "met_count": 0,
                "missing_count": 0,
                "completeness_score": 100.0,
                "gaps": [],
                "met": [],
                "error": "Column 'planned_position_id' not found in requirements dataset.",
            }

        reqs[req_pos_col] = reqs[req_pos_col].astype(str).str.strip()
        reqs[req_pos_col] = reqs[req_pos_col].apply(self._norm_id)
        pos_reqs = reqs[req_pos_col] == pos_id
        pos_reqs = reqs[pos_reqs]

        if pos_reqs.empty:
            return {
                "position_id": pos_id,
                "position_name": position_name,
                "total_requirements": 0,
                "met_count": 0,
                "missing_count": 0,
                "completeness_score": 100.0,
                "gaps": [],
                "met": [],
                "info": "No formal qualification requirements configured for this role.",
            }

        # --------------------- Employee Qualifications ------------------- #
        quals = self.data.get("emp_qualifications", pd.DataFrame())
        qual_pn_col = self._find_column(quals, ["personal_number"])
        qual_id_col = self._find_column(quals, ["qualification_id", "id_q", "id_kvalifikace"])

        existing_ids: List[str] = []
        if not quals.empty and qual_pn_col and qual_id_col:
            quals = quals.copy()
            quals[qual_pn_col] = quals[qual_pn_col].astype(str).str.strip()
            quals[qual_pn_col] = quals[qual_pn_col].apply(self._norm_id)
            emp_quals = quals[quals[qual_pn_col] == self._norm_id(employee_id)]

            if not emp_quals.empty:
                if "valid_to" in emp_quals.columns:
                    now = datetime.now()
                    try:
                        emp_quals["valid_to_dt"] = pd.to_datetime(
                            emp_quals["valid_to"], errors="coerce"
                        )
                        mask_valid = (
                            emp_quals["valid_to_dt"].isna()
                            | (emp_quals["valid_to_dt"] >= now)
                        )
                        emp_quals = emp_quals[mask_valid]
                    except Exception:
                        pass

                existing_ids = [
                    self._norm_id(x)
                    for x in emp_quals[qual_id_col].dropna().tolist()
                ]

        # --------------------- Calculate Gaps ------------------------------ #
        gaps: List[Dict[str, Any]] = []
        met: List[Dict[str, Any]] = []

        qid_col_req = self._find_column(
            pos_reqs, ["qualification_id", "id_q", "id_kvalifikace"]
        )
        qname_col_req = self._find_column(
            pos_reqs, ["qualification_name", "kvalifikace", "name_q"]
        )
        mandatory_col = self._find_column(
            pos_reqs, ["is_mandatory", "mandatory", "povinne"]
        )

        for _, row in pos_reqs.iterrows():
            q_id = self._norm_id(row.get(qid_col_req)) if qid_col_req else ""
            q_name = str(row.get(qname_col_req) or q_id or "").strip()
            is_mandatory = bool(row.get(mandatory_col)) if mandatory_col else True

            if q_id and q_id in existing_ids:
                met.append({"id": q_id, "name": q_name})
            else:
                gaps.append(
                    {
                        "id": q_id or None,
                        "name": q_name or "Unknown qualification",
                        "mandatory": is_mandatory,
                    }
                )

        total = len(pos_reqs)
        met_count = len(met)
        missing_count = len(gaps)
        completeness = (met_count / total) if total > 0 else 1.0

        return {
            "position_id": pos_id,
            "position_name": position_name,
            "total_requirements": total,
            "met_count": met_count,
            "missing_count": missing_count,
            "completeness_score": round(completeness * 100, 1),
            "gaps": gaps,
            "met": met,
        }

    def get_team_stats(self) -> Dict[str, Any]:
        """
        Aggregation for Team Dashboard.
        Populates departments from Org Hierarchy if missing in Employee file.
        Aggregates top skills from both Internal courses and Degreed.
        """
        employees = self.data.get("employees", pd.DataFrame())
        if employees.empty:
            return {
                "total_employees": 0,
                "departments": {},
                "positions": {},
                "top_skills": {}
            }

        # 1. Enrich Employees with Department Names
        # If 'department' column is missing or full of nulls, map via Org Hierarchy
        if "department" not in employees.columns or employees["department"].isna().all():
            org = self.data.get("org_hierarchy", pd.DataFrame())
            obj_col = self._find_column(org, ["objid", "org_unit_id", "organizational_unit"])
            dept_col = self._find_column(org, ["stxte", "department", "name_en"])
            emp_ou_col = self._find_column(employees, ["org_unit_id", "org_unit"])

            if not org.empty and obj_col and dept_col and emp_ou_col:
                org = org.copy()
                org[obj_col] = org[obj_col].astype(str).str.strip().apply(self._norm_id)
                mapping = pd.Series(
                    org[dept_col].values, index=org[obj_col]
                ).to_dict()
                
                employees["department"] = (
                    employees[emp_ou_col]
                    .astype(str)
                    .str.strip()
                    .apply(self._norm_id)
                    .map(mapping)
                )

        # 2. Stats Containers
        stats = {
            "total_employees": len(employees),
            "departments": {},
            "positions": {},
            "top_skills": {}
        }

        # Departments
        if "department" in employees.columns:
            stats["departments"] = (
                employees["department"].fillna("Unknown").value_counts().to_dict()
            )
        
        # Positions
        pos_col = self._find_column(employees, ["position_name", "planned_profession", "job_title"])
        if pos_col:
            stats["positions"] = (
                employees[pos_col].fillna("Unknown").value_counts().to_dict()
            )

        # 3. Top Skills (Internal + Degreed)
        all_skills = []
        
        # A. Internal Courses
        internal = self.data.get("internal_courses", pd.DataFrame())
        int_col = self._find_column(internal, ["event_name", "oznaceni_typu_akce", "course_name", "nazev_kurzu"])
        if not internal.empty and int_col:
            vals = internal[int_col].dropna().astype(str).tolist()
            all_skills.extend([v for v in vals if len(v.strip()) > 2])

        # B. Degreed Content
        degreed = self.data.get("degreed", pd.DataFrame())
        deg_col = self._find_column(degreed, ["content_title", "title", "content_name"])
        if not degreed.empty and deg_col:
            vals = degreed[deg_col].dropna().astype(str).tolist()
            all_skills.extend([v for v in vals if len(v.strip()) > 2])

        # Aggregate Top 10
        if all_skills:
            stats["top_skills"] = dict(Counter(all_skills).most_common(10))

        return stats

    # ---------------------------------------------------------------------
    # Internal: skills extraction
    # ---------------------------------------------------------------------

    def _skills_from_internal_courses(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Skills from internal courses ZHRPD_VZD_STA_007.
        """
        internal = self.data.get("internal_courses", pd.DataFrame())
        if internal.empty:
            return []

        internal = internal.copy()
        pn_col = self._find_column(internal, ["personal_number"])
        if pn_col is None:
            return []

        internal[pn_col] = internal[pn_col].astype(str).str.strip()
        internal[pn_col] = internal[pn_col].apply(self._norm_id)
        
        # Use .copy() to avoid SettingWithCopyWarning
        emp_int = internal[internal[pn_col] == self._norm_id(employee_id)].copy()
        
        if emp_int.empty:
            return []

        name_col = self._find_column(
            emp_int,
            ["event_name", "oznaceni_typu_akce", "course_name", "nazev", "name"],
        )
        date_col = self._find_column(
            emp_int,
            ["end_date", "datum_ukonceni", "datum_ukonceni_kurzu"],
        )
        event_type_col = self._find_column(
            emp_int,
            ["event_type", "typ_akce"],
        )

        skill_mapping = self.data.get("skill_mapping", pd.DataFrame())
        skill_dict_df = self.data.get("skill_dict", pd.DataFrame())

        if event_type_col is None or skill_mapping.empty:
            return self._skills_from_internal_courses_simple(
                emp_int, name_col, date_col, event_type_col
            )

        mapping = skill_mapping.copy()
        map_idobj_col = self._find_column(mapping, ["content_id", "id_objektu", "idobj"])
        map_skill_id_col = self._find_column(mapping, ["skill_id", "id_skillu"])
        map_skill_name_col = self._find_column(mapping, ["skill_name", "skill_v_en"])
        if map_idobj_col is None:
            return self._skills_from_internal_courses_simple(
                emp_int, name_col, date_col, event_type_col
            )

        emp_int[event_type_col] = emp_int[event_type_col].apply(self._norm_id)
        mapping[map_idobj_col] = mapping[map_idobj_col].apply(self._norm_id)

        skill_name_map: Dict[str, str] = {}
        if not skill_dict_df.empty:
            sd = skill_dict_df.copy()
            sd_id_col = self._find_column(sd, ["skill_id"])
            sd_name_col = self._find_column(sd, ["skill_name", "skill_en", "skill"])
            if sd_id_col and sd_name_col:
                sd[sd_id_col] = sd[sd_id_col].apply(self._norm_id)
                for _, r in sd.iterrows():
                    sid = self._norm_id(r.get(sd_id_col))
                    sname = r.get(sd_name_col)
                    if not sid or pd.isna(sname):
                        continue
                    skill_name_map[sid] = str(sname).strip()

        mapping_skill_name_map: Dict[str, str] = {}
        if map_skill_id_col and map_skill_name_col:
            tmp = mapping[[map_skill_id_col, map_skill_name_col]].dropna()
            for _, r in tmp.iterrows():
                sid = self._norm_id(r.get(map_skill_id_col))
                sname = str(r.get(map_skill_name_col) or "").strip()
                if sid and sname and sid not in mapping_skill_name_map:
                    mapping_skill_name_map[sid] = sname

        merged = emp_int.merge(
            mapping,
            how="left",
            left_on=event_type_col,
            right_on=map_idobj_col,
        )

        skills: List[Dict[str, Any]] = []

        for _, row in merged.iterrows():
            course_name = str(row.get(name_col) or "Internal training").strip()
            completion_date = row.get(date_col) if date_col else None

            raw_skill_id = row.get(map_skill_id_col) if map_skill_id_col else None
            skill_id_norm = self._norm_id(raw_skill_id) if raw_skill_id is not None else ""

            skill_category_name = None
            if skill_id_norm:
                skill_category_name = skill_name_map.get(skill_id_norm)
                if not skill_category_name:
                    skill_category_name = mapping_skill_name_map.get(skill_id_norm)

            if not skill_category_name:
                skill_category_name = "none"

            skills.append(
                {
                    "skill": course_name,
                    "level": None,
                    "source": "Internal Course",
                    "source_name": course_name,
                    "date": completion_date,
                    "category": skill_category_name,
                }
            )

        return skills

    def _skills_from_internal_courses_simple(
        self,
        emp_int: pd.DataFrame,
        name_col: Optional[str],
        date_col: Optional[str],
        event_type_col: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Fallback extraction when no skill mapping is available.
        """
        skills: List[Dict[str, Any]] = []
        for _, row in emp_int.iterrows():
            course_name = str(row.get(name_col) or "Internal training").strip()
            category = (
                str(row.get(event_type_col)).strip()
                if event_type_col and pd.notna(row.get(event_type_col))
                else ""
            )
            skill_item: Dict[str, Any] = {
                "skill": course_name,
                "level": None,
                "source": "Internal Course",
                "source_name": course_name,
                "date": row.get(date_col) if date_col else None,
            }
            if category:
                skill_item["category"] = category
            skills.append(skill_item)
        return skills

    def _skills_from_degreed(
        self, profile: Dict[str, Any], employee_id: str
    ) -> List[Dict[str, Any]]:
        """
        Skills from Degreed + Degreed_Content_Catalog.
        """
        degreed = self.data.get("degreed", pd.DataFrame())
        if degreed.empty:
            return []

        login_value: Optional[str] = None
        employees = self.data.get("employees", pd.DataFrame())
        if not employees.empty:
            employees = employees.copy()
            pn_emp_col = self._find_column(employees, ["personal_number"])
            if pn_emp_col:
                employees[pn_emp_col] = employees[pn_emp_col].astype(str).str.strip()
                employees[pn_emp_col] = employees[pn_emp_col].apply(self._norm_id)
                emp_row = employees[employees[pn_emp_col] == self._norm_id(employee_id)]
                if not emp_row.empty:
                    login_col = self._find_column(
                        employees,
                        ["name", "user_name", "persstat_start_month_user_name"],
                    )
                    if login_col and login_col in emp_row.columns:
                        raw_login = emp_row.iloc[0][login_col]
                        if pd.notna(raw_login):
                            login_value = str(raw_login).strip()

        degreed = degreed.copy()
        emp_deg = pd.DataFrame()

        deg_emp_col = self._find_column(degreed, ["employee_id", "personal_number"])
        if login_value and deg_emp_col:
            degreed[deg_emp_col] = (
                degreed[deg_emp_col]
                .astype(str)
                .str.strip()
                .str.split("@")
                .str[0]
                .str.lower()
            )
            login_norm = str(login_value).strip().split("@")[0].lower()
            emp_deg = degreed[degreed[deg_emp_col] == login_norm]

        if emp_deg.empty and profile.get("employee_id") and deg_emp_col:
            profile_login_norm = str(profile["employee_id"]).strip().split("@")[0].lower()
            emp_deg = degreed[degreed[deg_emp_col] == profile_login_norm]

        if emp_deg.empty:
            deg_pn_col = self._find_column(degreed, ["pernr", "id_p"])
            if deg_pn_col:
                degreed[deg_pn_col] = degreed[deg_pn_col].astype(str).str.strip()
                degreed[deg_pn_col] = degreed[deg_pn_col].apply(self._norm_id)
                emp_deg = degreed[degreed[deg_pn_col] == self._norm_id(employee_id)]

        if emp_deg.empty:
            return []

        results: List[Dict[str, Any]] = []

        skill_dict = self.data.get("degreed_skill_dict", pd.DataFrame())
        deg_skill_map: Dict[str, str] = {}
        if not skill_dict.empty:
            skill_dict = skill_dict.copy()
            sid_col = self._find_column(skill_dict, ["skill_id"])
            sname_col = self._find_column(skill_dict, ["skill_name", "skill_en", "name"])
            if sid_col and sname_col:
                skill_dict[sid_col] = skill_dict[sid_col].apply(self._norm_id)
                for _, row in skill_dict.iterrows():
                    sid = row.get(sid_col)
                    name = row.get(sname_col)
                    if pd.isna(sid) or pd.isna(name):
                        continue
                    sid_norm = self._norm_id(sid)
                    if not sid_norm:
                        continue
                    deg_skill_map[sid_norm] = str(name).strip()

        deg_cat = self.data.get("degreed_content", pd.DataFrame())
        if not deg_cat.empty:
            deg_cat = deg_cat.copy()
            cat_content_col = self._find_column(deg_cat, ["content_id"])
            deg_content_col = self._find_column(emp_deg, ["content_id", "idobj", "course_id"])

            if cat_content_col and deg_content_col:
                deg_cat[cat_content_col] = deg_cat[cat_content_col].apply(self._norm_id)
                emp_deg[deg_content_col] = emp_deg[deg_content_col].apply(self._norm_id)

                merged = pd.merge(
                    emp_deg,
                    deg_cat,
                    left_on=deg_content_col,
                    right_on=cat_content_col,
                    how="left",
                )

                skill_cols = [c for c in merged.columns if c.startswith("skill_")]
                category_cols = [c for c in merged.columns if c.startswith("category_")]
                group_cols = [c for c in merged.columns if c.startswith("group_")]

                title_col = self._find_column(merged, ["content_title", "title"])
                date_col = self._find_column(merged, ["completion_date", "completed_date"])

                for _, row in merged.iterrows():
                    base_name = (
                        row.get(title_col)
                        or row.get("content_title")
                        or row.get(deg_content_col)
                    )
                    completion_date = row.get(date_col)

                    cat_values: List[str] = []
                    for col in category_cols:
                        val = row.get(col)
                        if pd.isna(val):
                            continue
                        text = str(val).strip()
                        if text:
                            cat_values.append(text)
                    grp_values: List[str] = []
                    for col in group_cols:
                        val = row.get(col)
                        if pd.isna(val):
                            continue
                        text = str(val).strip()
                        if text:
                            grp_values.append(text)

                    category_value = ""
                    if cat_values:
                        category_value = ", ".join(sorted(set(cat_values)))
                    if grp_values:
                        grp_text = ", ".join(sorted(set(grp_values)))
                        category_value = (
                            f"{category_value} | {grp_text}"
                            if category_value
                            else grp_text
                        )

                    created_skill = False

                    if skill_cols:
                        for col in skill_cols:
                            val = row.get(col)
                            if pd.isna(val):
                                continue
                            raw = str(val).strip()
                            if not raw:
                                continue

                            skill_id_norm = self._norm_id(raw)
                            skill_name = ""
                            if skill_id_norm and deg_skill_map:
                                skill_name = deg_skill_map.get(skill_id_norm, "")

                            if not skill_name:
                                skill_name = raw

                            skill_item: Dict[str, Any] = {
                                "skill": skill_name,
                                "level": None,
                                "source": "Degreed",
                                "source_name": base_name,
                                "date": completion_date,
                            }
                            if category_value:
                                skill_item["category"] = category_value
                            results.append(skill_item)
                            created_skill = True

                    if not created_skill:
                        skill_item = {
                            "skill": str(base_name).strip(),
                            "level": None,
                            "source": "Degreed",
                            "source_name": base_name,
                            "date": completion_date,
                        }
                        if category_value:
                            skill_item["category"] = category_value
                        results.append(skill_item)

                return results

        title_col = self._find_column(emp_deg, ["content_title", "title"])
        date_col = self._find_column(emp_deg, ["completion_date", "completed_date"])

        for _, row in emp_deg.iterrows():
            base_name = str(row.get(title_col) or row.get("content_id") or "Degreed Course").strip()
            results.append(
                {
                    "skill": base_name,
                    "level": None,
                    "source": "Degreed",
                    "source_name": base_name,
                    "date": row.get(date_col),
                }
            )

        return results

    def get_degreed_learning_table(self, employee_id: str) -> pd.DataFrame:
        """
        Builds a compact Degreed learning table for the employee.
        """
        emp_profile = self.get_employee_profile(employee_id)
        if not emp_profile:
            return pd.DataFrame()

        degreed = self.data.get("degreed", pd.DataFrame())
        if degreed.empty:
            return pd.DataFrame()

        login_value: Optional[str] = None
        employees = self.data.get("employees", pd.DataFrame())
        if not employees.empty:
            employees = employees.copy()
            pn_emp_col = self._find_column(employees, ["personal_number"])
            if pn_emp_col:
                employees[pn_emp_col] = employees[pn_emp_col].astype(str).str.strip()
                employees[pn_emp_col] = employees[pn_emp_col].apply(self._norm_id)
                emp_row = employees[employees[pn_emp_col] == self._norm_id(employee_id)]
                if not emp_row.empty:
                    login_col = self._find_column(
                        employees,
                        ["name", "user_name", "persstat_start_month_user_name"],
                    )
                    if login_col and login_col in emp_row.columns:
                        raw_login = emp_row.iloc[0][login_col]
                        if pd.notna(raw_login):
                            login_value = str(raw_login).strip()

        degreed = degreed.copy()
        emp_deg = pd.DataFrame()

        deg_emp_col = self._find_column(degreed, ["employee_id", "personal_number"])
        if login_value and deg_emp_col:
            degreed[deg_emp_col] = (
                degreed[deg_emp_col]
                .astype(str)
                .str.strip()
                .str.split("@")
                .str[0]
                .str.lower()
            )
            login_norm = str(login_value).strip().split("@")[0].lower()
            emp_deg = degreed[degreed[deg_emp_col] == login_norm]

        if emp_deg.empty and emp_profile.get("employee_id") and deg_emp_col:
            profile_login_norm = str(emp_profile["employee_id"]).strip().split("@")[0].lower()
            emp_deg = degreed[degreed[deg_emp_col] == profile_login_norm]

        if emp_deg.empty:
            deg_pn_col = self._find_column(degreed, ["pernr", "id_p"])
            if deg_pn_col:
                degreed[deg_pn_col] = degreed[deg_pn_col].astype(str).str.strip()
                degreed[deg_pn_col] = degreed[deg_pn_col].apply(self._norm_id)
                emp_deg = degreed[degreed[deg_pn_col] == self._norm_id(employee_id)]

        if emp_deg.empty:
            return pd.DataFrame()

        deg_cat = self.data.get("degreed_content", pd.DataFrame())
        merged = emp_deg.copy()

        if not deg_cat.empty:
            deg_cat = deg_cat.copy()
            cat_content_col = self._find_column(deg_cat, ["content_id"])
            deg_content_col = self._find_column(emp_deg, ["content_id", "idobj", "course_id"])
            if cat_content_col and deg_content_col:
                deg_cat[cat_content_col] = deg_cat[cat_content_col].apply(self._norm_id)
                merged[deg_content_col] = merged[deg_content_col].apply(self._norm_id)
                merged = merged.merge(
                    deg_cat,
                    left_on=deg_content_col,
                    right_on=cat_content_col,
                    how="left",
                )

        merged = merged.copy()

        category_cols = [c for c in merged.columns if c.startswith("category_")]
        if category_cols:
            def _join_categories(row):
                values = []
                for col in category_cols:
                    val = row.get(col)
                    if pd.isna(val):
                        continue
                    text = str(val).strip()
                    if text:
                        values.append(text)
                if not values:
                    return ""
                return ", ".join(sorted(set(values)))

            merged["categories"] = merged.apply(_join_categories, axis=1)
        else:
            merged["categories"] = ""

        title_col = self._find_column(merged, ["title", "content_title"])
        provider_col = self._find_column(merged, ["provider", "content_provider"])
        type_col = self._find_column(merged, ["content_type", "type"])
        completion_col = self._find_column(merged, ["completion_date", "completed_date"])
        url_col = self._find_column(merged, ["content_url", "url"])

        minutes_series = None
        if "estimated_learning_minutes" in merged.columns:
            minutes_series = merged["estimated_learning_minutes"]
        if "content_estimated_learning_minutes" in merged.columns:
            if minutes_series is None:
                minutes_series = merged["content_estimated_learning_minutes"]
            else:
                minutes_series = minutes_series.where(
                    minutes_series.notna(),
                    merged["content_estimated_learning_minutes"],
                )
        if minutes_series is None:
            merged["minutes"] = None
        else:
            merged["minutes"] = minutes_series

        data = {}
        if completion_col:
            data["completed_date"] = merged[completion_col]
        if title_col:
            data["title"] = merged[title_col]
        if provider_col:
            data["provider"] = merged[provider_col]
        if type_col:
            data["content_type"] = merged[type_col]
        data["minutes"] = merged["minutes"]
        data["categories"] = merged["categories"]
        if url_col:
            data["url"] = merged[url_col]

        result = pd.DataFrame(data)
        if not result.empty and "completed_date" in result.columns:
            try:
                result["completed_date"] = pd.to_datetime(
                    result["completed_date"], errors="coerce"
                )
                result = result.sort_values("completed_date", ascending=False)
            except Exception:
                pass

        return result