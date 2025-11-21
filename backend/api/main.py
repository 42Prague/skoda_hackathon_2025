"""
FastAPI Backend for Skill DNA - Organizational Genome Analyzer
Serves ML/AI analysis results to React frontend
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import pandas as pd
import json
import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.clustering import analyze_skill_genome, SkillClusterAnalyzer
from ai.timeseries import analyze_skill_evolution, SkillEvolutionAnalyzer
from ai.embeddings import analyze_skill_semantics, SkillEmbeddingAnalyzer
from ai.advanced_insights import AdvancedInsightsEngine
from ai.mentorship_engine import MentorshipEngine, get_mentorship_recommendations
from data.synthetic_data import save_synthetic_data
from data.db_loader import load_all_from_db
from data.db_writer import persist_parsed_data_to_db
from data.anomaly_detection import IngestionAnomalyDetector, log_ingestion_event
from parsers.multi_format_parser import MultiFormatParser
from parsers.validator import DataTransformer
from i18n.translations import TranslationManager
from monitoring.health import get_health_monitor
from reporting.pdf_generator import generate_executive_pdf_report
from api.upload_automation import router as automation_router

# Initialize FastAPI app
app = FastAPI(
    title="Skill DNA API",
    description="Organizational Skill Genome Analysis - Škoda Auto Hackathon",
    version="1.0.0"
)

# Enable CORS (production + dev)
ALLOWED_ORIGINS_STR = os.getenv(
    "ALLOWED_ORIGINS",
    "https://skill-dna-organizational-genome.vercel.app,"
    "http://localhost:3000,http://localhost:3001,http://localhost:5173"
)
ALLOWED_ORIGINS = ALLOWED_ORIGINS_STR.split(',')

# Add regex pattern for all Vercel preview deployments
import re
VERCEL_PREVIEW_PATTERN = re.compile(r'^https://skill-dna-organizational-genome-[a-z0-9]+-elvi-zekajs-projects\.vercel\.app$')

# Custom CORS middleware to handle Vercel preview URLs
from fastapi.middleware.cors import CORSMiddleware as BaseCORSMiddleware
class CustomCORSMiddleware(BaseCORSMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            origin = None
            for header_name, header_value in scope.get("headers", []):
                if header_name == b"origin":
                    origin = header_value.decode("latin1")
                    break

            if origin and VERCEL_PREVIEW_PATTERN.match(origin):
                # Add Vercel preview URL to allowed origins dynamically
                if origin not in self.allow_origins:
                    self.allow_origins.append(origin)

        return await super().__call__(scope, receive, send)

app.add_middleware(
    CustomCORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include automation router for n8n integration
app.include_router(automation_router)

# Global analyzers (cached for performance)
_cluster_analyzer = None
_timeseries_analyzer = None
_embedding_analyzer = None
_advanced_insights = None

# Pydantic models for request/response
class AnalysisRequest(BaseModel):
    method: str = "hierarchical"  # "hierarchical" or "dbscan"
    n_clusters: Optional[int] = 4

class SkillGapRequest(BaseModel):
    required_skills: List[str]
    employee_skills: List[str]

class SkillInsightRequest(BaseModel):
    skills: List[str]
    context: str = "Škoda Auto automotive company"

# ClusterAnalysisRequest not used - endpoint accepts List[str] directly to match frontend


# Utility functions
def load_analyzers():
    """Initialize or reload all analyzers from PostgreSQL database"""
    global _cluster_analyzer, _timeseries_analyzer, _embedding_analyzer, _advanced_insights

    try:
        # Load data from PostgreSQL
        print("[DB] Loading data from PostgreSQL...")
        skill_matrix, evolution_df = load_all_from_db()

        # Fallback to synthetic data if DB is empty
        if len(skill_matrix) == 0:
            print("[WARN] Database empty, using synthetic data as fallback")
            if not os.path.exists("data/skill_matrix.csv"):
                save_synthetic_data()
            skill_matrix = pd.read_csv("data/skill_matrix.csv")
            evolution_df = pd.read_csv("data/skill_evolution.csv")

        # Initialize analyzers with loaded data
        _cluster_analyzer = SkillClusterAnalyzer(skill_matrix)
        _timeseries_analyzer = SkillEvolutionAnalyzer(evolution_df)
        _embedding_analyzer = SkillEmbeddingAnalyzer()
        _advanced_insights = AdvancedInsightsEngine(skill_matrix, evolution_df, _timeseries_analyzer)

        print(f"[OK] Analyzers loaded: {len(skill_matrix)} employees, {len(evolution_df)} evolution records")
        print(f"[OK] Advanced insights engine initialized")
        return True
    except Exception as e:
        print(f"❌ Error loading analyzers: {e}")
        import traceback
        traceback.print_exc()
        return False


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize data and analyzers on startup"""
    print("[LAUNCH] Starting Skill DNA API...")

    # Load analyzers from PostgreSQL (with synthetic fallback)
    success = load_analyzers()
    if success:
        print("[OK] API Ready!")
    else:
        print("[WARN] API started but analyzers failed to load")


