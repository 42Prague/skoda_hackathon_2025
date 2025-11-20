
from flask import Blueprint, request, jsonify
from utils.response_helpers import success_response, error_response
from services.position_service import PositionService

position_bp = Blueprint('positions', __name__)

# Initialize service
position_service = PositionService()

@position_bp.route('', methods=['GET'])
def get_all_positions():
    """Get all positions with optional filtering"""
    try:
        # Get query parameters for filtering
        department = request.args.get('department')
        min_experience = request.args.get('min_experience', type=int)
        
        # Get filtered positions
        positions = position_service.get_positions(
            department=department,
            min_experience=min_experience
        )
        
        return success_response(
            data=positions,
            message=f"Found {len(positions)} positions"
        )
        
    except Exception as e:
        return error_response(str(e), 500)