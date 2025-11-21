"""
Analytics API endpoints for HR dashboard
Uses PostgreSQL database (same as Streamlit app)
Backend Data Engine for ŠKODA AI Skill Coach
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import os
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
from app.core.data_engine import (
    get_employee_skills as get_employee_skills_data,
    get_qualification_timeline as get_qualification_timeline_data,
    get_skills_expiring_soon as get_skills_expiring_soon_data,
    get_learning_recommendations as get_learning_recommendations_data,
    calculate_career_readiness_score as calculate_career_readiness_score_data,
    get_team_skills_heatmap,
    calculate_position_readiness,
    get_company_skill_trends,
    get_db_engine
)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

# PostgreSQL connection string (same as Streamlit app)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://skoda_user:skoda_password@postgres:5432/skoda_user"
)

# Note: get_db_engine is now imported from data_engine module


@router.get("/employees")
async def list_employees():
    """Get list of all employees with names and IDs"""
    try:
        query = """
        SELECT personal_number, name
        FROM employees
        ORDER BY name
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")


@router.get("/employee/{employee_id}")
async def get_employee(employee_id: str):
    """Get employee basic information"""
    try:
        query = """
        SELECT 
            personal_number,
            name,
            field_of_study,
            current_profession,
            planned_profession,
            planned_position,
            education_category,
            start_year
        FROM employees
        WHERE personal_number = %s
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        # Replace NaN with None for JSON serialization
        result = df.iloc[0].to_dict()
        result = {k: (None if (isinstance(v, float) and (pd.isna(v) or not pd.isfinite(v))) else v) for k, v in result.items()}
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee: {str(e)}")


# ============================================================================
# NEW ENDPOINTS: Clean JSON formats for MUI X Charts
# These must come BEFORE less specific routes like /skills
# ============================================================================

@router.get("/employee/{employee_id}/skill-profile")
async def get_employee_skill_profile(employee_id: str):
    """
    A. EMPLOYEE SKILL PROFILE JSON
    Returns clean JSON structure optimized for frontend visualizations.
    """
    try:
        # Verify employee exists
        engine = get_db_engine()
        emp_query = """
            SELECT personal_number, current_profession, planned_profession
            FROM employees
            WHERE personal_number = %s
        """
        emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
        if emp_df.empty:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        emp_row = emp_df.iloc[0]
        current_profession = emp_row['current_profession'] if pd.notna(emp_row['current_profession']) else None
        planned_profession = emp_row['planned_profession'] if pd.notna(emp_row['planned_profession']) else None
        
        # Get normalized skills
        skills = get_employee_skills_data(employee_id)
        
        # Format skills for response (remove theme/category from main response)
        formatted_skills = [
            {
                "name": s['name'],
                "expertiseLevel": s['expertiseLevel'],
                "validUntil": s['validUntil']
            }
            for s in skills
        ]
        
        # Get qualification timeline
        qualification_timeline = get_qualification_timeline_data(employee_id)
        formatted_timeline = [
            {
                "name": q['name'],
                "date": q['date']
            }
            for q in qualification_timeline
        ]
        
        # Get skills expiring soon
        expiring_skills = get_skills_expiring_soon_data(employee_id)
        formatted_expiring = [
            {
                "name": s['name'],
                "expertiseLevel": s['expertiseLevel'],
                "validUntil": s['validUntil']
            }
            for s in expiring_skills
        ]
        
        return {
            "employeeId": employee_id,
            "currentProfession": current_profession,
            "plannedProfession": planned_profession,
            "skills": formatted_skills,
            "qualificationTimeline": formatted_timeline,
            "skillsExpiringSoon": formatted_expiring
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching employee skill profile: {str(e)}")


@router.get("/employee/{employee_id}/learning-recommendations")
async def get_learning_recommendations_endpoint(employee_id: str):
    """
    B. LEARNING RECOMMENDATION JSON
    Returns AI-powered learning recommendations with skill gaps.
    """
    try:
        # Verify employee exists
        engine = get_db_engine()
        emp_query = "SELECT personal_number FROM employees WHERE personal_number = %s"
        emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
        if emp_df.empty:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Get recommendations and skill gaps
        recommendations, skill_gaps = get_learning_recommendations_data(employee_id)
        
        # Calculate career readiness score
        readiness_score = calculate_career_readiness_score_data(employee_id)
        
        return {
            "employeeId": employee_id,
            "careerReadinessScore": readiness_score,
            "aiRecommendations": recommendations,
            "skillGaps": skill_gaps
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching learning recommendations: {str(e)}")


@router.get("/employee/{employee_id}/skills")
async def get_employee_skills(employee_id: str):
    """Get employee skills"""
    try:
        query = """
        SELECT 
            skill_name,
            skill_theme,
            expertise_level,
            validity_end_date,
            skill_category
        FROM skill_mapping
        WHERE personal_number = %s
        ORDER BY expertise_level DESC, skill_name
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Convert dates to strings for JSON serialization
        if 'validity_end_date' in df.columns:
            df['validity_end_date'] = df['validity_end_date'].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")


