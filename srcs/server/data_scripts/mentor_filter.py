import pandas as pd
import numpy as np
import ast
from typing import List, Optional, Dict, Any, Tuple

# --------------------------------------------------
# 1. Load and prepare core datasets
# --------------------------------------------------

def load_employee_skills(skill_positions_path: str = "employee_skill_positions.csv") -> pd.DataFrame:
    df = pd.read_csv(skill_positions_path)
    df["employee_id"] = df["employee_id"].astype(str)
    df["cluster_kmeans"] = df["cluster_kmeans"].astype(str)
    return df

def load_employee_indicators(diagrams_path: str = "employee_diagrams.csv") -> pd.DataFrame:
    df = pd.read_csv(diagrams_path)
    df["employee_id"] = df["employee_id"].astype(str)
    # Rename columns to more consistent names
    df = df.rename(columns={
        "breadth": "skill_breadth",
        "depth": "skill_depth",
        "learning_intensity": "learning_intensity",
        "qualification_strength": "qualification_strength",
        "job_requirement_coverage": "job_requirement_coverage",
        "skill_gap_index": "skill_gap_index",
        "recent_learning_index": "recent_learning_index",
    })
    # If you have organization/position here, keep their names.
    # For demo, assume columns 'organization' and 'position_id' exist or add them later.
    return df

def load_employee_qualifications(quals_emp_path: str = "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx") -> pd.DataFrame:
    df = pd.read_excel(quals_emp_path)
    df = df.rename(columns={
        "ID P": "employee_id",
        "ID Q": "qualification_id",
        "Název Q": "qualification_name",
    })
    df["employee_id"] = df["employee_id"].astype(str)
    df["qualification_id"] = df["qualification_id"].astype(str)
    return df

def load_position_requirements(qual_req_path: str = "ZPE_KOM_KVAL.xlsx") -> pd.DataFrame:
    df = pd.read_excel(qual_req_path)
    df = df.rename(columns={
        "ID kvalifikace": "qualification_id",
        "Kvalifikace": "qualification_name",
        "Číslo FM": "position_id",
    })
    df["qualification_id"] = df["qualification_id"].astype(str)
    df["position_id"] = df["position_id"].astype(str)
    return df

def load_org_hierarchy(org_path: str = "RLS.sa_org_hierarchy - SE.xlsx") -> pd.DataFrame:
    df = pd.read_excel(org_path)
    df = df.rename(columns={
        "sa_org_hierarchy.objid": "org_id",
        "sa_org_hierarchy.paren": "parent_org_id",
        "sa_org_hierarchy.short": "org_short",
        "sa_org_hierarchy.stxtc": "org_name_cs",
        "sa_org_hierarchy.stxtd": "org_name_de",
        "sa_org_hierarchy.stxte": "org_name_en",
    })
    df["org_id"] = df["org_id"].astype(str)
    df["parent_org_id"] = df["parent_org_id"].astype(str)
    return df

def parse_top_skills(cell, max_skills: int = 5) -> str:
    """
    Parse top_skills_tfidf string into a readable string of top skill names.
    """
    if pd.isna(cell):
        return ""
    try:
        lst = ast.literal_eval(str(cell))
        names = [s for s, w in lst[:max_skills] if isinstance(s, str)]
        return ", ".join(names)
    except Exception:
        return ""

def build_employee_master(
    skill_positions_path: str = "employee_skill_positions.csv",
    diagrams_path: str = "employee_diagrams.csv",
    quals_emp_path: str = "ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx",
    qual_req_path: str = "ZPE_KOM_KVAL.xlsx",
) -> Dict[str, pd.DataFrame]:
    """
    Build a master employee dataframe and supporting tables.

    Returns a dict with:
      - employees: merged indicators + skill positions
      - employee_quals: per-qualification rows
      - employee_qual_sets: employee_id -> set of qualification_ids
      - position_req: position -> required qualifications
    """
    # Load core
    skills_df = load_employee_skills(skill_positions_path)
    indicators_df = load_employee_indicators(diagrams_path)
    quals_emp_df = load_employee_qualifications(quals_emp_path)
    position_req_df = load_position_requirements(qual_req_path)

    # Merge skills + indicators
    emp_df = indicators_df.merge(
        skills_df,
        on="employee_id",
        how="left"
    )

    # Parse top skills short if not present
    if "top_skills_tfidf" in emp_df.columns and "top_skills_short" not in emp_df.columns:
        emp_df["top_skills_short"] = emp_df["top_skills_tfidf"].apply(parse_top_skills)

    # Build qualification sets
    emp_qual_sets = (
        quals_emp_df
        .groupby("employee_id")["qualification_id"]
        .apply(lambda q: set(q.astype(str).tolist()))
        .reset_index()
        .rename(columns={"qualification_id": "qual_set"})
    )

    # Attach to employee master
    emp_df = emp_df.merge(
        emp_qual_sets,
        on="employee_id",
        how="left"
    )
    emp_df["qual_set"] = emp_df["qual_set"].apply(lambda x: x if isinstance(x, set) else set())

    return {
        "employees": emp_df,
        "employee_quals": quals_emp_df,
        "employee_qual_sets": emp_qual_sets,
        "position_req": position_req_df,
    }

