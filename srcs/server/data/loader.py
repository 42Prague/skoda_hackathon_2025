"""
Utilities for loading employee data from external sources.
"""

from __future__ import annotations

from typing import List, Dict, Any

import pandas as pd

from models.employee import Employee

# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------
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


class EmployeeLoader:
    """Loader capable of transforming Excel rows into `Employee` objects."""

    def __init__(self) -> None:
        # Precompute mapping for speed
        self.column_to_field = COLUMN_TO_FIELD

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_from_excel(self, file_path: str) -> Dict[str, Employee]:
        """Read an Excel file and return a dict keyed by personal number."""
        df = pd.read_excel(file_path, dtype=str)
        employees: Dict[str, Employee] = {}
        for _, row in df.iterrows():
            try:
                emp = self._row_to_employee(row)
                employees[emp.personal_number] = emp
            except Exception:
                # Skip problematic rows; consider logging in real code
                continue
        return employees

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _row_to_employee(self, row: Any) -> Employee:
        """Convert a single row (Series or dict) to Employee using mapping."""
        if REQUIRED_EXCEL_COL not in row or pd.isna(row[REQUIRED_EXCEL_COL]):
            raise ValueError("Row missing required personal number column")

        data: Dict[str, Any] = {}
        for excel_col, field in self.column_to_field.items():
            if excel_col in row and not pd.isna(row[excel_col]):
                data[field] = row[excel_col]

        # If personal_number numeric, set employee_id too
        personal_no = str(data["personal_number"])
        if personal_no.isdigit():
            data["employee_id"] = int(personal_no)

        return Employee(**data)  # type: ignore[arg-type]
