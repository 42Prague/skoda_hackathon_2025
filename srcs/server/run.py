"""
Main Application Entry Point
Simplified main file that uses the application factory pattern
"""

import os
from app_factory import create_app
from config.settings import config

def main():
    """Main application entry point"""
    
    # Get configuration from environment or use default
    config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Create the Flask application
    app = create_app(config[config_name])
    
    # Get host and port from config
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True)
    
    print("🚀 Starting Employee Skills Analyzer Server...")
    print(f"📍 Server URL: http://{host}:{port}")
    print(f"🔧 Environment: {config_name}")
    print(f"🐞 Debug mode: {debug}")
    print("\n📚 Available endpoints:")
    print("  • GET  /                     - API information")
    print("  • GET  /health               - Health check")
    print("  • GET  /api/v1/employees     - List employees")
    print("  • POST /api/v1/employees     - Create employee")
    print("  • GET  /api/v1/skills/suggestions/<id> - Skill suggestions")
    print("  • POST /api/v1/skills/analyze/gap - Skills gap analysis")
    print("\n💡 Try the test script: python test_api.py")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    # Run the application
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug  # Only reload in debug mode
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped gracefully")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == '__main__':
    main()
