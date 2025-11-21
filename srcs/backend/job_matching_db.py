#!/usr/bin/env python3
"""
Incremental Job-Employee Matching System (DB-backed)
----------------------------------------------------
- Uses SQLite for persistent storage.
- Stores employees, jobs, embeddings, and match scores.
- Supports incremental updates:
	* upsert_job_from_dict(...)      -> recompute matches for this job vs all employees
	* upsert_employee_from_dict(...) -> recompute matches for this employee vs all jobs

Intended usage with a frontend:
- Backend calls upsert_* when an employee or job is created/updated.
- Frontend queries the DB (e.g. via API) for top matches.
"""

import sqlite3
import json
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer, util

from config import (
	DB_PATH as CONFIG_DB_PATH,
	EMPLOYEES_CSV,
	JOBS_CSV,
	SENTENCE_TRANSFORMER_MODEL,
)

# -----------------------
# CONFIGURATION
# -----------------------
EMP_FILE = str(EMPLOYEES_CSV)
JOB_FILE = str(JOBS_CSV)
DB_PATH = str(CONFIG_DB_PATH)
TOP_N_DEFAULT = 10

WEIGHTS = {
	"skill_overlap": 0.4,
	"education_match": 0.2,
	"experience_score": 0.2,
	"position_similarity": 0.15,
	"intent_score": 0.05,
}

SKILL_DIFFICULTY = {
	# --- Core programming / backend fundamentals ---
	"python": 0.97,
	"java": 0.80,
	"c++": 0.85,
	"c": 0.87,
	"sql": 0.67,

	# --- Data & ML ecosystem ---
	"pandas": 0.53,
	"numpy": 0.53,
	"tensorflow": 0.80,
	"keras": 0.67,
	"spark": 0.67,

	# --- Cloud / DevOps ---
	"aws": 0.60,
	"docker": 0.53,
	"kubernetes": 0.53,
	"linux": 0.47,
	"microservices": 0.47,

	# --- Web / API frameworks ---
	"flask": 0.33,
	"node": 0.33,
	"react": 0.27,
	"typescript": 0.20,
	"graphql": 0.20,

	# --- Frontend & markup ---
	"javascript": 0.13,
	"html": 0.07,
	"css": 0.02,
}

EDU_LEVEL = {"High School": 0, "Bachelor": 1, "Master": 2, "PhD": 3}


# -----------------------
# HELPER FUNCTIONS
# -----------------------

def _parse_skills(skills_str):
	"""Parse semicolon-separated skills into a normalized set."""
	if not isinstance(skills_str, str) or not skills_str.strip():
		return set()
	return {s.strip().lower() for s in skills_str.split(";") if s.strip()}


def compute_skill_overlap(emp_skills, job_skills, difficulty_map=SKILL_DIFFICULTY):
	"""Weighted overlap of employee skills over required job skills."""
	e = _parse_skills(emp_skills)
	j = _parse_skills(job_skills)
	if not j:
		return 0.0
	common = e & j
	num = sum(difficulty_map.get(s, 0.5) for s in common)
	den = sum(difficulty_map.get(s, 0.5) for s in j)
	return num / den if den > 0 else 0.0


def get_skill_match_miss(emp_skills, job_skills, sep=";"):
	"""
	Return two CSV-friendly strings:
	  - match_str: required skills the employee has (e.g., "java;tensorflow")
	  - miss_str:  required skills the employee lacks (e.g., "aws;kubernetes")
	If a list would be empty, return "-" instead.
	"""
	e = _parse_skills(emp_skills)

	job_list = []
	if isinstance(job_skills, str) and job_skills.strip():
		normalized = job_skills.replace(",", sep)
		job_list = [s.strip().lower() for s in normalized.split(sep) if s.strip()]

	match = [s for s in job_list if s in e]
	miss = [s for s in job_list if s not in e]

	match_str = sep.join(match) if match else "-"
	miss_str = sep.join(miss) if miss else "-"
	return match_str, miss_str


