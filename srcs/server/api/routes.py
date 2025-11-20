"""
API Routes Registration
Separates route definitions from business logic
"""

from .employee_routes import employee_bp
from .skill_routes import skill_bp
from .health_routes import health_bp

def register_routes(app):
    """
    Register all route blueprints with the Flask app
    """
    
    # Register blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(employee_bp, url_prefix='/api/v1/employees')
    app.register_blueprint(skill_bp, url_prefix='/api/v1/skills')
    
    # Register root route
    @app.route('/')
    def root():
        return {
            "message": "Employee Skills Analyzer API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "employees": "/api/v1/employees",
                "skills": "/api/v1/skills"
            }
        }
