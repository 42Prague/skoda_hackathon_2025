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
from .action_type_loader import ActionTypeLoader
from models.action_type_record import ActionTypeRecord

class DataAccesser:
    """Lightweight accessor for ERP employee data."""

    def __init__(self) -> None:  # noqa: D401 (simple description OK)
        # Keyed by `personal_number` (string).
        self.__employees_loader = EmployeeLoader()
        self.__qualifications_loader = QualificationLoader()
        self.__past_qualifications_loader = PastQualificationLoader()
        self.__action_types_loader = ActionTypeLoader()
        self.__action_types : List[ActionTypeRecord] = {}
        self.__employees_by_personal_number: Dict[str, Employee] = {}
        self.__qualifications_by_course_id: Dict[str, Qualification] = {}
        self.__past_qualifications: Dict[str, List[Qualification]] = {}
        print("Loading employee data from Excel...")
        self.__employees_by_personal_number = self.__employees_loader.load_from_excel(
            "../data/erp_employee_data.xlsx"
        )
        # print("Loading qualification data from Excel...")
        # self.__qualifications_by_course_id = self.__qualifications_loader.load_from_excel(
        #     "data/erp_qualification_data.xlsx"
        # )
        print("Loading past qualification data from Excel...")
        self.__past_qualifications = self.__past_qualifications_loader.load(
            "../data/past_qual.xlsx"
        )
        print("Loading action type data from Excel...")
        self.__action_types = self.__action_types_loader.load(
            "../data/erp_action_type_data.xlsx"
        )

    def get_all_employees(self) -> List[Employee]:
        """Return all loaded Employee records."""
        
        
        return list(self.__employees_by_personal_number.values())
    
    def get_employee_data(self, employee_id: int) -> Optional[Employee]:
        """Return the Employee record for a given *personal number*.

        Args:
            employee_id: Personal number identifier received from ERP.

        Returns:
            The corresponding `Employee` dataclass instance, or `None`
            if the personal number is not in the local index.
        """
        return self.__employees_by_personal_number.get(str(employee_id))

    def get_all_employees(self, limit: Optional[int] = None, debug_print: bool = True) -> List[Employee]:
        """Return all loaded Employee objects; optionally print first 5.

        Args:
            limit: If provided, slice the returned list to this size.
            debug_print: When True, print first 5 employees for quick inspection.
        """
        employees = list(self.__employees_by_personal_number.values())
        # if debug_print:
        #     print("-- First 5 employees (debug) --")
        #     for emp in employees[:5]:
        #         # Safely access optional attributes
        #         name = getattr(emp, 'user_name', getattr(emp, 'name', ''))
        #         print(f"personal_number={emp.personal_number} name={name} position={getattr(emp,'position','')} skills={getattr(emp,'skills', [])}")
        #     print("-- End preview --")
        return employees

    def get_qualifications(self) -> int:
        """Return the total number of qualification records loaded."""
        return len(self.__qualifications_by_course_id)

    def get_qualification_by_employee(self, employee_id: str) -> List[Qualification]:
        """Return the Qualification record for a given employee ID."""
        return self.__past_qualifications.get(employee_id)
    
    def get_action_types(self) -> Dict[str, ActionTypeRecord]:
        """Return all loaded action type records."""
        return self.__action_types
    
    def get_employee_qualifications(self, employee_id: int) -> List[Qualification]:
        """Return the Qualification record for a given employee ID."""
        return self.__past_qualifications.get(str(employee_id), [])
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