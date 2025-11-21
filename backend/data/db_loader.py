"""
Database Loader - Replaces synthetic CSV with real PostgreSQL data
"""
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Tuple
from data.skill_categorizer import SkillCategorizer

def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure DATABASE_URL with your PostgreSQL connection string. "
            "Example: postgresql://user:password@host:port/database"
        )

    return psycopg2.connect(database_url)

def load_skill_matrix_from_db() -> pd.DataFrame:
    """
    Query PostgreSQL and build skill matrix (wide format)
    Returns: DataFrame with columns: employee_id, skill1, skill2, ...
    Each skill column is binary (1 = has skill, 0 = doesn't)
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get all unique skills
        cur.execute("SELECT DISTINCT skill_name FROM skills ORDER BY skill_name")
        all_skills = [row['skill_name'] for row in cur.fetchall()]

        # Get employee-skill pairs
        cur.execute("""
            SELECT DISTINCT e.employee_id, s.skill_name
            FROM employees e
            JOIN skill_events se ON e.employee_id = se.employee_id
            JOIN skills s ON se.skill_id = s.skill_id
        """)
        employee_skills = cur.fetchall()

        # Get all employees
        cur.execute("SELECT DISTINCT employee_id FROM employees ORDER BY employee_id")
        all_employees = [row['employee_id'] for row in cur.fetchall()]

        # Build skill matrix
        skill_matrix = []
        for emp_id in all_employees:
            row = {"employee_id": emp_id}
            emp_skill_set = {es['skill_name'] for es in employee_skills if es['employee_id'] == emp_id}

            for skill in all_skills:
                row[skill] = 1 if skill in emp_skill_set else 0

            skill_matrix.append(row)

        df = pd.DataFrame(skill_matrix)
        print(f"[DB] Loaded skill matrix: {len(df)} employees x {len(all_skills)} skills")

        return df

    finally:
        cur.close()
        conn.close()

def load_skill_evolution_from_db() -> pd.DataFrame:
    """
    Query PostgreSQL and build time-series evolution data
    Returns: DataFrame with columns: skill, year, employee_count
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Get skill evolution by year
        cur.execute("""
            SELECT
                s.skill_name as skill,
                EXTRACT(YEAR FROM se.event_date) as year,
                COUNT(DISTINCT se.employee_id) as popularity,
                COALESCE(s.skill_category, 'General') as category
            FROM skills s
            JOIN skill_events se ON s.skill_id = se.skill_id
            WHERE se.event_date IS NOT NULL
            GROUP BY s.skill_name, s.skill_category, EXTRACT(YEAR FROM se.event_date)
            ORDER BY skill, year
        """)

        evolution_data = cur.fetchall()
        df = pd.DataFrame(evolution_data)

        # Auto-categorize ALL skills using keyword-based categorizer
        # This overrides any existing categories with intelligent categorization
        if len(df) > 0:
            expected_categories = ['legacy_engineering', 'software_cloud', 'e_mobility', 'ai_emerging']
            before_categories = df['category'].value_counts().to_dict()

            df['category'] = df['skill'].apply(SkillCategorizer.categorize)

            after_categories = df['category'].value_counts().to_dict()
            categorized_count = len(df[df['category'].isin(expected_categories)])
            print(f"[DB] Auto-categorized {categorized_count} skills into {len(after_categories)} categories")
            print(f"[DB] Category distribution: {after_categories}")

        if len(df) == 0:
            # If no data, create minimal placeholder
            print("[DB] Warning: No evolution data found, creating minimal dataset")
            df = pd.DataFrame({
                'skill': ['Python'],
                'year': [2024],
                'popularity': [1],
                'category': ['General']
            })
        else:
            print(f"[DB] Loaded skill evolution: {len(df)} records")

        return df

    finally:
        cur.close()
        conn.close()

def load_all_from_db() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load both skill matrix and evolution data from PostgreSQL
    Returns: (skill_matrix_df, evolution_df)
    """
    try:
        skill_matrix = load_skill_matrix_from_db()
        evolution = load_skill_evolution_from_db()
        return skill_matrix, evolution
    except Exception as e:
        print(f"[ERROR] Failed to load data from database: {e}")
        # Return minimal DataFrames to prevent crashes
        skill_matrix = pd.DataFrame({"employee_id": []})
        evolution = pd.DataFrame({"skill": [], "year": [], "popularity": [], "category": []})
        return skill_matrix, evolution

if __name__ == "__main__":
    # Test loading
    print("Testing database loader...")
    skill_matrix, evolution = load_all_from_db()
    print(f"\nSkill Matrix Shape: {skill_matrix.shape}")
    print(f"Evolution Data Shape: {evolution.shape}")
    print("\nSkill Matrix Sample:")
    print(skill_matrix.head())
    print("\nEvolution Data Sample:")
    print(evolution.head())
