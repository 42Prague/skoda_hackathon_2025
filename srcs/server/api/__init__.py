"""
API package initialization
"""

from .routes import register_routes
from .employee_routes import employee_bp
from .skill_routes import skill_bp

__all__ = ['register_routes', 'employee_bp', 'skill_bp']
