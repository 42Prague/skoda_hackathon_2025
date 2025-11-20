"""
Data access layer for Employee records.

For now this is an in-memory stub. Replace with a real data source
(DB, API, CSV import, etc.) when available.
"""

from typing import Dict, Optional

from models.employee import Employee


class DataAccesser:
    """Lightweight accessor for ERP employee data."""

    def __init__(self) -> None:  # noqa: D401 (simple description OK)
        # Keyed by `personal_number` (string).
        self._employees_by_personal_number: Dict[str, Employee] = {}

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def load_from_excel(self, file_path: str) -> int:
        """Load employee records from an Excel spreadsheet.

        The Excel file must contain columns whose headers exactly match the
        field names of the `Employee` dataclass (e.g. ``personal_number``,
        ``profession``, etc.).  Extra columns are ignored; missing columns
        default to ``None``.

        Args:
            file_path: Path to the ``.xlsx`` file.

        Returns:
            Number of employee rows successfully loaded into the in-memory
            cache.
        """
        try:
            from .loader import load_employees_from_excel  # local import to avoid cycles
        except ImportError as exc:
            raise ImportError("pandas + openpyxl are required for Excel loading: pip install pandas openpyxl") from exc

        employees = load_employees_from_excel(file_path)
        for emp in employees:
            self.cache_employee(emp)
        return len(employees)
    def get_employee_data(self, employee_id: int) -> Optional[Employee]:
        """Return the Employee record for a given *personal number*.

        Args:
            employee_id: Personal number identifier received from ERP.

        Returns:
            The corresponding `Employee` dataclass instance, or `None`
            if the personal number is not in the local index.
        """
        return self._employees_by_personal_number.get(str(employee_id))

    # ------------------------------------------------------------------
    # Convenience helpers (optional; extend as needed)
    # ------------------------------------------------------------------
    def cache_employee(self, employee: Employee) -> None:
        """Add or update a record in the in-memory index."""
        self._employees_by_personal_number[employee.personal_number] = employee

    def clear_cache(self) -> None:
        """Remove all cached employee records (testing / reload helper)."""
        self._employees_by_personal_number.clear()
