from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

from data_loader import get_data_loader
from llm_service import llm_service

# Load .env file from the same directory as this script
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

print(f"🔧 Loading .env from: {env_path}")
print(f"   LLM_API_BASE_URL: {os.getenv('LLM_API_BASE_URL', 'Not set')}")
print(f"   LLM_API_KEY: {'***' + os.getenv('LLM_API_KEY', '')[-10:] if os.getenv('LLM_API_KEY') else 'Not set'}")
print(f"   LLM_DEPLOYMENT_NAME: {os.getenv('LLM_DEPLOYMENT_NAME', 'Not set')}")

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting AI Skill Coach API...")
    try:
        get_data_loader()  # Initialize data loader
        print("Server running on http://localhost:8000")
    except Exception as e:
        print(f"❌ FATAL ERROR during startup: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to prevent server from starting
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="AI Skill Coach API", 
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AIPlanRequest(BaseModel):
    employee_profile: Dict[str, Any]
    gaps: Dict[str, Any]

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "AI Skill Coach API",
        "version": "1.0.0"
    }

# Get list of employees
@app.get("/api/employees")
async def get_employees():
    """Get list of all employees"""
    loader = get_data_loader()
    employees = loader.get_employees()
    return employees

# Get list of roles
@app.get("/api/roles")
async def get_roles():
    """Get list of all available roles"""
    loader = get_data_loader()
    roles = loader.get_roles()
    return roles

# Get employee profile
@app.get("/api/profile")
async def get_profile(personal_number: str):
    """Get comprehensive employee profile including skills and qualifications"""
    loader = get_data_loader()
    profile = loader.get_employee_profile(personal_number)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return profile

# Get skill and qualification gaps
@app.get("/api/gaps")
async def get_gaps(personal_number: str, role_id: str):
    """Compute gaps between employee profile and target role requirements"""
    loader = get_data_loader()
    gaps = loader.compute_gaps(personal_number, role_id)
    
    if not gaps:
        raise HTTPException(
            status_code=404, 
            detail="Employee or role not found"
        )
    
    return gaps

# Generate AI learning plan
@app.post("/api/ai-plan")
async def generate_ai_plan(request: AIPlanRequest):
    """Generate personalized learning plan using AI"""
    try:
        plan = await llm_service.generate_learning_plan(
            request.employee_profile,
            request.gaps
        )
        return plan
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating AI plan: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
