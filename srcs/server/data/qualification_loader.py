class QualificationLoader:
    pass


"""
Utilities for loading employee data from external sources.
"""

from typing import List, Dict, Any

import pandas as pd

from models.qualification import Qualification

# ---------------------------------------------------------------------------
# Column mapping
# ---------------------------------------------------------------------------
COLUMN_TO_FIELD = {
    "ID Kurzu": "course_id",
    "Zkratka D": "course_code",
    "Název D": "course_name",
    "Téma": "topic",
    "Oddělení": "department",
    "Kontaktní osoba": "contact_person",
    "Počát.datum": "start_date",
    "Koncové datum": "end_date",
    "ID Skillu": "skill_id",
    "Skill v EN": "skill_name_en",
}

REQUIRED_EXCEL_COL = "ID Kurzu"


class QualificationLoader:
    """Loader capable of transforming Excel rows into `Qualification` objects."""

    def __init__(self) -> None:
        # Precompute mapping for speed
        self.column_to_field = COLUMN_TO_FIELD

    def load_from_excel(self, file_path: str) -> Dict[str, Qualification]:
        """Read an Excel file and return a dict keyed by course ID."""
        df = pd.read_excel(file_path, dtype=str)
        qualifications: Dict[str, Qualification] = {}
        for _, row in df.iterrows():
            try:
                qual = self.__row_to_qualification(row)
                qualifications[qual.course_id] = qual
            except Exception:
                # Skip problematic rows; consider logging in real code
                continue
        return qualifications

    def __row_to_qualification(self, row: Any) -> Qualification:
        """Convert a single row (Series or dict) to Qualification using mapping."""
        if REQUIRED_EXCEL_COL not in row or pd.isna(row[REQUIRED_EXCEL_COL]):
            raise ValueError("Row missing required course ID column")

        data: Dict[str, Any] = {}
        for excel_col, field in self.column_to_field.items():
            if excel_col in row and not pd.isna(row[excel_col]):
                data[field] = row[excel_col]

        return Qualification(**data)  # type: ignore[arg-type]

