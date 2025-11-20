"""
Employee API Routes
Handles all employee-related endpoints
"""

from flask import Blueprint, request, jsonify
from services.employee_service import EmployeeService
from utils.validators import validate_employee_data
from utils.response_helpers import success_response, error_response

employee_bp = Blueprint('employees', __name__)

# Initialize service
employee_service = EmployeeService()

@employee_bp.route('', methods=['GET'])
def get_all_employees():
    """Get all employees with optional filtering"""
    try:
        # Get query parameters for filtering
        department = request.args.get('department')
        position = request.args.get('position')
        min_experience = request.args.get('min_experience', type=int)
        
        # Get filtered employees
        employees = employee_service.get_employees(
            department=department,
            position=position,
            min_experience=min_experience
        )
        
        return success_response(
            data=employees,
            message=f"Found {len(employees)} employees"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('/<int:employee_id>', methods=['GET'])
def get_employee_by_id(employee_id):
    """Get specific employee by ID"""
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        
        if not employee:
            return error_response("Employee not found", 404)
            
        return success_response(data=employee)
        
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('', methods=['POST'])
def create_employee():
    """Create a new employee"""
    try:
        # Get and validate data
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        # Validate input data
        validation_error = validate_employee_data(data)
        if validation_error:
            return error_response(validation_error, 400)
        
        # Create employee
        employee = employee_service.create_employee(data)
        
        return success_response(
            data=employee,
            message="Employee created successfully",
            status_code=201
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('/<int:employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update existing employee"""
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided", 400)
        
        # Update employee
        employee = employee_service.update_employee(employee_id, data)
        
        if not employee:
            return error_response("Employee not found", 404)
            
        return success_response(
            data=employee,
            message="Employee updated successfully"
        )
        
    except ValueError as e:
        return error_response(str(e), 400)
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('/<int:employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete an employee"""
    try:
        success = employee_service.delete_employee(employee_id)
        
        if not success:
            return error_response("Employee not found", 404)
            
        return success_response(
            message="Employee deleted successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('/<int:employee_id>/skills', methods=['POST'])
def add_skill_to_employee(employee_id):
    """Add skills to an employee"""
    try:
        data = request.get_json()
        skills = data.get('skills', [])
        
        if not skills:
            return error_response("No skills provided", 400)
        
        updated_employee = employee_service.add_skills(employee_id, skills)
        
        if not updated_employee:
            return error_response("Employee not found", 404)
            
        return success_response(
            data=updated_employee,
            message=f"Added {len(skills)} skills to employee"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@employee_bp.route('/<int:employee_id>/skills/<skill>', methods=['DELETE'])
def remove_skill_from_employee(employee_id, skill):
    """Remove a skill from an employee"""
    try:
        updated_employee = employee_service.remove_skill(employee_id, skill)
        
        if not updated_employee:
            return error_response("Employee not found or skill not found", 404)
            
        return success_response(
            data=updated_employee,
            message=f"Removed skill '{skill}' from employee"
        )
        
    except Exception as e:
        return error_response(str(e), 500)
