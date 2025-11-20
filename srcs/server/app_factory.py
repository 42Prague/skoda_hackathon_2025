"""
Application Factory
Creates and configures the Flask application
"""

from flask import Flask
from config.settings import Config
from api.routes import register_routes

def create_app(config_class=Config):
    """
    Application factory function
    Creates and configures Flask app with all components
    """
    
    # Create Flask instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Register all routes
    register_routes(app)
    
    # Add error handlers
    register_error_handlers(app)
    
    # Add middleware
    register_middleware(app)
    
    return app

def register_error_handlers(app):
    """Register custom error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            "success": False,
            "error": "Endpoint not found",
            "status_code": 404
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }, 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return {
            "success": False,
            "error": "Bad request",
            "status_code": 400
        }, 400

def register_middleware(app):
    """Register middleware functions"""
    
    @app.before_request
    def before_request():
        """Run before each request"""
        # Add logging, authentication, etc. here
        pass
    
    @app.after_request
    def after_request(response):
        """Run after each request"""
        # Add CORS headers, logging, etc.
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