@app.get("/")
async def root():
    """API health check with DB/Cache status"""
    db_ok = False
    redis_ok = False
    # Postgres check
    try:
        import psycopg2, os
        dsn = os.getenv("DATABASE_URL")
        if dsn:
            conn = psycopg2.connect(dsn, connect_timeout=2)
            cur = conn.cursor(); cur.execute("SELECT 1"); cur.fetchone()
            cur.close(); conn.close()
            db_ok = True
    except Exception as e:
        db_err = str(e)
    # Redis check
    try:
        import redis, os
        rurl = os.getenv("REDIS_URL")
        if rurl:
            r = redis.Redis.from_url(rurl); r.ping(); redis_ok = True
    except Exception as e:
        redis_err = str(e)
    return {
        "status": "operational" if (_cluster_analyzer and _timeseries_analyzer and _embedding_analyzer) else "degraded",
        "message": "Skill DNA API - Organizational Genome Analyzer",
        "version": "1.0.0",
        "analyzers_loaded": {
            "cluster": _cluster_analyzer is not None,
            "timeseries": _timeseries_analyzer is not None,
            "embeddings": _embedding_analyzer is not None
        },
        "infrastructure": {
            "postgres": db_ok,
            "redis": redis_ok
        },
        "endpoints": {
            "genome": "/api/genome",
            "evolution": "/api/evolution",
            "insights": "/api/insights",
            "cluster": "/api/cluster/{cluster_id}",
            "skill": "/api/skill/{skill_name}",
            "gap-analysis": "/api/gap-analysis",
            "network": "/api/network-analysis"
        }
    }


@app.get("/api/genome")
async def get_genome_data(method: str = "hierarchical"):
    """
    Get genome visualization data for D3.js force-directed graph
    Replaces MOCK_GENOME_DATA in frontend constants.ts
    """
    if not _cluster_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        data = _cluster_analyzer.generate_genome_visualization_data(method=method)
        response_data = {
            "success": True,
            "data": data
        }
        # Use json.dumps to bypass FastAPI's encoder and handle numpy types
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/evolution")
async def get_evolution_data():
    """
    Get skill evolution timeline data for Recharts
    Replaces EVOLUTION_DATA in frontend constants.ts
    """
    if not _timeseries_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        chart_data = _timeseries_analyzer.generate_evolution_chart_data()
        strategic_insights = _timeseries_analyzer.generate_strategic_insights()

        response_data = {
            "success": True,
            "chart_data": chart_data,
            "insights": strategic_insights
        }
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/insights")
async def get_strategic_insights():
    """
    Get comprehensive strategic insights combining all analyses
    Now includes: mutation risk, ROI metrics, workforce readiness, forecast accuracy
    """
    if not _timeseries_analyzer or not _advanced_insights:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # Legacy insights
        insights = _timeseries_analyzer.generate_strategic_insights()
        category_trends = _timeseries_analyzer.analyze_category_trends()

        # NEW: Advanced differentiated insights
        advanced_insights = _advanced_insights.generate_comprehensive_insights()

        response_data = {
            "success": True,
            "strategic_insights": insights,  # Legacy for backward compatibility
            "category_trends": category_trends,  # Legacy for backward compatibility
            "advanced_insights": advanced_insights,  # NEW differentiated intelligence
            "executive_summary": advanced_insights.get('executive_summary', {}),
            "workforce_readiness": advanced_insights.get('workforce_readiness', {}),
            "mutation_risk_analysis": advanced_insights.get('mutation_risk_analysis', []),
            "roi_analysis": advanced_insights.get('roi_analysis', []),
            "forecast_accuracy": advanced_insights.get('forecast_accuracy', []),
            "mentorship_recommendations": advanced_insights.get('mentorship_recommendations', []),
            "talent_redundancy_alerts": advanced_insights.get('talent_redundancy_alerts', []),
            "taxonomy_evolution": advanced_insights.get('taxonomy_evolution', {}),
            "critical_actions": advanced_insights.get('critical_actions', [])
        }
        return JSONResponse(content=json.loads(json.dumps(response_data, default=str)))
    except Exception as e:
        print(f"[ERROR] Insights endpoint failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/analyze-cluster")
