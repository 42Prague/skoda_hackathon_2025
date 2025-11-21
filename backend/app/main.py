import logging
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import settings
from etl_pipeline import run_etl_pipeline
from skill_graph import SkillGraph, build_graph_from_parquet
from skill_engine import SkillEngine
from ai_coach_agent import get_coach

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Škoda AI Skill Coach API",
    description="Private, containerized AI skill development coach for Škoda employees",
    version="1.0.0"
)

# CORS middleware (adjust origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # USER: Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
skill_graph: Optional[SkillGraph] = None
skill_engine: Optional[SkillEngine] = None


# Pydantic models for request/response
class CoachQuestionRequest(BaseModel):
    """Request model for AI coach questions."""
    question: str
    context: Optional[str] = None


class CoachQuestionResponse(BaseModel):
    """Response model for AI coach answers."""
    answer: str


class SkillSearchRequest(BaseModel):
    """Request model for skill search."""
    query: str
    top_k: int = 5


class EmployeeProfileResponse(BaseModel):
    """Response model for employee profile."""
    personal_number: str
    skills: List[Dict]
    qualifications: List[Dict]
    missing_qualifications: List[Dict]


# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint for Azure Container Apps.

    Returns basic system status.
    """
    return {
        "status": "ok",
        "service": "skoda-ai-coach",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Škoda AI Skill Coach API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "etl": "/etl/run (POST)",
            "skills": "/skills/{personal_number} (GET)",
            "coach": "/coach/ask (POST)",
            "search": "/search/skills (POST)"
        }
    }


# ETL endpoints
@app.post("/etl/run")
async def run_etl(background_tasks: BackgroundTasks):
    def etl_task():
        try:
            logger.info("Starting ETL pipeline (background task)")
            run_etl_pipeline()
            logger.info("ETL pipeline completed")
        except Exception as e:
            logger.error(f"ETL pipeline failed: {e}")

    background_tasks.add_task(etl_task)

    return {
        "status": "started",
        "message": "ETL pipeline execution started in background"
    }


@app.post("/etl/build-graph")
async def build_graph(background_tasks: BackgroundTasks):
    def graph_task():
        global skill_graph
        try:
            logger.info("Building skill graph (background task)")
            skill_graph = build_graph_from_parquet()
            logger.info("Skill graph built successfully")
        except Exception as e:
            logger.error(f"Graph building failed: {e}")

    background_tasks.add_task(graph_task)

    return {
        "status": "started",
        "message": "Graph building started in background"
    }


# Graph query endpoints
@app.get("/skills/{personal_number}", response_model=EmployeeProfileResponse)
async def get_employee_profile(personal_number: str):
    global skill_graph

    # Load graph if not in memory
    if skill_graph is None:
        try:
            skill_graph = SkillGraph.load()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load skill graph: {e}"
            )

    # Get employee data
    try:
        skills = skill_graph.get_employee_skills(personal_number)
        qualifications = skill_graph.get_employee_qualifications(personal_number)
        missing = skill_graph.get_missing_qualifications(personal_number)

        return EmployeeProfileResponse(
            personal_number=personal_number,
            skills=skills,
            qualifications=qualifications,
            missing_qualifications=missing
        )

    except Exception as e:
        logger.error(f"Error fetching employee profile: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch employee profile: {e}"
        )


@app.get("/graph/stats")
async def get_graph_stats():
    """Get skill graph statistics."""
    global skill_graph

    if skill_graph is None:
        try:
            skill_graph = SkillGraph.load()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load skill graph: {e}"
            )

    try:
        stats = skill_graph.get_stats()
        return {"stats": stats}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get graph stats: {e}"
        )


# Skill search endpoint
@app.post("/search/skills")
async def search_skills(request: SkillSearchRequest):
    global skill_engine

    # Load engine if not in memory
    if skill_engine is None:
        try:
            skill_engine = SkillEngine.load_index()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load skill engine: {e}"
            )
    
    # If index doesn't exist, load data and build
    if skill_engine.embeddings is None:
        try:
            skill_engine.load_skills_data()
            skill_engine.build_skill_index()
            skill_engine.save_index()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to build skill index: {e}"
            )

    try:
        results = skill_engine.search_similar_skills(
            request.query,
            top_k=request.top_k
        )

        return {"results": results}

    except Exception as e:
        logger.error(f"Skill search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Skill search failed: {e}"
        )


# AI Coach endpoints
@app.post("/coach/ask", response_model=CoachQuestionResponse)
async def ask_coach(request: CoachQuestionRequest):
    try:
        coach = get_coach()
        answer = coach.answer_question(
            user_input=request.question,
            context=request.context
        )

        return CoachQuestionResponse(answer=answer)

    except Exception as e:
        logger.error(f"Coach query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Coach query failed: {e}"
        )


@app.post("/coach/learning-path")
async def generate_learning_path(
    personal_number: str,
    target_role: Optional[str] = None
):
    global skill_graph

    # Load graph if needed
    if skill_graph is None:
        try:
            skill_graph = SkillGraph.load()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load skill graph: {e}"
            )

    try:
        # Get employee data
        skills = skill_graph.get_employee_skills(personal_number)
        skill_names = [s.get('name', '') for s in skills if s.get('name')]

        missing = skill_graph.get_missing_qualifications(personal_number)
        missing_names = [m.get('name', '') for m in missing if m.get('name')]

        # Get target role from graph if not provided
        if not target_role:
            emp_node = f"emp:{personal_number}"
            if emp_node in skill_graph.graph:
                target_role = skill_graph.graph.nodes[emp_node].get('planned_position', 'Unknown')

        # Generate learning path
        coach = get_coach()
        learning_path = coach.generate_learning_path(
            current_skills=skill_names,
            target_role=target_role or "Unknown",
            missing_qualifications=missing_names
        )

        return {
            "personal_number": personal_number,
            "target_role": target_role,
            "current_skills": skill_names,
            "missing_qualifications": missing_names,
            "learning_path": learning_path
        }

    except Exception as e:
        logger.error(f"Learning path generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Learning path generation failed: {e}"
        )


# Startup event
@app.on_event("startup")
async def startup_event():
    global skill_graph, skill_engine

    logger.info("Starting Škoda AI Skill Coach API...")

    # Check if graph state exists; if not, run ETL and build graph
    if not settings.graph_state_path.exists():
        logger.info("Graph state not found. Initiating automatic ETL and Graph Build...")
        try:
            # Check if raw files exist before running
            if any(settings.raw_xlsx_dir.glob("*.xlsx")):
                logger.info("Raw Excel files found. Running ETL pipeline...")
                run_etl_pipeline()

                logger.info("Building skill graph...")
                skill_graph = build_graph_from_parquet()
                logger.info("Automatic setup complete.")
            else:
                logger.warning(f"No Excel files found in {settings.raw_xlsx_dir}. Skipping automatic ETL. Please place .xlsx files in the persistent_data/raw_xlsx folder.")
        except Exception as e:
            logger.error(f"Automatic setup failed: {e}")
    else:
        # Try to load graph (non-blocking)
        try:
            skill_graph = SkillGraph.load()
            logger.info("Skill graph loaded on startup")
        except Exception as e:
            logger.warning(f"Could not load skill graph on startup: {e}")

    # Try to load skill engine (non-blocking)
    try:
        skill_engine = SkillEngine.load_index()
        logger.info("Skill engine loaded on startup")
    except Exception as e:
        logger.warning(f"Could not load skill engine on startup: {e}")

    logger.info("API startup complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Škoda AI Skill Coach API...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower()
    )
