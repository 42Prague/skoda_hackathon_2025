#!/usr/bin/env python3
import logging
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import DB_PATH, EMPLOYEES_CSV, JOBS_CSV
from job_matching_db import JobEmployeeMatcher
from training_path_builder import TrainingPathBuilder

DB_PATH_STR = str(DB_PATH)

app = FastAPI(title="Talent Matching API")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=False,
	allow_methods=["*"],
	allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("talent-matching")


class EmployeeUpdate(BaseModel):
	emp_id: str
	emp_position: Optional[str] = ""
	emp_skills: Optional[str] = ""
	emp_education_level: Optional[str] = ""
	emp_years_experience: Optional[float] = 0
	emp_desired_job: Optional[str] = ""
	emp_open_to_change: Optional[float] = 0
	learning_hours_per_week: Optional[float] = 0
	looking_for_opportunities: Optional[bool] = False
	looking_reason: Optional[str] = ""


class JobUpdate(BaseModel):
	job_id: str
	job_title: Optional[str] = ""
	job_required_skills: Optional[str] = ""
	job_required_education: Optional[str] = ""
	job_required_experience: Optional[float] = 0
	job_description: Optional[str] = ""


def _query_rows(sql: str, params: tuple = ()):
	conn = sqlite3.connect(DB_PATH_STR, check_same_thread=False)
	conn.row_factory = sqlite3.Row
	try:
		cur = conn.cursor()
		cur.execute(sql, params)
		rows = cur.fetchall()
		return [dict(row) for row in rows]
	finally:
		conn.close()


def run_training_pipeline() -> int:
	builder = TrainingPathBuilder(DB_PATH_STR)
	try:
		return builder.build_training_plans()
	finally:
		builder.close()


def run_job_matching_pipeline(reseed: bool = False) -> int:
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		if reseed or matcher.count_employees() == 0 or matcher.count_jobs() == 0:
			matcher.init_from_csv(str(EMPLOYEES_CSV), str(JOBS_CSV))
		else:
			matcher.recompute_all_matches()
		cur = matcher.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM matches")
		return int(cur.fetchone()[0])
	finally:
		matcher.close()


def bootstrap_database() -> None:
	matches = run_job_matching_pipeline()
	logger.info("Job matching ready with %s rows", matches)
	training_rows = run_training_pipeline()
	logger.info("Training plans ready with %s rows", training_rows)


@app.on_event("startup")
async def on_startup():
	bootstrap_database()


@app.get("/api/health")
def health_check():
	return {"status": "ok"}


@app.post("/api/update/employee")
def update_employee(data: EmployeeUpdate):
	if data.looking_for_opportunities and not data.looking_reason:
		raise HTTPException(status_code=400, detail="looking_reason is required when looking_for_opportunities is true")
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		matcher.upsert_employee_from_dict(data.dict())
	finally:
		matcher.close()

	training_rows = run_training_pipeline()
	return {"status": "ok", "employee": data.emp_id, "training_rows": training_rows}


@app.post("/api/update/job")
def update_job(data: JobUpdate):
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		matcher.upsert_job_from_dict(data.dict())
	finally:
		matcher.close()

	training_rows = run_training_pipeline()
	return {"status": "ok", "job": data.job_id, "training_rows": training_rows}


@app.post("/api/run/job-matching")
def run_job_matching():
	matches = run_job_matching_pipeline()
	return {"status": "ok", "matches": matches}


@app.post("/api/run/training-plan")
def run_training_plan():
	training_rows = run_training_pipeline()
	return {"status": "ok", "training_rows": training_rows}


@app.get("/api/job-matches")
def get_job_matches(
	limit: int = Query(200, ge=1, le=1000),
	emp_id: Optional[str] = None,
	job_id: Optional[str] = None,
):
	filters = []
	params = []

	if emp_id:
		filters.append("m.emp_id = ?")
		params.append(emp_id)
	if job_id:
		filters.append("m.job_id = ?")
		params.append(job_id)

	where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

	rows = _query_rows(
		f"""
		SELECT m.job_id, j.job_title, m.emp_id, m.match_mark, m.match_score,
		       m.skill_overlap, m.education_match, m.experience_score,
		       m.position_similarity, m.intent_score, m.skill_match, m.skill_miss
		FROM matches m
		LEFT JOIN jobs j ON j.job_id = m.job_id
		{where_clause}
		ORDER BY m.match_score DESC
		LIMIT ?
		""",
		(*params, limit),
	)
	return {"status": "ok", "count": len(rows), "data": rows}


@app.get("/api/training-plans")
def get_training_plans(limit: int = Query(200, ge=1, le=1000)):
	rows = _query_rows(
		"""
		SELECT job_id, emp_id, skill_miss, intro_courses_list,
		       deep_courses_list, intro_hours_list, deep_hours_list,
		       intro_total_time_weeks, deep_total_time_weeks
		FROM training_plan
		ORDER BY job_id, emp_id
		LIMIT ?
		""",
		(limit,),
	)
	return {"status": "ok", "count": len(rows), "data": rows}


@app.get("/top_employees_for_job/{job_id}")
def top_employees(job_id: str, limit: int = 10):
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		return matcher.top_employees_for_job(job_id, top_n=limit)
	finally:
		matcher.close()


@app.get("/top_jobs_for_employee/{emp_id}")
def top_jobs(emp_id: str, limit: int = 10):
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		return matcher.top_jobs_for_employee(emp_id, top_n=limit)
	finally:
		matcher.close()


@app.get("/training_plan/{job_id}/{emp_id}")
def get_training_plan(job_id: str, emp_id: str):
	rows = _query_rows(
		"""
		SELECT *
		FROM training_plan
		WHERE job_id = ? AND emp_id = ?
		""",
		(job_id, emp_id),
	)
	if not rows:
		raise HTTPException(status_code=404, detail="Training plan not found")
	return rows[0]


@app.get("/employees")
def list_employees():
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		rows = matcher._fetch_all_employees()
		return [dict(r) for r in rows]
	finally:
		matcher.close()


@app.get("/jobs")
def list_jobs():
	matcher = JobEmployeeMatcher(DB_PATH_STR)
	try:
		rows = matcher._fetch_all_jobs()
		return [dict(r) for r in rows]
	finally:
		matcher.close()
