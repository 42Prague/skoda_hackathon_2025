
from models.employee import Employee

class DataAccesser():
    """
    Data access layer for Employee Skills Analyzer
    """
    
    def __init__(self):
        """Initialize data accesser"""
        pass

    def get_employee_data(self, employee_id: int) -> Employee:
        """Retrieve employee data by ID"""
        return Employee(employee_id, "Sample Name", "Sample Dept", ["skill1", "skill2"])