# --------------------------------------------------
# 2. Helper: required qualifications for a position
# --------------------------------------------------

def get_required_qualifications_for_position(
    position_id: str,
    position_req_df: pd.DataFrame
) -> List[str]:
    subset = position_req_df[position_req_df["position_id"] == str(position_id)]
    return sorted(subset["qualification_id"].unique().tolist())

# --------------------------------------------------
# 3. Mentor search logic
# --------------------------------------------------

def compute_qualification_match_fraction(
    emp_qual_set: set,
    required_quals: set
) -> float:
    if not required_quals:
        return 0.0
    if not isinstance(emp_qual_set, set):
        return 0.0
    return len(emp_qual_set & required_quals) / len(required_quals)

def compute_mentor_score(row) -> float:
    """
    Simple heuristic to rank mentors.
    You can tweak this scoring.
    """
    coverage = float(row.get("job_requirement_coverage", 0) or 0)
    depth = float(row.get("skill_depth", 0) or 0)
    qual_strength = float(row.get("qualification_strength", 0) or 0)
    gap = float(row.get("skill_gap_index", 0) or 0)
    recent_learning = float(row.get("recent_learning_index", 0) or 0)
    qual_match = float(row.get("qual_match_fraction", 0) or 0)

    # Example weighted sum
    score = (
        0.30 * coverage +
        0.20 * depth +
        0.15 * qual_strength +
        0.10 * recent_learning +
        0.15 * qual_match -
        0.10 * gap
    )
    return score

