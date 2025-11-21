"""FastAPI application for skills taxonomy API."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import settings
from src.database import neo4j_client
from src.models import (
    FindJobsRequest,
    FindSkillsRequest,
    ExtractSkillsRequest,
    SystemStats,
    SearchSkillsRequest,
    SearchJobsRequest,
)
from .query_service import query_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("Starting up Skills Taxonomy API...")
    await neo4j_client.connect()
    logger.info("✓ Connected to Neo4j database")

    yield

    # Shutdown
    logger.info("Shutting down Skills Taxonomy API...")
    await neo4j_client.close()
    logger.info("✓ Closed Neo4j connection")


# Create FastAPI app
app = FastAPI(
    title="Skills Taxonomy API",
    description="LLM-based skill extraction and job matching system with hierarchical taxonomy",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Skills Taxonomy API",
        "version": "0.1.0",
        "docs": "/docs",
        "neo4j_browser": "http://localhost:7474",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        await neo4j_client.execute_query("RETURN 1 as test")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database connection failed")


@app.post("/api/v1/find-jobs")
async def find_jobs(request: FindJobsRequest):
    """Find jobs matching the specified skills.

    This endpoint finds jobs that require the skills you provide.
    It supports:
    - Matching all skills or any skill
    - Including jobs that require parent skills in the hierarchy
    - Ranking results by match score and coverage

    Example:
    ```json
    {
      "skills": ["Python", "Machine Learning", "Docker"],
      "match_all": false,
      "include_parents": true,
      "limit": 20
    }
    ```
    """
    try:
        job_matches = await query_service.find_jobs_by_skills(
            skills=request.skills,
            match_all=request.match_all,
            include_parents=request.include_parents,
            limit=request.limit,
        )

        return {
            "jobs": [match.model_dump() for match in job_matches],
            "total": len(job_matches),
            "query": request.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error finding jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/find-skills")
async def find_skills(request: FindSkillsRequest):
    """Find skills required by jobs with matching title.

    This endpoint searches for jobs by title and returns the skills
    they require, ranked by frequency and confidence.

    Example:
    ```json
    {
      "job_title": "Machine Learning Engineer",
      "include_children": true
    }
    ```
    """
    try:
        skills = await query_service.find_skills_by_job(
            job_title=request.job_title,
            include_children=request.include_children,
        )

        return {
            "skills": [skill.model_dump() for skill in skills],
            "total": len(skills),
            "query": request.model_dump(),
        }

    except Exception as e:
        logger.error(f"Error finding skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/extract-skills")
async def extract_skills(request: ExtractSkillsRequest):
    """Extract and validate skills from text.

    This endpoint:
    1. Uses LLM to extract skills from provided text
    2. Validates extracted skills against the database
    3. Returns validated skills, semantic matches, and unmatched skills

    Useful for analyzing resumes, job descriptions, or any text
    containing skill mentions.

    Example:
    ```json
    {
      "text": "I have 5 years of experience with Python and Django, working on ML projects using TensorFlow."
    }
    ```
    """
    try:
        validation_response = await query_service.extract_validated_skills(
            text=request.text
        )

        return validation_response.model_dump()

    except Exception as e:
        logger.error(f"Error extracting skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search-skills")
async def search_skills(request: SearchSkillsRequest):
    """Search for skills by name or pattern.

    This endpoint searches for skills using multiple matching strategies:
    - Exact match: Matches canonical names exactly
    - Alias match: Matches against skill aliases
    - Semantic match: Uses embeddings for similarity-based matching

    You can enable/disable each matching strategy and control the
    minimum similarity threshold for semantic matches.

    Example:
    ```json
    {
      "query": "kuberntes",
      "top_k": 10,
      "min_similarity": 0.7,
      "include_exact": true,
      "include_aliases": true,
      "include_semantic": true
    }
    ```

    Response includes match_type ("exact", "alias", or "semantic") and
    similarity score for semantic matches.
    """
    try:
        response = await query_service.search_skills(
            query=request.query,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
            include_exact=request.include_exact,
            include_aliases=request.include_aliases,
            include_semantic=request.include_semantic,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error searching skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/search-jobs")
async def search_jobs(request: SearchJobsRequest):
    """Search for jobs by title or keywords.

    This endpoint uses full-text search to find jobs matching your query.
    You can search only in job titles (more precise) or also include
    job descriptions (broader results).

    Example:
    ```json
    {
      "query": "developer",
      "top_k": 10,
      "search_in_description": false
    }
    ```

    Results are ranked by relevance score from the full-text search.
    """
    try:
        response = await query_service.search_jobs(
            query=request.query,
            top_k=request.top_k,
            search_in_description=request.search_in_description,
        )

        return response.model_dump()

    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats", response_model=SystemStats)
async def get_stats():
    """Get system statistics.

    Returns statistics about the database:
    - Total number of jobs
    - Total number of skills
    - Total job-skill relationships
    - Average skills per job
    - Skill breakdown by category
    - Number of hierarchical relationships
    """
    try:
        stats = await neo4j_client.get_stats()

        return SystemStats(
            total_jobs=stats["total_jobs"],
            total_skills=stats["total_skills"],
            total_relationships=stats["total_relationships"],
            avg_skills_per_job=stats["avg_skills_per_job"],
            skill_categories=stats["skill_categories"],
            hierarchical_skills=stats["total_hierarchical"],
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/visualize/{job_id}")
async def visualize_job(job_id: str):
    """Get Neo4j Browser URL for visualizing a job and its skills.

    Returns a Cypher query and URL to visualize the job's skill graph
    in Neo4j Browser.
    """
    cypher_query = f"""
    MATCH (j:Job {{id: '{job_id}'}})-[r:REQUIRES]->(s:Skill)
    OPTIONAL MATCH (s)-[p:PARENT_OF*]->(child:Skill)
    RETURN j, r, s, p, child
    """

    neo4j_browser_url = "http://localhost:7474/browser/"

    return {
        "job_id": job_id,
        "neo4j_browser_url": neo4j_browser_url,
        "cypher_query": cypher_query,
        "instructions": (
            "1. Open Neo4j Browser at http://localhost:7474\n"
            "2. Login with username: neo4j, password: skillspassword\n"
            "3. Copy and paste the cypher_query into the query editor\n"
            "4. Click 'Run' to visualize the job's skill graph"
        ),
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
