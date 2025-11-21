"""
Skill Analysis API Routes
Handles all skill-related endpoints and analysis
"""

from flask import Blueprint, request, jsonify
from services.skill_service import SkillService
from services.skill_clustering_service import skill_clustering_service
from services.skill_mapping_service import skill_mapping_service
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

        return success_response(data={'csv': csv_data})
    except Exception as e:
        print("Error in export_all_employee_diagrams:", e)
        return error_response(str(e), 500)

@skill_bp.route('/clustering/data', methods=['GET'])
def get_clustering_data():
    """Return employee skill clustering data (UMAP + KMeans + top TF-IDF skills).

    Query params:
      force_recompute=true  -> recompute pipeline even if cached / CSV exists
    """
    try:
        print("Received request for clustering data")
        force = request.args.get('force_recompute', 'false').lower() == 'true'
        data = skill_clustering_service.get_clustering_data(force_recompute=False)
        if not data:
            return success_response(data=[], message='No clustering data available (missing source files or empty result)')
        return success_response(data=data, message=f'Returned {len(data)} clustered employees')
    except Exception as e:
        print('Error in get_clustering_data:', e)
        return error_response(str(e), 500)

@skill_bp.route('/mapping/predict', methods=['POST'])
def generate_skill_mapping_predictions():
    """Generate the predicted skill mapping CSV using sentence embeddings.

    Body (JSON optional): {"force": true}
    """
    try:
        payload = request.get_json(silent=True) or {}
        force = bool(payload.get('force'))
        path = skill_mapping_service.ensure_predicted_mapping(force=False)
        status = skill_mapping_service.get_status()
        return success_response(data={"output_path": path, "status": status}, message="Skill mapping predictions generated")
    except ImportError as ie:
        return error_response(str(ie), 500)
    except Exception as e:
        print('Error in generate_skill_mapping_predictions:', e)
        return error_response(str(e), 500)

@skill_bp.route('/mapping/status', methods=['GET'])
def skill_mapping_status():
    try:
        return success_response(data=skill_mapping_service.get_status())
    except Exception as e:
        return error_response(str(e), 500)

