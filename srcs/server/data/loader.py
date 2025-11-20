"""
Utilities for loading employee data from external sources.
"""

from __future__ import annotations

from typing import List, Dict, Any

import pandas as pd

from models.employee import Employee


EXPECTED_COLUMNS = {field for field in Employee.__dataclass_fields__.keys()}


def _row_to_employee(row: Dict[str, Any]) -> Employee:
    """Convert a single dataframe row (dict-like) into an Employee instance."""
    kwargs = {key: row.get(key) for key in EXPECTED_COLUMNS}
    # Ensure personal_number exists
    if not kwargs.get("personal_number"):
        raise ValueError("Missing required field 'personal_number' in row: %s" % row)
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
