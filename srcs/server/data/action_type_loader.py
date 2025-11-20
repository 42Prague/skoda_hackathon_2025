"""Loader for action type records (Excel) -> Dict[participant_id, List[ActionTypeRecord]]."""
from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd

from models.action_type_record import ActionTypeRecord, CZECH_TO_EN_ACTION_MAP  # type: ignore

REQUIRED_COL = "ID účastníka"  # participant identifier column in Excel

class ActionTypeLoader:
    """Loads action type Excel into structured records grouped by participant_id."""

    def __init__(self) -> None:
        # mapping: source_excel_column -> target_model_field
        self.mapping = CZECH_TO_EN_ACTION_MAP

    def load(self, file_path: str) -> List[ActionTypeRecord]:
        """Read Excel file and build mapping participant_id -> list[ActionTypeRecord]."""
        df = pd.read_excel(file_path, dtype=str)
        records: List[ActionTypeRecord] = []

        for _, row in df.iterrows():
            try:
                rec = self.__row_to_record(row)
            except Exception:
                continue
            records.append(rec)

        return records

    def __row_to_record(self, row: Any) -> ActionTypeRecord:
        if REQUIRED_COL not in row or pd.isna(row[REQUIRED_COL]):
            raise ValueError("Row missing participant ID")

        data: Dict[str, Any] = {}
        for source_col, target_field in self.mapping.items():
            if source_col in row and not pd.isna(row[source_col]):
                data[target_field] = row[source_col]

        # Parse dates using model staticmethod
        if "start_date" in data:
            data["start_date"] = data["start_date"]  # type: ignore
        if "end_date" in data:
            data["end_date"] = data["end_date"]  # type: ignore

        return ActionTypeRecord(**data)  # type: ignore[arg-type]

# Convenience function

def load_action_types(file_path: str) -> Dict[str, List[ActionTypeRecord]]:
    return ActionTypeLoader().load(file_path)