@router.get("/employee/{employee_id}/skill-theme-breakdown")
async def get_skill_theme_breakdown(employee_id: str):
    """Get skill theme breakdown for pie chart"""
    try:
        query = """
        SELECT 
            skill_theme,
            COUNT(*) as skill_count,
            AVG(CASE 
                WHEN expertise_level = 'Expert' THEN 5
                WHEN expertise_level = 'Advanced' THEN 4
                WHEN expertise_level = 'Intermediate' THEN 3
                WHEN expertise_level = 'Basic' THEN 2
                ELSE 1
            END) as avg_level
        FROM skill_mapping
        WHERE personal_number = %s
        GROUP BY skill_theme
        ORDER BY skill_count DESC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching skill theme breakdown: {str(e)}")


@router.get("/employee/{employee_id}/expertise-distribution")
async def get_expertise_distribution(employee_id: str):
    """Get expertise level distribution for bar chart"""
    try:
        query = """
        SELECT 
            expertise_level,
            COUNT(*) as count
        FROM skill_mapping
        WHERE personal_number = %s
        GROUP BY expertise_level
        ORDER BY 
            CASE expertise_level
                WHEN 'Expert' THEN 1
                WHEN 'Advanced' THEN 2
                WHEN 'Intermediate' THEN 3
                WHEN 'Basic' THEN 4
                ELSE 5
            END
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching expertise distribution: {str(e)}")


@router.get("/employee/{employee_id}/qualifications")
async def get_qualifications(employee_id: str):
    """Get employee qualifications"""
    try:
        query = """
        SELECT 
            qualification_name,
            qualification_type,
            status,
            start_date,
            end_date,
            completion_date,
            duration_days,
            provider
        FROM doklad_kvalifikace_komplet
        WHERE personal_number = %s
        ORDER BY completion_date DESC NULLS LAST, start_date DESC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Convert dates to strings
        date_cols = ['start_date', 'end_date', 'completion_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching qualifications: {str(e)}")


@router.get("/employee/{employee_id}/qualification-status")
async def get_qualification_status(employee_id: str):
    """Get qualification status summary"""
    try:
        query = """
        SELECT 
            COUNT(*) FILTER (WHERE status = 'Completed') as completed,
            COUNT(*) FILTER (WHERE status = 'In Progress') as in_progress,
            COUNT(*) FILTER (WHERE status = 'Planned') as planned,
            COUNT(*) as total
        FROM doklad_kvalifikace_komplet
        WHERE personal_number = %s
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        if df.empty:
            return {"completed": 0, "in_progress": 0, "planned": 0, "total": 0}
        # Replace NaN with 0 for JSON serialization
        result = df.iloc[0].to_dict()
        result = {k: (0 if (isinstance(v, float) and (pd.isna(v) or not pd.isfinite(v))) else (int(v) if isinstance(v, (float, int)) and pd.notna(v) else v)) for k, v in result.items()}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching qualification status: {str(e)}")


@router.get("/employee/{employee_id}/learning-timeline")
async def get_learning_timeline(employee_id: str):
    """Get learning activity timeline"""
    try:
        query = """
        SELECT 
            DATE_TRUNC('month', completion_date) as month,
            COUNT(*) as content_count,
            SUM(estimated_time_minutes) as total_minutes,
            COUNT(DISTINCT provider) as provider_count
        FROM degreed_data
        WHERE personal_number = %s
          AND completion_date IS NOT NULL
        GROUP BY DATE_TRUNC('month', completion_date)
        ORDER BY month DESC
        LIMIT 12
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Convert month to string and handle NaT
        if 'month' in df.columns:
            df['month'] = df['month'].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching learning timeline: {str(e)}")


@router.get("/employee/{employee_id}/provider-breakdown")
async def get_provider_breakdown(employee_id: str):
    """Get learning provider breakdown"""
    try:
        query = """
        SELECT 
            provider,
            COUNT(*) as content_count,
            SUM(estimated_time_minutes) as total_minutes
        FROM degreed_data
        WHERE personal_number = %s
          AND provider IS NOT NULL
        GROUP BY provider
        ORDER BY content_count DESC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching provider breakdown: {str(e)}")


