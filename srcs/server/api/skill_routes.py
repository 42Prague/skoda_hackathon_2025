"""
Skill Analysis API Routes
Handles all skill-related endpoints and analysis
"""

from flask import Blueprint, request, jsonify
from services.skill_service import SkillService
from utils.response_helpers import success_response, error_response

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

