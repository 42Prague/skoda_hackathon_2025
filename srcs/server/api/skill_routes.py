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

@skill_bp.route('/suggestions/<int:employee_id>', methods=['GET'])
def get_skill_suggestions(employee_id):
    """Get personalized skill suggestions for an employee"""
    try:
        suggestions = skill_service.get_skill_suggestions(employee_id)
        
        if not suggestions:
            return error_response("Employee not found", 404)
            
        return success_response(
            data=suggestions,
            message="Skill suggestions generated successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/analyze/gap', methods=['POST'])
def analyze_skills_gap():
    """Analyze skills gap for department or entire organization"""
    try:
        data = request.get_json() or {}
        department = data.get('department')
        position = data.get('position')
        
        analysis = skill_service.analyze_skills_gap(
            department=department,
            position=position
        )
        
        return success_response(
            data=analysis,
            message="Skills gap analysis completed"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/trends', methods=['GET'])
def get_skill_trends():
    """Get trending skills across the organization"""
    try:
        # Get query parameters
        department = request.args.get('department')
        limit = request.args.get('limit', 10, type=int)
        
        trends = skill_service.get_skill_trends(
            department=department,
            limit=limit
        )
        
        return success_response(
            data=trends,
            message="Skill trends retrieved successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/compatibility', methods=['POST'])
def check_team_compatibility():
    """Check skill compatibility between team members"""
    try:
        data = request.get_json()
        employee_ids = data.get('employee_ids', [])
        
        if len(employee_ids) < 2:
            return error_response("At least 2 employees required for compatibility check", 400)
        
        compatibility = skill_service.check_team_compatibility(employee_ids)
        
        return success_response(
            data=compatibility,
            message="Team compatibility analysis completed"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/learning-path/<int:employee_id>', methods=['GET'])
def get_learning_path(employee_id):
    """Get personalized learning path for an employee"""
    try:
        # Get query parameters
        target_position = request.args.get('target_position')
        experience_level = request.args.get('experience_level')
        
        learning_path = skill_service.generate_learning_path(
            employee_id=employee_id,
            target_position=target_position,
            experience_level=experience_level
        )
        
        if not learning_path:
            return error_response("Employee not found", 404)
            
        return success_response(
            data=learning_path,
            message="Learning path generated successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/benchmarks', methods=['GET'])
def get_skill_benchmarks():
    """Get skill benchmarks by position and experience level"""
    try:
        position = request.args.get('position')
        department = request.args.get('department')
        
        benchmarks = skill_service.get_skill_benchmarks(
            position=position,
            department=department
        )
        
        return success_response(
            data=benchmarks,
            message="Skill benchmarks retrieved successfully"
        )
        
    except Exception as e:
        return error_response(str(e), 500)

@skill_bp.route('/recommendations/team', methods=['POST'])
def get_team_recommendations():
    """Get recommendations for building a balanced team"""
    try:
        data = request.get_json()
        required_skills = data.get('required_skills', [])
        team_size = data.get('team_size', 5)
        department = data.get('department')
        
        recommendations = skill_service.get_team_building_recommendations(
            required_skills=required_skills,
            team_size=team_size,
            department=department
        )
        
        return success_response(
            data=recommendations,
            message="Team building recommendations generated"
        )
        
    except Exception as e:
        return error_response(str(e), 500)