def find_mentors_for_employee(
    mentee_id: str,
    data: Dict[str, pd.DataFrame],
    *,
    # Org / position filters
    same_org_only: bool = True,
    same_cluster_only: bool = False,
    cluster_radius: Optional[float] = None,  # UMAP distance threshold
    # Target position qualification-based filter
    target_position_id: Optional[str] = None,
    min_qual_match_fraction: float = 0.0,
    # Indicator thresholds
    min_skill_depth: Optional[float] = None,
    min_job_coverage: Optional[float] = None,
    max_skill_gap: Optional[float] = None,
    min_recent_learning: Optional[float] = None,
    # Skill keyword filter
    skill_keywords: Optional[List[str]] = None,
    # Max results
    top_n: int = 50
) -> pd.DataFrame:
    """
    Find mentor candidates for a given mentee.

    Parameters:
    - mentee_id: employee_id of the mentee
    - data: dict returned by build_employee_master
    - same_org_only: restrict mentors to the same organization as mentee (if org column exists)
    - same_cluster_only: restrict mentors to the same skill cluster_kmeans
    - cluster_radius: if set, use UMAP distance to find mentors near mentee in skill space
    - target_position_id: if set, use ZPE_KOM_KVAL to weigh qualification match
    - min_qual_match_fraction: minimum fraction of target position qualifications a mentor must have (0–1)
    - min_* / max_*: indicator-based thresholds
    - skill_keywords: list of skill keywords to filter mentors by (OR logic)
    - top_n: maximum number of mentors to return
    """

    emp_df = data["employees"].copy()
    position_req_df = data["position_req"]

    mentee_id = str(mentee_id)
    mentee_row = emp_df[emp_df["employee_id"] == mentee_id].head(1)
    if mentee_row.empty:
        raise ValueError(f"Mentee {mentee_id} not found in employee data.")

    mentee = mentee_row.iloc[0]

    # Start with all other employees as potential mentors
    df = emp_df[emp_df["employee_id"] != mentee_id].copy()

    # 1) Same organization filter (if available)
    if same_org_only and "organization" in df.columns and "organization" in mentee.index:
        org = mentee["organization"]
        df = df[df["organization"] == org]

    # 2) Skill cluster / UMAP proximity filters
    if same_cluster_only:
        mentee_cluster = str(mentee["cluster_kmeans"])
        df = df[df["cluster_kmeans"] == mentee_cluster]

    if cluster_radius is not None:
        if "x" in df.columns and "y" in df.columns:
            mx, my = float(mentee["x"]), float(mentee["y"])
            dx = df["x"] - mx
            dy = df["y"] - my
            dist2 = dx * dx + dy * dy
            df = df[dist2 <= cluster_radius * cluster_radius]

    # 3) Skill keyword filter (simple OR)
    if skill_keywords:
        skill_col = df["skill"].fillna("").astype(str).str.lower()
        mask = pd.Series(False, index=df.index)
        for kw in skill_keywords:
            kw_lower = str(kw).lower()
            mask |= skill_col.str.contains(kw_lower)
        df = df[mask]

    # 4) Indicator filters
    def apply_min(colname: str, min_val: Optional[float]):
        nonlocal df
        if min_val is not None and colname in df.columns:
            df = df[df[colname] >= min_val]

    def apply_max(colname: str, max_val: Optional[float]):
        nonlocal df
        if max_val is not None and colname in df.columns:
            df = df[df[colname] <= max_val]

    apply_min("skill_depth", min_skill_depth)
    apply_min("job_requirement_coverage", min_job_coverage)
    apply_min("recent_learning_index", min_recent_learning)
    apply_max("skill_gap_index", max_skill_gap)

    # 5) Qualification match versus target position
    if target_position_id is not None:
        required_quals = set(
            get_required_qualifications_for_position(
                position_id=str(target_position_id),
                position_req_df=position_req_df
            )
        )
    else:
        required_quals = set()

    if required_quals:
        req_count = len(required_quals)

        def qual_match_fraction(qual_set):
            if not isinstance(qual_set, set) or req_count == 0:
                return 0.0
            return len(qual_set & required_quals) / req_count

        df["qual_match_fraction"] = df["qual_set"].apply(qual_match_fraction)
        df = df[df["qual_match_fraction"] >= min_qual_match_fraction]
    else:
        df["qual_match_fraction"] = 0.0

    # 6) Compute mentor score and sort
    df["mentor_score"] = df.apply(compute_mentor_score, axis=1)
    df = df.sort_values("mentor_score", ascending=False)

    if top_n is not None:
        df = df.head(top_n)

    # 7) Select columns to return
    cols_to_show = [
        "employee_id",
        "organization" if "organization" in df.columns else None,
        "position_id" if "position_id" in df.columns else None,
        "cluster_kmeans",
        "skill_breadth",
        "skill_depth",
        "learning_intensity",
        "qualification_strength",
        "job_requirement_coverage",
        "skill_gap_index",
        "recent_learning_index",
        "qual_match_fraction",
        "mentor_score",
        "top_skills_short" if "top_skills_short" in df.columns else None,
    ]
    cols_to_show = [c for c in cols_to_show if c is not None and c in df.columns]

    return df[cols_to_show]

# --------------------------------------------------
# 4. Example usage
# --------------------------------------------------

if __name__ == "__main__":
    # Build master data once
    data = build_employee_master(
        skill_positions_path="employee_skill_positions.csv",
        diagrams_path="employee_diagrams.csv",
        quals_emp_path="ZHRPD_VZD_STA_016_RE_RHRHAZ00.xlsx",
        qual_req_path="ZPE_KOM_KVAL.xlsx",
    )

    example_mentee_id = "4241"        # replace with a real employee_id
    example_target_position = "20002503"  # from your ZPE_KOM_KVAL sample

    mentors = find_mentors_for_employee(
        mentee_id=example_mentee_id,
        data=data,
        same_org_only=True,
        same_cluster_only=True,
        cluster_radius=None,           # or e.g., 1.0 if you want UMAP distance filter
        target_position_id=example_target_position,
        min_qual_match_fraction=0.5,
        min_skill_depth=5.0,
        min_job_coverage=3.0,
        max_skill_gap=8.0,
        min_recent_learning=2.0,
        skill_keywords=None,           # e.g. ["ai", "cloud"]
        top_n=20
    )

    print("Mentor candidates for mentee", example_mentee_id)
    print(mentors.head())