async def analyze_skill_cluster(skills: List[str] = Body(...)):
    """
    Analyze a cluster of skills (for Manager AI and node click analysis)
    Frontend sends array of skill names directly (NOT wrapped in object)
    """
    if not _timeseries_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # Calculate metrics for skills in cluster
        growth_rates = []
        mutation_risks = []

        for skill in skills:
            try:
                growth_info = _timeseries_analyzer.calculate_growth_rate(skill, window=3)
                growth_rates.append(growth_info.get('growth_rate', 0))

                risk_score = _timeseries_analyzer.calculate_mutation_risk_score(skill)
                mutation_risks.append(risk_score)
            except:
                continue  # Skip skills not in dataset

        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        avg_risk = sum(mutation_risks) / len(mutation_risks) if mutation_risks else 0

        # Determine evolutionary stage
        if avg_growth > 15:
            stage = "Rapid Growth (Emerging Technologies)"
        elif avg_growth > 5:
            stage = "Steady Growth (Mainstream Adoption)"
        elif avg_growth > -5:
            stage = "Stable (Mature Technologies)"
        else:
            stage = "Declining (Legacy Systems)"

        # Generate recommendation
        if avg_growth > 10:
            recommendation = "HIGH PRIORITY: Invest heavily in training and recruitment. These skills are critical for future competitiveness."
        elif avg_growth > 0:
            recommendation = "MAINTAIN: Continue current training programs. Monitor market trends for acceleration."
        elif avg_risk > 0.6:
            recommendation = "PHASE OUT: High risk of obsolescence. Begin transition planning to emerging alternatives."
        else:
            recommendation = "STABLE: Maintain current expertise levels. Focus resources on high-growth areas."

        return {
            "success": True,
            "data": {
                "analysis": {
                    "skills_analyzed": len(skills),
                    "evolutionary_stage": stage,
                    "avg_growth_rate": round(avg_growth, 2),
                    "avg_mutation_risk": round(avg_risk, 3),
                    "recommendation": recommendation
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/cluster/{cluster_id}")
async def get_cluster_details(cluster_id: int):
    """
    Get detailed analysis of a specific skill cluster
    """
    if not _cluster_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # Run clustering
        labels = _cluster_analyzer.hierarchical_clustering(n_clusters=4)

        # Get characteristics
        cluster_chars = _cluster_analyzer.get_cluster_characteristics(labels)

        if cluster_id not in cluster_chars:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        return {
            "success": True,
            "cluster_id": cluster_id,
            "details": cluster_chars[cluster_id]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/skill/{skill_name}")
async def get_skill_analysis(skill_name: str):
    """
    Get comprehensive analysis of a specific skill
    Includes: growth rate, forecast, similar skills, mutation risk
    """
    if not _timeseries_analyzer or not _embedding_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # Growth analysis
        growth_info = _timeseries_analyzer.calculate_growth_rate(skill_name, window=3)

        # Forecast
        forecast = _timeseries_analyzer.forecast_skill(skill_name, forecast_years=2)

        # Mutation risk
        risk_score = _timeseries_analyzer.calculate_mutation_risk_score(skill_name)

        # Forecast accuracy (MAPE/RMSE) - backtesting on historical data
        forecast_accuracy = _timeseries_analyzer.calculate_forecast_accuracy(skill_name, test_years=2)

        # Similar skills (semantic)
        all_skills = _timeseries_analyzer.skills
        similar_skills = _embedding_analyzer.find_similar_skills(skill_name, all_skills, top_k=5)

        # AI insight
        insight = _embedding_analyzer.generate_skill_insights(skill_name)

        return {
            "success": True,
            "skill": skill_name,
            "growth_analysis": growth_info,
            "forecast": forecast,
            "forecast_accuracy": forecast_accuracy,
            "mutation_risk": risk_score,
            "similar_skills": similar_skills,
            "ai_insight": insight
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/forecast-accuracy/{skill_name}")
async def get_forecast_accuracy(skill_name: str, test_years: int = 2):
    """
    Get forecast accuracy metrics (MAPE, RMSE) for a specific skill
    Uses backtesting: trains on historical data, predicts recent years, compares to actuals

    Query Parameters:
    - test_years: Number of recent years to use for accuracy testing (default: 2)

    Returns:
    {
        "mape": float (Mean Absolute Percentage Error, 0-100),
        "rmse": float (Root Mean Squared Error),
        "accuracy_grade": "Excellent" | "Good" | "Acceptable" | "Poor" | "Very Poor",
        "comparison": [{year, actual, predicted, error, error_percent}]
    }
    """
    if not _timeseries_analyzer:
        raise HTTPException(status_code=503, detail="Timeseries analyzer not initialized")

    try:
        accuracy = _timeseries_analyzer.calculate_forecast_accuracy(skill_name, test_years=test_years)
        return {
            "success": True,
            "skill": skill_name,
            **accuracy
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast accuracy calculation failed: {str(e)}")


@app.post("/api/gap-analysis")
async def analyze_skill_gap(request: SkillGapRequest):
    """
    Analyze skill gap between required and current employee skills
    Uses semantic similarity for intelligent matching
    """
    if not _embedding_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        gap_analysis = _embedding_analyzer.analyze_skill_gap(
            required_skills=request.required_skills,
            employee_skills=request.employee_skills
        )

        return {
            "success": True,
            "gap_analysis": gap_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/mentorship/recommend/{employee_id}")
async def recommend_mentors(
    employee_id: str,
    target_skill: Optional[str] = None,
    top_k: int = 5
):
    """
    Recommend mentors for an employee based on:
    - Graph centrality (skill influence/connectivity)
    - Skill similarity and overlap
    - Growth trajectories (emerging vs declining skills)

    Query Parameters:
    - target_skill: Optional specific skill the mentee wants to learn
    - top_k: Number of mentor recommendations to return (default: 5)

    Returns:
    {
        "mentorship_recommendations": [
            {
                "mentor_id": str,
                "mentor_name": str,
                "department": str,
                "position": str,
                "score": float (0-1),
                "centrality": float (0-1),
                "shared_skills": int,
                "skills_to_improve": int,
                "new_skills_offered": int,
                "top_skills_to_learn": [str],
                "improvement_opportunities": [{skill, mentor_level, mentee_level, gap}],
                "reasoning": str
            }
        ],
        "retraining_paths": [
            {
                "from_skill": str (declining skill),
                "to_skill": str (emerging skill),
                "urgency": "high" | "medium",
                "opportunity": float (growth rate),
                "reasoning": str
            }
        ]
    }
    """
    try:
        # Initialize mentorship engine with analyzers (if available)
        engine = MentorshipEngine(
            embedding_analyzer=_embedding_analyzer,
            timeseries_analyzer=_timeseries_analyzer
        )

        # Get mentor recommendations
        mentors = engine.recommend_mentors(
            mentee_id=employee_id,
            target_skill=target_skill,
            top_k=top_k
        )

        # Get retraining paths
        retraining = engine.recommend_retraining_paths(employee_id, top_k=3)

        return {
            "success": True,
            "mentee_id": employee_id,
            "target_skill": target_skill,
            "mentorship_recommendations": mentors,
            "retraining_paths": retraining
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mentorship recommendation failed: {str(e)}")


@app.get("/api/mentorship/centrality/{employee_id}")
async def get_employee_centrality(employee_id: str):
    """
    Calculate skill centrality score for an employee

    Centrality score (0-1) measures:
    - Skill diversity (breadth of knowledge)
    - Skill rarity (uncommon expertise)
    - Skill proficiency levels

    Higher centrality = more influential/knowledgeable employee (better mentor candidate)
    """
    try:
        engine = MentorshipEngine()
        centrality = engine.calculate_skill_centrality(employee_id)

        return {
            "success": True,
            "employee_id": employee_id,
            "centrality_score": centrality,
            "grade": (
                "Expert" if centrality > 0.7 else
                "Advanced" if centrality > 0.5 else
                "Intermediate" if centrality > 0.3 else
                "Beginner"
            )
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Centrality calculation failed: {str(e)}")


@app.post("/api/analyze-cluster")
async def analyze_cluster(skills: List[str]):
    """
    Analyze a custom skill cluster (for Manager AI chat)
    Similar to Gemini analyzeSkillCluster but using Python ML
    """
    if not _timeseries_analyzer:
        raise HTTPException(status_code=503, detail="Analyzer not initialized")

    try:
        # Calculate aggregate metrics for this cluster
        growth_rates = []
        mutation_risks = []

        for skill in skills:
            try:
                growth_info = _timeseries_analyzer.calculate_growth_rate(skill, window=3)
                growth_rates.append(growth_info['growth_rate'])

                risk = _timeseries_analyzer.calculate_mutation_risk_score(skill)
                mutation_risks.append(risk)
            except:
                continue  # Skip skills not in dataset

        avg_growth = sum(growth_rates) / len(growth_rates) if growth_rates else 0
        avg_risk = sum(mutation_risks) / len(mutation_risks) if mutation_risks else 0

        # Classify evolutionary stage
        if avg_growth > 10:
            stage = "Explosive Emerging"
        elif avg_growth > 3:
            stage = "Rapidly Growing"
        elif avg_growth > -3:
            stage = "Stable Dominant"
        else:
            stage = "Declining/Legacy"

        # Generate recommendation
        if avg_risk > 0.7:
            recommendation = "URGENT: High obsolescence risk. Immediate reskilling program required."
        elif avg_growth > 10:
            recommendation = "Strategic priority: Scale training capacity to meet explosive demand."
        elif avg_risk < 0.3 and avg_growth > 0:
            recommendation = "Healthy cluster. Maintain current training investment levels."
        else:
            recommendation = "Monitor closely. Consider gradual transition to emerging technologies."

        return {
            "success": True,
            "analysis": {
                "skills_analyzed": len(skills),
                "evolutionary_stage": stage,
                "avg_growth_rate": round(avg_growth, 2),
                "avg_mutation_risk": round(avg_risk, 2),
                "recommendation": recommendation
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/regenerate-data")
async def regenerate_synthetic_data():
    """
    Regenerate synthetic data (for testing/demo purposes)
    """
    try:
        save_synthetic_data()
        load_analyzers()

        return {
            "success": True,
            "message": "Synthetic data regenerated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data generation failed: {str(e)}")


@app.get("/api/network-analysis")
async def get_network_analysis():
    """
    Get skill network analysis (hub skills, bridges, communities)
    Returns graceful empty payload with warning instead of 500 on failure.
    """
    if not _cluster_analyzer:
        return {"success": False, "network_insights": {}, "warning": "Analyzer not initialized"}

    try:
        labels = _cluster_analyzer.hierarchical_clustering(n_clusters=4)
        if labels is None or len(labels) == 0:
            return {"success": False, "network_insights": {}, "warning": "Insufficient data for clustering"}
        G = _cluster_analyzer.build_skill_network(labels, threshold=0.3)
        network_insights = _cluster_analyzer.get_network_insights(G)
        return {"success": True, "network_insights": network_insights}
    except Exception as e:
        # Log and return non-fatal result
        print(f"[WARN] Network analysis failed: {e}")
        return {"success": False, "network_insights": {}, "warning": f"Network analysis failed: {str(e)}"}


@app.post("/api/upload-data")
async def upload_data(file: UploadFile = File(...), language: str = "en"):
    """
    Upload CSV/Excel/PDF file with employee skill data
    Supports 6 different formats (Czech and English)
    Auto-detects format, persists to PostgreSQL, and reloads analyzers
    """
    try:
        # Save uploaded file to temporary location
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1])
        temp_path = temp_file.name
        temp_file.close()  # Close handle for Windows so pandas/openpyxl can read it

        with open(temp_path, 'wb') as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Parse file with multi-format parser
        parser = MultiFormatParser()
        parsed_data = parser.parse(temp_path)

        # Clean up temp file
        os.unlink(temp_path)

        # Check parsing success
        if not parsed_data.get('success', False):
            # Log failed ingestion
            try:
                log_ingestion_event(
                    filename=file.filename,
                    format_detected=parsed_data.get('format', 'unknown'),
                    rows_processed=0,
                    status='failed',
                    error_message=parsed_data.get('error', 'Unknown parsing error')
                )
            except:
                pass  # Don't fail upload if logging fails

            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": parsed_data.get('error', 'Unknown parsing error'),
                    "columns_found": parsed_data.get('columns_found', []),
                    "suggestion": parsed_data.get('suggestion', '')
                }
            )

        # Run anomaly detection on parsed data
        anomaly_report = None
        try:
            detector = IngestionAnomalyDetector()
            df = pd.DataFrame(parsed_data.get('data', []))

            # Run full validation
            anomaly_report = detector.run_full_validation(
                df=df,
                source=parsed_data.get('format', 'unknown'),
                date_columns=['hire_date', 'completion_date', 'start_date', 'event_date']
            )
        except Exception as anom_err:
            anomaly_report = {
                'overall_status': 'warning',
                'summary': f'Anomaly detection failed: {str(anom_err)}'
            }

        # Persist parsed data to PostgreSQL
        db_result = persist_parsed_data_to_db(parsed_data)

        if not db_result.get('success', False):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": f"Database persistence failed: {db_result.get('error')}",
                    "parsed_successfully": True,
                    "format_detected": parsed_data.get('format')
                }
            )

        # Persist to canonical_events table (normalized format)
        try:
            from data.canonical_persistence import persist_canonical_events_batch
            canonical_stats = persist_canonical_events_batch(
                parsed_data,
                parsed_data.get('format', 'unknown')
            )
            db_result['canonical_events_created'] = canonical_stats.get('canonical_events_created', 0)
            db_result['canonical_skipped_invalid'] = canonical_stats.get('skipped_invalid', 0)
        except Exception as canon_err:
            db_result['canonical_warning'] = f'Canonical persistence failed: {str(canon_err)}'

        # Reload analyzers with new data from database
        reload_success = load_analyzers()
        if not reload_success:
            db_result['warning'] = 'Data persisted to database but analyzer reload failed'

        # Log ingestion event with anomaly report
        try:
            ingestion_status = (
                'success' if anomaly_report.get('overall_status') == 'pass' else
                'warning' if anomaly_report.get('overall_status') == 'warning' else
                'failed'
            )

            log_ingestion_event(
                filename=file.filename,
                format_detected=parsed_data.get('format'),
                rows_processed=db_result.get('skill_events_inserted', 0),
                status=ingestion_status,
                anomaly_report=anomaly_report
            )
        except Exception as log_err:
            print(f"[WARN] Ingestion logging failed: {log_err}")

        # Return comprehensive summary
        result = {
            'success': True,
            'format_detected': parsed_data.get('format'),
            'encoding': parsed_data.get('encoding'),
            'employees_inserted': db_result.get('employees_inserted', 0),
            'skills_inserted': db_result.get('skills_inserted', 0),
            'skill_events_inserted': db_result.get('skill_events_inserted', 0),
            'canonical_events_created': db_result.get('canonical_events_created', 0),
            'canonical_skipped_invalid': db_result.get('canonical_skipped_invalid', 0),
            'analyzers_reloaded': reload_success,
            'anomaly_detection': anomaly_report,
            'message': 'File uploaded successfully and persisted to database'
        }

        # Add warnings if any
        warnings = []
        if 'canonical_warning' in db_result:
            warnings.append(db_result['canonical_warning'])
        if anomaly_report and anomaly_report.get('overall_status') in ['warning', 'fail']:
            warnings.append(f"Data quality: {anomaly_report.get('summary')}")
        if warnings:
            result['warnings'] = warnings

        return JSONResponse(content=json.loads(json.dumps(result, default=str)))

    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)

        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/supported-formats")
async def get_supported_formats(language: str = "en"):
    """
    Get documentation for all 5 supported CSV formats
    Helps users understand what format their data should be in
    """
    translator = TranslationManager(default_language=language)

    formats = {
        "format1_hr_system": {
            "name": translator.get_ui_label("format_hr_system", language),
            "description": "Czech HR system with start/end dates and variant fields",
            "required_columns": ["VP", "TO", "ID obj.", "ITyp", "STyp", "Zaèátek", "Konec"],
            "example": "VP,TO,ID obj.,ITyp,STyp,S,Zaèátek,Konec,VarPole"
        },
        "format2_planning": {
            "name": translator.get_ui_label("format_planning", language),
            "description": "Planning system with validity periods",
            "required_columns": ["Var.plánu", "Typ obj.", "ID objektu", "Subtyp", "Platí od", "Platí do"],
            "example": "Var.plánu,Typ obj.,ID objektu,Subtyp,Platí od,Platí do,Jazyk,Øetìzec"
        },
        "format3_lms": {
            "name": translator.get_ui_label("format_lms", language),
            "description": "Learning Management System (easiest format)",
            "required_columns": ["Employee ID", "Content Title", "Content Type", "Completed Date"],
            "example": "Completed Date,Employee ID,Content ID,Content Title,Content Type,Completion Points"
        },
        "format4_projects": {
            "name": translator.get_ui_label("format_projects", language),
            "description": "Project/task data with qualifications",
            "required_columns": ["ID P", "Počát.datum", "Koncové datum", "ID Q", "Název Q"],
            "example": "ID P,Počát.datum,Koncové datum,ID Q,Název Q"
        },
        "format5_qualifications": {
            "name": translator.get_ui_label("format_qualifications", language),
            "description": "Direct qualification/skill listing",
            "required_columns": ["ID kvalifikace", "Kvalifikace", "Číslo FM"],
            "example": "ID kvalifikace,Kvalifikace,Číslo FM"
        }
    }

    return {
        "success": True,
        "supported_formats": formats,
        "note": "System auto-detects format. At least 60% of required columns must be present."
    }


@app.post("/api/reskilling-roi-simulator")
async def simulate_reskilling_roi(from_skill: str = Body(...), to_skill: str = Body(...), num_employees: int = Body(10)):
    """
    Simulate ROI of reskilling employees from one skill to another
    Interactive tool for workforce planning and investment decisions
    """
    if not _advanced_insights:
        raise HTTPException(status_code=503, detail="Advanced insights engine not initialized")

    try:
        simulation_result = _advanced_insights.simulate_reskilling_roi(from_skill, to_skill, num_employees)

        return {
            "success": True,
            "simulation": simulation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI simulation failed: {str(e)}")


@app.get("/api/mentorship-recommendations")
async def get_mentorship_recommendations():
    """
    Get mentorship and transition recommendations
    Identifies high-risk skills and recommends transition paths with mentorship pairings
    """
    if not _advanced_insights:
        raise HTTPException(status_code=503, detail="Advanced insights engine not initialized")

    try:
        recommendations = _advanced_insights.generate_mentorship_recommendations()

        return {
            "success": True,
            "recommendations": recommendations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mentorship recommendations failed: {str(e)}")


@app.get("/api/talent-redundancy-alerts")
async def get_talent_redundancy_alerts():
    """
    Get talent redundancy risk alerts (single points of failure)
    Identifies skills where only 1-2 employees have critical expertise
    """
    if not _advanced_insights:
        raise HTTPException(status_code=503, detail="Advanced insights engine not initialized")

    try:
        alerts = _advanced_insights.detect_talent_redundancy_risks()

        return {
            "success": True,
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Redundancy alert detection failed: {str(e)}")


@app.get("/api/taxonomy-evolution")
async def get_taxonomy_evolution(year_start: Optional[int] = None, year_end: Optional[int] = None):
    """
    Analyze skill taxonomy evolution over time
    Shows new skills emerged, obsolete skills, and major growth/decline patterns
    """
    if not _advanced_insights:
        raise HTTPException(status_code=503, detail="Advanced insights engine not initialized")

    try:
        years_to_compare = None
        if year_start and year_end:
            years_to_compare = [year_start, year_end]

        taxonomy_analysis = _advanced_insights.analyze_taxonomy_evolution(years_to_compare)

        return {
            "success": True,
            "taxonomy_evolution": taxonomy_analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Taxonomy evolution analysis failed: {str(e)}")


@app.get("/api/translations/{language}")
async def get_translations(language: str):
    """
    Get all UI translations for specified language (en/cz)
    Frontend can load all labels at once for language switching
    """
    translator = TranslationManager(default_language=language)

    if language not in ["en", "cz"]:
        raise HTTPException(status_code=400, detail="Language must be 'en' or 'cz'")

    return {
        "success": True,
        "language": language,
        "labels": translator.get_all_labels(language)
    }


@app.get("/api/export-report")
async def export_executive_report():
    """
    Generate and download PDF executive report

    Produces a professional PDF report containing:
    - Executive summary with key metrics
    - Workforce readiness assessment
    - High-risk skills analysis
    - Talent redundancy alerts (single points of failure)
    - High-ROI training opportunities
    - Mentorship & transition programs
    - Critical actions & recommendations

    Returns:
        PDF file download (application/pdf)
    """
    try:
        if not _advanced_insights:
            raise HTTPException(status_code=503, detail="Advanced insights engine not initialized")

        # Generate comprehensive insights
        insights = _advanced_insights.generate_comprehensive_insights()

        # Type validation - ensure insights is a dict
        if not isinstance(insights, dict):
            raise TypeError(f"generate_comprehensive_insights returned {type(insights).__name__} instead of dict. Value: {insights}")

        # Generate PDF report
        pdf_buffer = generate_executive_pdf_report(insights)

        # Return PDF as downloadable file
        from datetime import datetime
        filename = f"skill-dna-executive-report-{datetime.now().strftime('%Y%m%d')}.pdf"

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except Exception as e:
        print(f"Error generating PDF report: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")


@app.get("/api/taxonomy/latest")
async def get_latest_taxonomy():
    """
    Get the most recent taxonomy version

    Returns:
        {
            'version_number': int,
            'taxonomy': Dict[category -> List[skills]],
            'cluster_stats': Dict,
            'created_at': str,
            'change_summary': str
        }
    """
    try:
        from data.taxonomy_versioning import get_latest_taxonomy as get_latest
        return JSONResponse(content=get_latest())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch latest taxonomy: {str(e)}")


@app.get("/api/taxonomy/diff/{version_id}")
async def get_taxonomy_diff(version_id: int):
    """
    Get diff between specified version and latest version

    Args:
        version_id: Version number to compare against latest

    Returns:
        {
            'version_from': int,
            'version_to': int,
            'added_categories': List[str],
            'removed_categories': List[str],
            'skills_added': Dict[category -> List[skills]],
            'skills_removed': Dict[category -> List[skills]],
            'skills_moved': List[{skill, from_category, to_category}],
            'summary': str
        }
    """
    try:
        from data.taxonomy_versioning import get_latest_taxonomy as get_latest, get_taxonomy_diff as calc_diff

        latest = get_latest()
        latest_version = latest['version_number']

        if version_id == latest_version:
            return JSONResponse(content={
                'version_from': version_id,
                'version_to': latest_version,
                'summary': 'Comparing to same version - no changes'
            })

        diff = calc_diff(version_id, latest_version)
        return JSONResponse(content=diff)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate taxonomy diff: {str(e)}")


@app.get("/api/taxonomy/versions")
async def list_taxonomy_versions(limit: int = 50):
    """
    List all taxonomy versions (most recent first)

    Returns:
        List of {version_number, created_at, change_summary, trigger_type, created_by}
    """
    try:
        from data.taxonomy_versioning import list_all_versions
        versions = list_all_versions(limit=limit)
        return JSONResponse(content={'versions': versions, 'total': len(versions)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list taxonomy versions: {str(e)}")


@app.get("/api/health")
async def get_system_health():
    """
    Comprehensive health & status dashboard
    Production monitoring endpoint for operational readiness

    Returns:
    - Overall system status and grade
    - Database health and performance
    - System resource usage (CPU, memory, disk)
    - Analyzer status and data quality
    - Upload pipeline health
    - Uptime metrics
    - Feature inventory
    """
    try:
        health_monitor = get_health_monitor()

        # Generate comprehensive report
        health_report = health_monitor.generate_comprehensive_health_report(
            cluster_analyzer=_cluster_analyzer,
            timeseries_analyzer=_timeseries_analyzer,
            embedding_analyzer=_embedding_analyzer,
            advanced_insights=_advanced_insights
        )

        return {
            "success": True,
            "health": health_report
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Health check failed: {str(e)}",
            "status": "unknown"
        }


# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
