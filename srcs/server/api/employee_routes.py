"""
Employee API Routes
Handles all employee-related endpoints
"""

from flask import Blueprint
from services.employee_service import EmployeeService
from utils.response_helpers import success_response, error_response
from data.data_accesser import g_data_accesser

employee_bp = Blueprint('employees', __name__)

# Initialize service
employee_service = EmployeeService()

@employee_bp.route('', methods=['GET'])
def get_all_employees():
    """Get all employees with optional filtering"""
    try:
        # Get query parameters for filtering
        employees = g_data_accesser.get_all_employees()
        
        return success_response(
            data=employees,
            message=f"Found {len(employees)} employees"
        )
        
    except Exception as e:
        return error_response(str(e), 500)