@router.get("/employee/{employee_id}/degreed-activity")
async def get_degreed_activity(employee_id: str):
    """Get Degreed learning activity"""
    try:
        query = """
        SELECT 
            d.content_title,
            d.completion_date,
            d.provider,
            d.content_type,
            d.estimated_time_minutes,
            c.category,
            c.difficulty_level
        FROM degreed_data d
        LEFT JOIN degreed_catalog c ON d.content_id = c.content_id
        WHERE d.personal_number = %s
        ORDER BY d.completion_date DESC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Convert dates to strings
        if 'completion_date' in df.columns:
            df['completion_date'] = df['completion_date'].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Degreed activity: {str(e)}")


@router.get("/employee/{employee_id}/test-history")
async def get_test_history(employee_id: str):
    """Get test history"""
    try:
        query = """
        SELECT 
            t.test_name,
            t.test_date,
            t.score,
            t.passed,
            t.duration_minutes,
            ts.test_group,
            tp.test_subject,
            tp.test_theme
        FROM testovani_pisemne_dovednosti t
        LEFT JOIN test_skupina ts ON t.test_id = ts.test_id
        LEFT JOIN test_predmetu tp ON t.test_id = tp.test_id
        WHERE t.personal_number = %s
        ORDER BY t.test_date DESC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        # Convert dates to strings
        if 'test_date' in df.columns:
            df['test_date'] = df['test_date'].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching test history: {str(e)}")


@router.get("/employee/{employee_id}/test-pass-rate")
async def get_test_pass_rate(employee_id: str):
    """Get test pass rate data for chart"""
    try:
        query = """
        SELECT 
            test_date,
            score,
            passed
        FROM testovani_pisemne_dovednosti
        WHERE personal_number = %s
        ORDER BY test_date ASC
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))
        
        if df.empty:
            return []
        
        # Calculate cumulative pass rate
        df['cumulative_passed'] = df['passed'].astype(int).cumsum()
        df['cumulative_total'] = range(1, len(df) + 1)
        df['cumulative_pass_rate'] = (df['cumulative_passed'] / df['cumulative_total']) * 100
        
        # Convert dates to strings
        df['test_date'] = df['test_date'].astype(str).replace('NaT', None)
        # Replace NaN with None for JSON serialization
        df = df.replace({pd.NA: None, pd.NaT: None})
        df = df.where(pd.notnull(df), None)
        # Handle infinite or NaN float values
        for col in df.columns:
            if df[col].dtype == 'float64':
                df[col] = df[col].replace([float('inf'), float('-inf')], None)
                df[col] = df[col].where(pd.notnull(df[col]), None)
        
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching test pass rate: {str(e)}")




@router.get("/team/{team_id}/heatmap")
async def get_team_heatmap(team_id: str, member_ids: List[str] = Query(..., description="List of employee IDs in the team")):
    """
    C. MANAGER TEAM HEATMAP JSON
    Returns heatmap data optimized for MUI <HeatmapChart /> component.
    Format: rows/columns matrix as required by MUI X Charts.
    """
    try:
        if not member_ids:
            raise HTTPException(status_code=400, detail="member_ids query parameter is required")
        
        # Get heatmap data
        skills, members, heatmap_matrix = get_team_skills_heatmap(member_ids)
        
        return {
            "teamId": team_id,
            "skills": skills,
            "members": members,
            "heatmapMatrix": heatmap_matrix
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching team heatmap: {str(e)}")


@router.get("/employee/{employee_id}/position-readiness")
async def get_position_readiness(employee_id: str, target_role: str = Query(..., description="Target role/position to check readiness for")):
    """
    D. POSITION READINESS JSON
    Returns readiness score and blocking skills for a target position.
    """
    try:
        # Verify employee exists
        engine = get_db_engine()
        emp_query = "SELECT personal_number FROM employees WHERE personal_number = %s"
        emp_df = pd.read_sql_query(emp_query, engine, params=(employee_id,))
        if emp_df.empty:
            raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")
        
        # Calculate readiness
        readiness_score, blocking_skills = calculate_position_readiness(employee_id, target_role)
        
        return {
            "employeeId": employee_id,
            "targetRole": target_role,
            "readinessScore": readiness_score,
            "blockingSkills": blocking_skills
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating position readiness: {str(e)}")


@router.get("/company/skill-trends")
async def get_company_skill_trends_endpoint():
    """
    E. COMPANY-WIDE SKILL TRENDS JSON
    Returns yearly skill counts, emerging skills, and obsolete skills.
    """
    try:
        trends = get_company_skill_trends()
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company skill trends: {str(e)}")

