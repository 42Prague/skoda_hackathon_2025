"""
Flask REST API for Skill Gap AI
Provides endpoints for skill prediction and course recommendations
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_training import SkillMatchingAI
from skill_gap_system import get_system
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Load trained AI model on startup
print("🚀 Loading AI model...")
skill_ai = SkillMatchingAI()
try:
    skill_ai.load_model('models')
    print("✅ AI model loaded successfully!")
except Exception as e:
    print(f"⚠️  Warning: Could not load model - {e}")
    skill_ai = None

# Initialize skill gap analysis system
print("🚀 Loading skill gap analysis system...")
skill_system = None
try:
    skill_system = get_system()
    print("✅ Skill gap system ready!")
except Exception as e:
    print(f"⚠️  Warning: Skill gap system error - {e}")
    skill_system = None


@app.route('/')
def home():
    """API home page"""
    return jsonify({
        "name": "Skill Gap AI API",
        "version": "2.0",
        "status": "running",
        "model_loaded": skill_ai is not None,
        "skill_system_loaded": skill_system is not None,
        "endpoints": {
            "/predict": "POST - Predict skills for a course",
            "/predict/batch": "POST - Predict skills for multiple courses",
            "/health": "GET - Check API health",
            "/stats": "GET - Get model statistics",
            "/employee/analyze": "POST - Analyze individual employee skill gap",
            "/manager/dashboard": "GET - Manager team dashboard"
        }
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": skill_ai is not None
    })


@app.route('/predict', methods=['POST'])
def predict_skills():
    """
    Predict skills for a course
    
    Request body:
    {
        "course_title": "Python Programming for Data Science",
        "top_k": 3
    }
    
    Response:
    {
        "course_title": "Python Programming for Data Science",
        "predictions": [
            {"skill": "Programming", "confidence": 0.85},
            {"skill": "Data Analysis", "confidence": 0.72}
        ]
    }
    """
    if not skill_ai:
        return jsonify({"error": "AI model not loaded"}), 503
    
    try:
        data = request.get_json()
        
        if not data or 'course_title' not in data:
            return jsonify({"error": "Missing 'course_title' in request"}), 400
        
        course_title = data['course_title']
        top_k = data.get('top_k', 5)
        
        # Predict skills
        predictions = skill_ai.predict_skills_for_course(course_title, top_k=top_k)
        
        # Format response
        result = {
            "course_title": course_title,
            "predictions": [
                {
                    "skill": skill,
                    "confidence": float(confidence)
                }
                for skill, confidence in predictions
            ]
        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/predict/batch', methods=['POST'])
def predict_batch():
    """
    Predict skills for multiple courses at once
    
    Request body:
    {
        "courses": [
            "Python Programming",
            "Excel for Business",
            "Leadership Skills"
        ],
        "top_k": 3
    }
    """
    if not skill_ai:
        return jsonify({"error": "AI model not loaded"}), 503
    
    try:
        data = request.get_json()
        
        if not data or 'courses' not in data:
            return jsonify({"error": "Missing 'courses' array in request"}), 400
        
        courses = data['courses']
        top_k = data.get('top_k', 5)
        
        # Predict for each course
        results = []
        for course in courses:
            predictions = skill_ai.predict_skills_for_course(course, top_k=top_k)
            results.append({
                "course_title": course,
                "predictions": [
                    {"skill": skill, "confidence": float(conf)}
                    for skill, conf in predictions
                ]
            })
        
        return jsonify({"results": results})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/stats')
def get_stats():
    """Get model statistics"""
    if not skill_ai or not skill_ai.trained:
        return jsonify({
            "error": "Model not trained",
            "available_skills": []
        }), 503
    
    try:
        available_skills = skill_ai.skill_encoder.classes_.tolist()
        
        return jsonify({
            "model_trained": skill_ai.trained,
            "total_skills": len(available_skills),
            "available_skills": available_skills,
            "vectorizer_features": skill_ai.vectorizer.max_features
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/employee/analyze', methods=['POST'])
def analyze_employee():
    """
    Analyze individual employee skill gap
    
    Request body:
    {
        "employee_id": "EMP001",
        "target_position": "Senior Data Analyst"  // Optional
    }
    
    Response:
    {
        "employee": {...},
        "skill_gap_analysis": {
            "readiness_score": 75.5,
            "status": "IN_PROGRESS",
            "missing_required_skills": [...],
            "matched_skills": [...]
        },
        "recommended_learning_path": [
            {
                "course_id": "C001",
                "title": "Advanced Excel",
                "priority": "HIGH",
                "skills_taught": [...]
            }
        ],
        "development_plan": {...}
    }
    """
    if not skill_system:
        return jsonify({"error": "Skill gap system not initialized"}), 503
    
    try:
        data = request.get_json()
        
        if not data or 'employee_id' not in data:
            return jsonify({"error": "Missing 'employee_id' in request"}), 400
        
        employee_id = data['employee_id']
        target_position = data.get('target_position')
        
        # Analyze employee
        analysis = skill_system.analyze_employee(employee_id, target_position)
        
        if "error" in analysis:
            return jsonify(analysis), 404
        
        return jsonify(analysis)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/manager/dashboard', methods=['GET'])
def manager_dashboard():
    """
    Get manager dashboard with team analytics
    
    Query params:
        manager_id: Optional - filter by manager
    
    Response:
    {
        "team_overview": {
            "total_employees": 50,
            "average_readiness_score": 72.3,
            "ready_for_promotion": 12,
            "needs_development": 8
        },
        "top_skill_gaps": [...],
        "employee_details": [...],
        "training_recommendations": {...}
    }
    """
    if not skill_system:
        return jsonify({"error": "Skill gap system not initialized"}), 503
    
    try:
        manager_id = request.args.get('manager_id')
        
        # Get dashboard
        dashboard = skill_system.get_manager_dashboard(manager_id)
        
        return jsonify(dashboard)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*70)
    print("SKILL GAP AI - WEB API v2.0")
    print("="*70)
    print("\n🌐 Starting server...")
    print("📍 API will be available at: http://localhost:5000")
    print("\n📚 Available endpoints:")
    print("   GET  /                    - API info")
    print("   GET  /health              - Health check")
    print("   GET  /stats               - Model statistics")
    print("   POST /predict             - Predict skills for one course")
    print("   POST /predict/batch       - Predict skills for multiple courses")
    print("   POST /employee/analyze    - Analyze individual employee skill gap")
    print("   GET  /manager/dashboard   - Manager team dashboard")
    print("\n💡 Test employee analysis:")
    print('   curl -X POST http://localhost:5000/employee/analyze \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"employee_id": "EMP001"}\'')
    print("\n💡 Test manager dashboard:")
    print('   curl http://localhost:5000/manager/dashboard')
    print("\n" + "="*70 + "\n")
    
    # Run server
    app.run(host='0.0.0.0', port=5000, debug=True)
