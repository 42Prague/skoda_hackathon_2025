from typing import Optional

from models.employee import Employee


class DataAccesser:
    """Data access layer for Employee Skills Analyzer.

    For now this class acts as an in-memory stub. Later it can
    be extended to fetch data from real data sources (DB, API, files).
    """

    def __init__(self) -> None:
        # In a real implementation this would be replaced with
        # a DB connection or another data source. For now we
        # keep an in-memory index keyed by personal_number.
        self._employees_by_personal_number: dict[str, EmployeeDataRecord] = {}

    def get_employee_data(self, employee_id: int) -> Optional[Employee]:
        """Return Employee object for given personal_number.

        Args:
            employee_id: Personal number of the employee (ERP identifier).

        Returns:
            Employee instance or None if not found.
        """
        record = self._employees_by_personal_number.get(str(employee_id))
        if not record:
            return None

        # Map ERP record into existing Employee domain model.
        position = record.profession or "Unknown"
        department = record.basic_branch_of_education_name or "Unknown"

        return Employee(
            name=record.personal_number,
            position=position,
            skills=[],
            experience_years=0,
            department=department,
        )
