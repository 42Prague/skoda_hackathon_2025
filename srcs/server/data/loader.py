"""
Utilities for loading employee data from external sources.
"""

from __future__ import annotations

from typing import List, Dict, Any

import pandas as pd

from models.employee import Employee


# Mapping from Excel column headers to Employee dataclass field names
COLUMN_TO_FIELD = {
    "persstat_start_month.personal_number": "personal_number",
    "persstat_start_month.ob1": "persstat_ob1",
    "persstat_start_month.ob2": "persstat_ob2",
    "persstat_start_month.ob3": "persstat_ob3",
    "persstat_start_month.ob5": "persstat_ob5",
    "persstat_start_month.ob8": "persstat_ob8",
    "persstat_start_month.coordinator_group_id": "coordinator_group_id",
    "persstat_start_month.profession_id": "profession_id",
    "persstat_start_month.profession": "profession",
    "persstat_start_month.planned_profession_id": "planned_profession_id",
    "persstat_start_month.planned_profession": "planned_profession",
    "persstat_start_month.planned_position_id": "planned_position_id",
    "persstat_start_month.planned_position": "planned_position",
    "persstat_start_month.basic_branch_of_education_group": "basic_branch_of_education_group",
    "persstat_start_month.basic_branch_of_education_grou2": "basic_branch_of_education_group2",
    "persstat_start_month.basic_branch_of_education_id": "basic_branch_of_education_id",
    "persstat_start_month.basic_branch_of_education_name": "basic_branch_of_education_name",
    "persstat_start_month.education_category_id": "education_category_id",
    "persstat_start_month.education_category_name": "education_category_name",
    "persstat_start_month.field_of_study_id": "field_of_study_id",
    "persstat_start_month.field_of_study_name": "field_of_study_name",
    "persstat_start_month.field_of_stude_code_ispv": "field_of_study_code_ispv",
    "persstat_start_month.user_name": "user_name",
}

REQUIRED_EXCEL_COL = "persstat_start_month.personal_number"


def _row_to_employee(row: Dict[str, Any]) -> Employee:
    """Convert a single DataFrame row into an Employee instance using mapping."""
    if REQUIRED_EXCEL_COL not in row or pd.isna(row[REQUIRED_EXCEL_COL]):
        raise ValueError("Row missing required personal number column")

    kwargs: Dict[str, Any] = {}
    for excel_col, field_name in COLUMN_TO_FIELD.items():
        if excel_col in row:
            kwargs[field_name] = row[excel_col]
    # Derive simple int employee_id from personal_number if numeric
    personal_no = str(kwargs["personal_number"])
    if personal_no.isdigit():
        kwargs["employee_id"] = int(personal_no)

    return Employee(**kwargs)  # type: ignore[arg-type]


def load_employees_from_excel(file_path: str) -> List[Employee]:
    """Load employees from an Excel (.xlsx) file.

    The sheet must contain at least a column named ``personal_number``.
    Other columns matching `Employee` field names are mapped automatically.
    Unknown columns are ignored.
    """
    df = pd.read_excel(file_path, dtype=str)
    employees: List[Employee] = []
    for _, row in df.iterrows():
        try:
            emp = _row_to_employee(row)
            employees.append(emp)
        except Exception:
            # Skip invalid rows; in production you might log this.
            continue
    return employees
