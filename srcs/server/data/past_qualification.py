"""Loader for past qualification records (Excel) -> Dict[personal_number, List[QualificationRecord]]."""

from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd

from models.qualification_record import (
    QualificationRecord,
    CZECH_TO_EN_FIELD_MAP_QUAL_REC,
)

REQUIRED_COL = "ID P"  # minimal identifier column

class PastQualificationLoader:
    """Loads past qualification XLSX into structured records grouped by personal_number."""

    def __init__(self) -> None:
        self.mapping = CZECH_TO_EN_FIELD_MAP_QUAL_REC

    def load(self, file_path: str) -> Dict[str, List[QualificationRecord]]:
        """Read Excel file and build mapping personal_number -> list[QualificationRecord]."""
        df = pd.read_excel(file_path, dtype=str)
        grouped: Dict[str, List[QualificationRecord]] = {}

        for _, row in df.iterrows():
            try:
                rec = self._row_to_record(row)
            except Exception:
                continue
            grouped.setdefault(rec.personal_number, []).append(rec)

        return grouped

    def _row_to_record(self, row: Any) -> QualificationRecord:
        if REQUIRED_COL not in row or pd.isna(row[REQUIRED_COL]):
            raise ValueError("Row missing personal_number")

        data: Dict[str, Any] = {}
        for source_col, target_field in self.mapping.items():
            if source_col in row and not pd.isna(row[source_col]):
                data[target_field] = row[source_col]

        return QualificationRecord(**data)  # type: ignore[arg-type]

# Convenience function

def load_past_qualifications(file_path: str) -> Dict[str, List[QualificationRecord]]:
    return PastQualificationLoader().load(file_path)
