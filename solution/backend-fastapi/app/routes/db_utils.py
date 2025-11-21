from fastapi import APIRouter, HTTPException
import pandas as pd
import json
from pydantic import BaseModel
from typing import List

from app.core.data_engine import get_db_engine

router = APIRouter(prefix="/api/stats", tags=["statistiques"])



@router.get("/courses/{employee_id}")
async def get_degreed_learning(employee_id: str):
	"""
	Fetch all courses taken by an employee from the `degreed_learning` table.
	Returns a list of records (may be empty).
	"""
	try:
		query = """
		SELECT
			content_id,
			content_title,
			content_provider,
			completed_date,
			content_type,
			estimated_learning_minutes,
			completion_rating
		FROM degreed_learning
		WHERE employee_id = %s AND completed_date IS NOT NULL
		ORDER BY completed_date DESC
		"""
 
		engine = get_db_engine()
		df = pd.read_sql_query(query, engine, params=(employee_id,))

		if df.empty:
			return []

		return df.to_dict('records')
	except Exception as e:
		print(f"Error fetching Degreed learning for employee {employee_id}: {e}")
		raise HTTPException(status_code=500, detail=f"Error fetching Degreed learning: {str(e)}")

@router.get("/employees/by-coordinator/{coordinator_group_id}")
async def get_employees_by_coordinator(coordinator_group_id: str):
    """
    Fetch all employees that belong to a given coordinator_group_id.
    Returns the specified schema fields and an aggregated `skills` array
    (each item: {skill_id, proficiency_level}).
    """
    try:
        query = """
        SELECT
            e.personal_number,
            e.user_name,
            e.profession,
            COALESCE(
              json_agg(
                json_build_object('skill_id', es.skill_id, 'proficiency_level', es.proficiency_level)
                ORDER BY es.skill_id
              ) FILTER (WHERE es.skill_id IS NOT NULL),
              '[]'
            ) AS skills
        FROM employees e
        LEFT JOIN employee_skill es ON e.personal_number = es.employee_id
        WHERE e.coordinator_group_id = %s
        GROUP BY
            e.personal_number,
            e.user_name,
            e.profession
        ORDER BY e.personal_number
        """

        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(coordinator_group_id,))

        if df.empty:
            return []

        # Ensure skills column is parsed as python list of dicts
        if "skills" in df.columns:
            df["skills"] = df["skills"].apply(lambda v: json.loads(v) if isinstance(v, str) else v)

        return df.to_dict("records")
    except Exception as e:
        print(f"Error fetching employees for coordinator_group_id {coordinator_group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching employees: {str(e)}")

class SkillIds(BaseModel):
    skill_ids: List[str]
    
@router.post("/skills/lookup")
async def get_skills_by_ids(payload: SkillIds):
    """
    Take a JSON body {"skill_ids": [1,2,3]} and return matching rows
    from `skill_list` with fields: skill_id, skill_name, description.
    """
    try:
        ids = payload.skill_ids
        if not ids:
            return []

        placeholders = ",".join(["%s"] * len(ids))
        query = f"""
        SELECT
            skill_id,
            skill_name,
            description
        FROM skill_list
        WHERE skill_id IN ({placeholders})
        ORDER BY skill_id
        """

        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=tuple(ids))

        if df.empty:
            return []

        return df.to_dict("records")
    except Exception as e:
        print(f"Error fetching skills for ids {payload.skill_ids}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching skills: {str(e)}")
    

@router.get("/skills-global")
async def get_skills_global():
    """
    Fetch global skill counts per quarter, joining skill_name and description
    from skill_list on skill_id.
    """
    try:
        query = """
        SELECT
            sl.skill_id,
            sl.skill_name,
            sl.description,
            COUNT(DISTINCT es.employee_id) AS number_of_employees,
            COALESCE(SUM(NULLIF(es.proficiency_level, '')::int), 0) AS quantity
        FROM employee_skill es
        JOIN skill_list sl ON es.skill_id = sl.skill_id
        GROUP BY sl.skill_id, sl.skill_name, sl.description
        ORDER BY sl.skill_id
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine)

        if df.empty:
            return []

        return df.to_dict("records")
    except Exception as e:
        print(f"Error fetching global skills: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching global skills: {str(e)}")

@router.get("/employees/{employee_id}")
async def get_employee_skills(employee_id: str):
    """
    Fetch all skills for a given employee_id, including proficiency and the
    skill_name (and description) from skill_list.
    Returns list of records with: skill_id, proficiency_level, skill_name, description.
    """
    try:
        query = """
        SELECT
            es.skill_id,
            es.proficiency_level,
            sl.skill_name,
            sl.description
        FROM employee_skill es
        LEFT JOIN skill_list sl ON es.skill_id = sl.skill_id
        WHERE es.employee_id = %s
        ORDER BY es.skill_id
        """

        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(employee_id,))

        if df.empty:
            return []

        return df.to_dict("records")
    except Exception as e:
        print(f"Error fetching skills for employee {employee_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching employee skills: {str(e)}")

@router.get("/skills/{coordinator_group_id}")
async def get_skills_by_coordinator(coordinator_group_id: str):
    """
    Aggregate skills for all employees where employees.coordinator_group_id = %s.
    Returns: skill_id, skill_name, description, number_of_employees, quantity (sum of proficiency).
    """
    try:
        query = """
        SELECT
            sl.skill_id,
            sl.skill_name,
            sl.description,
            COUNT(DISTINCT es.employee_id) AS number_of_employees,
            COALESCE(SUM(NULLIF(es.proficiency_level, '')::int), 0) AS quantity
        FROM employee_skill es
        JOIN employees e ON es.employee_id = e.personal_number
        JOIN skill_list sl ON es.skill_id = sl.skill_id
        WHERE e.coordinator_group_id = %s
        GROUP BY sl.skill_id, sl.skill_name, sl.description
        ORDER BY sl.skill_id
        """
        engine = get_db_engine()
        df = pd.read_sql_query(query, engine, params=(coordinator_group_id,))

        if df.empty:
            return []

        return df.to_dict("records")
    except Exception as e:
        print(f"Error fetching global skills for coordinator_group_id {coordinator_group_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching global skills: {str(e)}")