def compute_education_match(emp_edu, job_edu):
	if emp_edu not in EDU_LEVEL or job_edu not in EDU_LEVEL:
		return 0.0
	return 1.0 if EDU_LEVEL[emp_edu] >= EDU_LEVEL[job_edu] else 0.0


def compute_experience_score(emp_years, job_years):
	diff = abs(emp_years - job_years)
	return max(0.0, 1 - diff / 10.0)


def encode_text(model, text):
	"""Encode text to numpy array and store as JSON string."""
	emb = model.encode(str(text), convert_to_numpy=True)
	return json.dumps(emb.tolist())  # JSON string for SQLite


def decode_emb(emb_json):
	if emb_json is None or emb_json == "":
		return None
	return np.array(json.loads(emb_json), dtype=np.float32)


def grade_from_score(total_score):
	if total_score >= 0.90:
		return "A"
	elif total_score >= 0.80:
		return "B"
	elif total_score >= 0.70:
		return "C"
	elif total_score >= 0.60:
		return "D"
	else:
		return "F"


# -----------------------
# CLASS: DB + MATCHING
# -----------------------

class JobEmployeeMatcher:
	_model_cache = None

	def __init__(self, db_path=DB_PATH):
		self.db_path = str(db_path)
		self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
		self.conn.row_factory = sqlite3.Row
		if JobEmployeeMatcher._model_cache is None:
			JobEmployeeMatcher._model_cache = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
		self.model = JobEmployeeMatcher._model_cache
		self._create_schema()

	# ----- DB schema -----

	def _create_schema(self):
		cur = self.conn.cursor()

		# Employees
		cur.execute("""
			CREATE TABLE IF NOT EXISTS employees (
				emp_id TEXT PRIMARY KEY,
				emp_position TEXT,
				emp_skills TEXT,
				emp_education_level TEXT,
				emp_years_experience REAL,
				emp_desired_job TEXT,
				emp_open_to_change REAL,
				learning_hours_per_week REAL DEFAULT 0.0,
				looking_for_opportunities INTEGER DEFAULT 0,
				looking_reason TEXT,
				emp_embedding TEXT
			)
		""")
		cur.execute("PRAGMA table_info(employees)")
		emp_columns = {row["name"] for row in cur.fetchall()}
		if "learning_hours_per_week" not in emp_columns:
			cur.execute("ALTER TABLE employees ADD COLUMN learning_hours_per_week REAL DEFAULT 0.0")
		if "looking_for_opportunities" not in emp_columns:
			cur.execute("ALTER TABLE employees ADD COLUMN looking_for_opportunities INTEGER DEFAULT 0")
		if "looking_reason" not in emp_columns:
			cur.execute("ALTER TABLE employees ADD COLUMN looking_reason TEXT")

		# Jobs
		cur.execute("""
			CREATE TABLE IF NOT EXISTS jobs (
				job_id TEXT PRIMARY KEY,
				job_title TEXT,
				job_required_skills TEXT,
				job_required_education TEXT,
				job_required_experience REAL,
				job_description TEXT,
				job_embedding TEXT
			)
		""")
		cur.execute("PRAGMA table_info(jobs)")
		job_columns = {row["name"] for row in cur.fetchall()}
		if "job_description" not in job_columns:
			cur.execute("ALTER TABLE jobs ADD COLUMN job_description TEXT")

		# Matches
		cur.execute("""
			CREATE TABLE IF NOT EXISTS matches (
				job_id TEXT,
				emp_id TEXT,
				match_mark TEXT,
				match_score REAL,
				skill_overlap REAL,
				education_match REAL,
				experience_score REAL,
				position_similarity REAL,
				intent_score REAL,
				skill_match TEXT,
				skill_miss TEXT,
				PRIMARY KEY (job_id, emp_id),
				FOREIGN KEY (job_id) REFERENCES jobs(job_id),
				FOREIGN KEY (emp_id) REFERENCES employees(emp_id)
			)
		""")

		# Indexes for speed
		cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_job ON matches(job_id)")
		cur.execute("CREATE INDEX IF NOT EXISTS idx_matches_emp ON matches(emp_id)")
		self.conn.commit()

	# ----- Init from CSV (one-time full load) -----

	def init_from_csv(self, emp_file=EMP_FILE, job_file=JOB_FILE):
		"""
		One-time initialization: load CSVs into DB and compute all embeddings + matches.
		If rows already exist with same IDs, they will be overwritten.
		"""
		emp_df = pd.read_csv(emp_file)
		job_df = pd.read_csv(job_file)

		print("🔹 Loading employees into DB & computing embeddings...")
		for _, row in emp_df.iterrows():
			self.upsert_employee_from_dict(row.to_dict(), recompute_matches=False)

		print("🔹 Loading jobs into DB & computing embeddings...")
		for _, row in job_df.iterrows():
			self.upsert_job_from_dict(row.to_dict(), recompute_matches=False)

		print("🔹 Computing full match matrix (all jobs × all employees)...")
		self.recompute_all_matches()
		print("✅ Initialization complete.")

	# ----- Core upsert operations -----

	def upsert_employee_from_dict(self, emp, recompute_matches=True):
		"""
		Insert/update an employee row and its embedding.
		If recompute_matches=True, recompute matches for this employee vs all jobs.
		'emp' is a dict with keys compatible with employees table / CSV.
		"""
		emp_id = str(emp["emp_id"])
		emp_position = emp.get("emp_position", "")
		emp_skills = emp.get("emp_skills", "")
		emp_education_level = emp.get("emp_education_level", "")
		emp_years_experience = float(emp.get("emp_years_experience", 0))
		emp_desired_job = emp.get("emp_desired_job", "")
		emp_open_to_change = float(emp.get("emp_open_to_change", 0))
		learning_hours_per_week = float(emp.get("learning_hours_per_week", emp.get("learning_hours", 0) or 0))
		looking_for_opportunities = 1 if emp.get("looking_for_opportunities") and emp.get("looking_reason") else 0
		looking_reason = emp.get("looking_reason", "") if looking_for_opportunities else ""

		# Rebuild embedding whenever desired_job changes
		emp_embedding = encode_text(self.model, emp_desired_job)

		cur = self.conn.cursor()
		cur.execute("""
			INSERT INTO employees (
				emp_id, emp_position, emp_skills, emp_education_level,
				emp_years_experience, emp_desired_job, emp_open_to_change,
				learning_hours_per_week, looking_for_opportunities,
				looking_reason, emp_embedding
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(emp_id) DO UPDATE SET
				emp_position = excluded.emp_position,
				emp_skills = excluded.emp_skills,
				emp_education_level = excluded.emp_education_level,
				emp_years_experience = excluded.emp_years_experience,
				emp_desired_job = excluded.emp_desired_job,
				emp_open_to_change = excluded.emp_open_to_change,
				learning_hours_per_week = excluded.learning_hours_per_week,
				looking_for_opportunities = excluded.looking_for_opportunities,
				looking_reason = excluded.looking_reason,
				emp_embedding = excluded.emp_embedding
		""", (
			emp_id, emp_position, emp_skills, emp_education_level,
			emp_years_experience, emp_desired_job, emp_open_to_change,
			learning_hours_per_week, looking_for_opportunities,
			looking_reason, emp_embedding,
		))
		self.conn.commit()

		if recompute_matches:
			self._recompute_matches_for_employee(emp_id)

	def upsert_job_from_dict(self, job, recompute_matches=True):
		"""
		Insert/update a job row and its embedding.
		If recompute_matches=True, recompute matches for this job vs all employees.
		'job' is a dict with keys compatible with jobs table / CSV.
		"""
		job_id = str(job["job_id"])
		job_title = job.get("job_title", "")
		job_required_skills = job.get("job_required_skills", "")
		job_required_education = job.get("job_required_education", "")
		job_required_experience = float(job.get("job_required_experience", 0))
		job_description = job.get("job_description", "")

		job_embedding = encode_text(self.model, job_title)

		cur = self.conn.cursor()
		cur.execute("""
			INSERT INTO jobs (
				job_id, job_title, job_required_skills,
				job_required_education, job_required_experience, job_description,
				job_embedding
			) VALUES (?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(job_id) DO UPDATE SET
				job_title = excluded.job_title,
				job_required_skills = excluded.job_required_skills,
				job_required_education = excluded.job_required_education,
				job_required_experience = excluded.job_required_experience,
				job_description = excluded.job_description,
				job_embedding = excluded.job_embedding
		""", (
			job_id, job_title, job_required_skills,
			job_required_education, job_required_experience,
			job_description, job_embedding,
		))
		self.conn.commit()

		if recompute_matches:
			self._recompute_matches_for_job(job_id)

	# ----- Match recomputation -----

	def recompute_all_matches(self):
		"""Full recomputation of the entire job<employee matrix."""
		cur = self.conn.cursor()
		cur.execute("DELETE FROM matches")
		self.conn.commit()

		jobs = self._fetch_all_jobs()
		employees = self._fetch_all_employees()

		for job in jobs:
			print(f"  → Recomputing for job {job['job_id']}")
			self._recompute_matches_for_job(job["job_id"], employees_cache=employees)

	def _fetch_all_employees(self):
		cur = self.conn.cursor()
		cur.execute("SELECT * FROM employees")
		rows = cur.fetchall()
		return rows

	def count_employees(self):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM employees")
		return int(cur.fetchone()[0])

	def _fetch_all_jobs(self):
		cur = self.conn.cursor()
		cur.execute("SELECT * FROM jobs")
		rows = cur.fetchall()
		return rows

	def count_jobs(self):
		cur = self.conn.cursor()
		cur.execute("SELECT COUNT(*) FROM jobs")
		return int(cur.fetchone()[0])

	def close(self):
		self.conn.close()

	def _recompute_matches_for_employee(self, emp_id):
		"""Recompute matches for one employee vs all jobs."""
		cur = self.conn.cursor()
		# Get employee
		cur.execute("SELECT * FROM employees WHERE emp_id = ?", (emp_id,))
		emp = cur.fetchone()
		if emp is None:
			return

		# Delete old matches for this employee
		cur.execute("DELETE FROM matches WHERE emp_id = ?", (emp_id,))
		self.conn.commit()

		emp_emb = decode_emb(emp["emp_embedding"])
		jobs = self._fetch_all_jobs()

		for job in jobs:
			match_row = self._compute_match_row(job, emp, job_emb=None, emp_emb=emp_emb)
			if match_row is not None:
				self._upsert_match_row(match_row)

		self.conn.commit()

	def _recompute_matches_for_job(self, job_id, employees_cache=None):
		"""Recompute matches for one job vs all employees."""
		cur = self.conn.cursor()
		# Get job
		cur.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
		job = cur.fetchone()
		if job is None:
			return

		# Delete old matches for this job
		cur.execute("DELETE FROM matches WHERE job_id = ?", (job_id,))
		self.conn.commit()

		job_emb = decode_emb(job["job_embedding"])
		employees = employees_cache if employees_cache is not None else self._fetch_all_employees()

		for emp in employees:
			match_row = self._compute_match_row(job, emp, job_emb=job_emb, emp_emb=None)
			if match_row is not None:
				self._upsert_match_row(match_row)

		self.conn.commit()

	def _compute_match_row(self, job, emp, job_emb=None, emp_emb=None):
		"""Compute one match row for given job+employee DB rows."""
		job_id = job["job_id"]
		job_title = job["job_title"]
		job_required_skills = job["job_required_skills"]
		job_required_education = job["job_required_education"]
		job_required_experience = float(job["job_required_experience"])

		emp_id = emp["emp_id"]
		emp_position = emp["emp_position"]
		emp_skills = emp["emp_skills"]
		emp_education_level = emp["emp_education_level"]
		emp_years_experience = float(emp["emp_years_experience"])
		emp_desired_job = emp["emp_desired_job"]
		intent_score = float(emp["emp_open_to_change"])

		# embeddings
		if job_emb is None:
			job_emb = decode_emb(job["job_embedding"])
		if emp_emb is None:
			emp_emb = decode_emb(emp["emp_embedding"])

		if job_emb is None or emp_emb is None:
			return None

		# Scores
		skill_overlap = compute_skill_overlap(emp_skills, job_required_skills)
		skill_match, skill_miss = get_skill_match_miss(emp_skills, job_required_skills)
		education_match = compute_education_match(emp_education_level, job_required_education)
		experience_score = compute_experience_score(emp_years_experience, job_required_experience)
		position_similarity = float(util.cos_sim(job_emb, emp_emb))

		total_score = (
			WEIGHTS["skill_overlap"] * skill_overlap +
			WEIGHTS["education_match"] * education_match +
			WEIGHTS["experience_score"] * experience_score +
			WEIGHTS["position_similarity"] * position_similarity +
			WEIGHTS["intent_score"] * intent_score
		)
		match_mark = grade_from_score(total_score)

		return {
			"job_id": job_id,
			"emp_id": emp_id,
			"match_mark": match_mark,
			"match_score": float(round(total_score, 3)),
			"skill_overlap": float(round(skill_overlap, 2)),
			"education_match": float(education_match),
			"experience_score": float(round(experience_score, 2)),
			"position_similarity": float(round(position_similarity, 2)),
			"intent_score": float(intent_score),
			"skill_match": skill_match,
			"skill_miss": skill_miss,
		}

	def _upsert_match_row(self, m):
		cur = self.conn.cursor()
		cur.execute("""
			INSERT INTO matches (
				job_id, emp_id, match_mark, match_score,
				skill_overlap, education_match, experience_score,
				position_similarity, intent_score, skill_match, skill_miss
			) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
			ON CONFLICT(job_id, emp_id) DO UPDATE SET
				match_mark = excluded.match_mark,
				match_score = excluded.match_score,
				skill_overlap = excluded.skill_overlap,
				education_match = excluded.education_match,
				experience_score = excluded.experience_score,
				position_similarity = excluded.position_similarity,
				intent_score = excluded.intent_score,
				skill_match = excluded.skill_match,
				skill_miss = excluded.skill_miss
		""", (
			m["job_id"], m["emp_id"], m["match_mark"], m["match_score"],
			m["skill_overlap"], m["education_match"], m["experience_score"],
			m["position_similarity"], m["intent_score"],
			m["skill_match"], m["skill_miss"],
		))

	# ----- Query helpers for frontend -----

	def top_employees_for_job(self, job_id, top_n=TOP_N_DEFAULT):
		"""
		Return top N employees for a given job_id as a list of dicts.
		This is what your frontend probably wants to call.
		"""
		cur = self.conn.cursor()
		cur.execute("""
			SELECT m.*, e.emp_position
			FROM matches m
			JOIN employees e ON e.emp_id = m.emp_id
			WHERE m.job_id = ?
			ORDER BY m.match_score DESC
			LIMIT ?
		""", (job_id, top_n))
		rows = cur.fetchall()
		return [dict(r) for r in rows]

	def top_jobs_for_employee(self, emp_id, top_n=TOP_N_DEFAULT):
		"""
		Return top N jobs for a given emp_id as a list of dicts.
		"""
		cur = self.conn.cursor()
		cur.execute("""
			SELECT m.*, j.job_title
			FROM matches m
			JOIN jobs j ON j.job_id = m.job_id
			WHERE m.emp_id = ?
			ORDER BY m.match_score DESC
			LIMIT ?
		""", (emp_id, top_n))
		rows = cur.fetchall()
		return [dict(r) for r in rows]


# -----------------------
# CLI-style main for init
# -----------------------

def main():
	matcher = JobEmployeeMatcher(DB_PATH)

	# One-time initialization from CSVs (if DB is empty):
	matcher.init_from_csv(EMP_FILE, JOB_FILE)

	# Show top X employees for each job
	cur = matcher.conn.cursor()
	cur.execute("SELECT job_id, job_title FROM jobs")
	for job in cur.fetchall():
		topX = matcher.top_employees_for_job(job["job_id"], top_n=5)
		print(f"\n🏢 {job['job_title']} ({job['job_id']}) — Top list:")
		for row in topX:
			print(f"   - {row['emp_id']} | score={row['match_score']} | mark={row['match_mark']}")

if __name__ == "__main__":
	main()
