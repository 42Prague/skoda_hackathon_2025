
"""
Data access layer for Employee records.

For now this is an in-memory stub. Replace with a real data source
(DB, API, CSV import, etc.) when available.
"""

from typing import Dict, Optional, List

from models.employee import Employee
from models.qualification import Qualification
from .loader import EmployeeLoader
from .qualification_loader import QualificationLoader
from .past_qualification import PastQualificationLoader

class DataAccesser:
    """Lightweight accessor for ERP employee data."""

    def __init__(self) -> None:  # noqa: D401 (simple description OK)
        # Keyed by `personal_number` (string).
        self.__employees_loader = EmployeeLoader()
        self.__qualifications_loader = QualificationLoader()
        self.__past_qualifications_loader = PastQualificationLoader()
        self.__employees_by_personal_number: Dict[str, Employee] = {}
        self.__qualifications_by_course_id: Dict[str, Qualification] = {}
        self.__past_qualifications_by_personal_number: Dict[str, List[Qualification]] = {}
        self.__employees_by_personal_number = self.__employees_loader.load_from_excel(
            "data/erp_employee_data.xlsx"
        )
        self.__qualifications_by_course_id = self.__qualifications_loader.load_from_excel(
            "data/erp_qualification_data.xlsx"
        )
        self.__past_qualifications_by_personal_number = self.__past_qualifications_loader.load_from_excel(
            "data/erp_past_qualification_data.xlsx"
        )

    def get_employee_data(self, employee_id: int) -> Optional[Employee]:
        """Return the Employee record for a given *personal number*.

        Args:
            employee_id: Personal number identifier received from ERP.

        Returns:
            The corresponding `Employee` dataclass instance, or `None`
            if the personal number is not in the local index.
        """
        return self.__employees_by_personal_number.get(str(employee_id))


    def get_qualifications(self) -> int:
        """Return the total number of qualification records loaded."""
        return len(self.__qualifications_by_course_id)

    def get_qualification_by_employee(self, employee_id: str) -> List[Qualification]:
        """Return the Qualification record for a given employee ID."""
        return self.__past_qualifications_by_personal_number.get(employee_id)

    # ------------------------------------------------------------------
    # Convenience helpers (optional; extend as needed)
    # ------------------------------------------------------------------
    def cache_employee(self, employee: Employee) -> None:
        """Add or update a record in the in-memory index."""
        self._employees_by_personal_number[employee.personal_number] = employee

    def clear_cache(self) -> None:
        """Remove all cached employee records (testing / reload helper)."""
        self._employees_by_personal_number.clear()


g_data_accesser = DataAccesser()