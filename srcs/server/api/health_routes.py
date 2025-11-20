"""
Health check routes
Simple endpoints for monitoring server status
"""

from flask import Blueprint, jsonify
from datetime import datetime
import psutil
import os

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@health_bp.route('/health/detailed')
def detailed_health_check():
    """Detailed health check with system information"""
    try:
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "process": {
                "pid": os.getpid(),
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
        })
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500
