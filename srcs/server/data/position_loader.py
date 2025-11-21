class QualificationLoader:
    pass


"""
Utilities for loading employee data from external sources.
"""

from __future__ import annotations

from typing import List, Dict, Any

import pandas as pd

from models.qualification import Qualification
from srcs.server.models.position import Position

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


class PositionLoader:
    """Loader capable of transforming Excel rows into `Position` objects."""

    def __init__(self) -> None:
        # Precompute mapping for speed
        self.column_to_field = COLUMN_TO_FIELD

    def load_from_excel(self, file_path: str) -> Dict[str, Position]:
        """Read an Excel file and return a dict keyed by course ID."""
        df = pd.read_excel(file_path, dtype=str)
        positions: Dict[str, Position] = {}
        for _, row in df.iterrows():
            try:
                pos = self.__row_to_position(row)
                positions[pos.id] = pos
            except Exception:
                # Skip problematic rows; consider logging in real code
                continue
        return positions

    def __row_to_position(self, row: Any) -> Position:
        """Convert a single row (Series or dict) to Position using mapping."""
        if REQUIRED_EXCEL_COL not in row or pd.isna(row[REQUIRED_EXCEL_COL]):
            raise ValueError("Row missing required course ID column")

        data: Dict[str, Any] = {}
        for excel_col, field in self.column_to_field.items():
            if excel_col in row and not pd.isna(row[excel_col]):
                data[field] = row[excel_col]

        return Position(**data)  # type: ignore[arg-type]

