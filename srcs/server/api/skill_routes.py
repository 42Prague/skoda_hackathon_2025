"""
Skill Analysis API Routes
Handles all skill-related endpoints and analysis
"""

from flask import Blueprint, request, jsonify
from services.skill_service import SkillService
from utils.response_helpers import success_response, error_response
from data.data_accesser import g_data_accesser

skill_bp = Blueprint('skills', __name__)

# Initialize service
skill_service = SkillService()

@skill_bp.route('/diagram/<int:employee_id>', methods=['GET'])
def get_employee_diagram(employee_id):
    """Get personalized skill diagram for an employee"""
    try:
        diagram = skill_service.get_employee_diagram(employee_id)

        if not diagram:
            return error_response("Employee not found", 404)
            
        return success_response(
            data=diagram,
        )
        
    except Exception as e:
        print("Error in get_employee_diagram:", e)
        return error_response(str(e), 500)

@skill_bp.route('/diagram/export', methods=['GET'])
def export_all_employee_diagrams():
    """Generate CSV with diagram metrics for all employees."""
    try:
        # Expect skill_service to provide access to employees
        employees = g_data_accesser.get_all_employees()
        if not employees:
            return error_response("No employees available", 404)
        import csv, io
        output = io.StringIO()
        fieldnames = [
            'employee_id', 'breadth', 'depth', 'learning_intensity', 'qualification_strength',
            'job_requirement_coverage', 'skill_gap_index', 'recent_learning_index'
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for emp in employees:
            emp_id = emp.personal_number
            diagram = skill_service.get_employee_diagram(emp_id) or {}
            row = {
                'employee_id': emp_id,
                'breadth': diagram.get('breadth'),
                'depth': diagram.get('depth'),
                'learning_intensity': diagram.get('learning_intensity'),
                'qualification_strength': diagram.get('qualification_strength'),
                'job_requirement_coverage': diagram.get('job_requirement_coverage'),
                'skill_gap_index': diagram.get('skill_gap_index'),
                'recent_learning_index': diagram.get('recent_learning_index'),
            }
            writer.writerow(row)
        csv_data = output.getvalue()
        with open('employee_diagrams.csv', 'w', encoding='utf-8', newline='') as f:
            f.write(csv_data)

        return success_response(data={'csv': csv_data})
    except Exception as e:
        print("Error in export_all_employee_diagrams:", e)
        return error_response(str(e), 500)

