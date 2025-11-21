#!/usr/bin/env python3
"""
Training Path Builder (DB-integrated)
-------------------------------------
Builds training plans for each job-employee pair
based on missing skills (from SQLite matches table)
and available courses (from CSV).

Writes results into a SQLite table:
	training_plan(job_id, emp_id, ...)
"""

import sqlite3
import csv
import math
from collections import defaultdict

from config import COURSES_CSV as CONFIG_COURSES_CSV, DB_PATH as CONFIG_DB_PATH

COURSES_CSV = str(CONFIG_COURSES_CSV)
DB_PATH = str(CONFIG_DB_PATH)

MAX_INTRO_PER_SKILL = 1
MAX_DEEP_PER_SKILL = 2


# -------------------------
# Helper functions
# -------------------------

def safe_float(value, default=0.0):
	try:
		return float(value)
	except (ValueError, TypeError):
		return default


def load_courses(path):
	"""
	Returns dict: skill -> list[course_dict]
	"""
	by_skill = defaultdict(list)

	with open(path, newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		for row in reader:
			skill = (row.get("skill") or "").strip().lower()
			if not skill:
				continue

			row["points"] = safe_float(row.get("difficulty_score"), 0.5)
			row["hours"] = safe_float(row.get("hours"), 1.0)
			row["rating"] = safe_float(row.get("rating"), 4.0)

			by_skill[skill].append(row)

	return by_skill


def intro_score(course):
	rating = course["rating"]
	hours = course["hours"] if course["hours"] > 0 else 1.0
	points = course["points"]

	return (0.5 * rating + 0.4 * (1.0 / hours) + 0.1 * (1.0 - points))


def deep_score(course):
	rating = course["rating"]
	hours = course["hours"]
	points = course["points"]

	norm_hours = min(hours / 60.0, 1.0)

	return (0.5 * rating + 0.3 * points + 0.2 * norm_hours)


def select_top_courses(courses, score_fn, max_per_skill):
	if not courses:
		return []

	scored = [(score_fn(c), c) for c in courses]
	scored.sort(key=lambda x: x[0], reverse=True)
	return [c for _, c in scored[:max_per_skill]]


# -------------------------
# MAIN CLASS
# -------------------------

class TrainingPathBuilder:

	def __init__(self, db_path=DB_PATH, courses_csv=COURSES_CSV):
		self.db_path = db_path
		self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
		self.conn.row_factory = sqlite3.Row

		self.courses = load_courses(courses_csv)
		self._ensure_schema()

	# Create training_plan table if missing
	def _ensure_schema(self):
		cur = self.conn.cursor()
		cur.execute("""
			CREATE TABLE IF NOT EXISTS training_plan (
				job_id TEXT,
				emp_id TEXT,
				skill_miss TEXT,
				intro_courses_list TEXT,
				deep_courses_list TEXT,
				intro_hours_list TEXT,
				deep_hours_list TEXT,
				intro_total_time_weeks TEXT,
				deep_total_time_weeks TEXT,
				PRIMARY KEY(job_id, emp_id)
			)
		""")

		# employees table needs learning_hours_per_week if missing
		cur.execute("PRAGMA table_info(employees);")
		cols = {row["name"] for row in cur.fetchall()}
		if "learning_hours_per_week" not in cols:
			cur.execute("ALTER TABLE employees ADD COLUMN learning_hours_per_week REAL DEFAULT 0.0")

		self.conn.commit()

	# Load employees learning hours
	def _load_employee_hours(self):
		cur = self.conn.cursor()
		cur.execute("SELECT emp_id, learning_hours_per_week FROM employees")
		return {row["emp_id"]: safe_float(row["learning_hours_per_week"], 0.0)
				for row in cur.fetchall()}

	# Load missing skills (skill_miss) for each job-employee
	def _load_missing_skills(self):
		"""Return list of dicts: job_id, emp_id, skill_miss."""
		cur = self.conn.cursor()
		cur.execute("""
			SELECT job_id, emp_id, skill_miss
			FROM matches
		""")
		return cur.fetchall()

	# Core logic — compute and insert all training plans
	def build_training_plans(self):
		employees_hours = self._load_employee_hours()
		rows = self._load_missing_skills()

		cur = self.conn.cursor()
		updated = 0

		for r in rows:
			job_id = r["job_id"]
			emp_id = r["emp_id"]
			skill_miss_raw = r["skill_miss"] or ""

			missing_skills = [
				s.strip().lower()
				for s in skill_miss_raw.split(";")
				if s.strip()
			]

			intro_courses = []
			deep_courses = []
			intro_hours = []
			deep_hours = []

			# Build plans per skill
			for skill in missing_skills:
				skill_courses = self.courses.get(skill, [])

				intro_for_skill = select_top_courses(
					skill_courses, intro_score, MAX_INTRO_PER_SKILL
				)
				deep_for_skill = select_top_courses(
					skill_courses, deep_score, MAX_DEEP_PER_SKILL
				)

				for c in intro_for_skill:
					intro_courses.append(c)
					intro_hours.append(c["hours"])

				for c in deep_for_skill:
					deep_courses.append(c)
					deep_hours.append(c["hours"])

			# Convert lists to strings
			intro_courses_list = ";".join(c["course_id"] for c in intro_courses) if intro_courses else ""
			deep_courses_list = ";".join(c["course_id"] for c in deep_courses) if deep_courses else ""

			intro_hours_list = ";".join(str(int(h)) if h.is_integer() else str(h) for h in intro_hours) if intro_hours else ""
			deep_hours_list = ";".join(str(int(h)) if h.is_integer() else str(h) for h in deep_hours) if deep_hours else ""

			# Time estimation
			learning_hours = employees_hours.get(emp_id, 0.0)

			if learning_hours > 0:
				intro_total_hours = sum(intro_hours)
				deep_total_hours = sum(deep_hours)

				intro_weeks = math.ceil(intro_total_hours / learning_hours) if intro_total_hours > 0 else 0
				deep_weeks  = math.ceil(deep_total_hours / learning_hours) if deep_total_hours > 0 else 0
			else:
				intro_weeks = ""
				deep_weeks = ""

			# Save to DB
			cur.execute("""
				INSERT OR REPLACE INTO training_plan (
					job_id, emp_id, skill_miss,
					intro_courses_list, deep_courses_list,
					intro_hours_list, deep_hours_list,
					intro_total_time_weeks, deep_total_time_weeks
				) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
			""", (
				job_id, emp_id, skill_miss_raw,
				intro_courses_list, deep_courses_list,
				intro_hours_list, deep_hours_list,
				intro_weeks, deep_weeks
			))
			updated += 1

		self.conn.commit()
		return updated

	def close(self):
		self.conn.close()


# -------------------------
# CLI entry point
# -------------------------

def main():
	builder = TrainingPathBuilder(DB_PATH, COURSES_CSV)
	builder.build_training_plans()
	print("Training plans written to SQLite table 'training_plan'.")


if __name__ == "__main__":
	main()
