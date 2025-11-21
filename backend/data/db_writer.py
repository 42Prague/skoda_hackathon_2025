"""
Database Writer - Persist parsed employee/skill data to PostgreSQL
"""
import psycopg2
from psycopg2.extras import execute_batch
import os
from typing import Dict, List
from datetime import datetime


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


def persist_parsed_data_to_db(parsed_data: Dict) -> Dict:
    """
    Persist parsed employee/skill data to PostgreSQL

    Args:
        parsed_data: Result from MultiFormatParser.parse()
                     Contains: {'employees': {...}, 'format': '...', 'total_employees': N}

    Returns:
        Dict with success status and stats
    """
    if not parsed_data.get('success', False):
        return {'success': False, 'error': 'Parsed data not successful'}

    employees_data = parsed_data.get('employees', {})
    if not employees_data:
        return {'success': False, 'error': 'No employee data found'}

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Track stats
        employees_inserted = 0
        skills_inserted = 0
        skill_events_inserted = 0

        # Process each employee
        for employee_id, emp_info in employees_data.items():
            # 1. Insert or update employee
            hire_date = emp_info.get('hire_date')
            department = emp_info.get('department', 'Unknown')
            position = emp_info.get('position', 'Unknown')

            cur.execute("""
                INSERT INTO employees (employee_id, hire_date, department, position)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (employee_id) DO UPDATE
                SET hire_date = EXCLUDED.hire_date,
                    department = EXCLUDED.department,
                    position = EXCLUDED.position
                RETURNING employee_id
            """, (employee_id, hire_date, department, position))

            employees_inserted += 1

            # 2. Process skills for this employee
            skills = emp_info.get('skills', [])
            for skill_info in skills:
                skill_name = skill_info.get('name')
                if not skill_name or len(skill_name) < 2:
                    continue  # Skip invalid skills

                # Insert skill if not exists
                cur.execute("""
                    INSERT INTO skills (skill_name)
                    VALUES (%s)
                    ON CONFLICT (skill_name) DO NOTHING
                    RETURNING skill_id
                """, (skill_name,))

                result = cur.fetchone()
                if result:
                    skill_id = result[0]
                    skills_inserted += 1
                else:
                    # Skill already exists, get its ID
                    cur.execute("SELECT skill_id FROM skills WHERE skill_name = %s", (skill_name,))
                    skill_id = cur.fetchone()[0]

                # 3. Insert skill event (employee acquired this skill)
                acquired_date = skill_info.get('acquired_date', datetime.now())
                category = skill_info.get('category', 'General')

                cur.execute("""
                    INSERT INTO skill_events (employee_id, skill_id, event_type, event_date, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (employee_id, skill_id, event_date) DO NOTHING
                """, (employee_id, skill_id, 'acquired', acquired_date, f"Category: {category}"))

                if cur.rowcount > 0:
                    skill_events_inserted += 1

        # Commit transaction
        conn.commit()

        print(f"[DB] Persisted: {employees_inserted} employees, {skills_inserted} new skills, {skill_events_inserted} skill events")

        return {
            'success': True,
            'employees_inserted': employees_inserted,
            'skills_inserted': skills_inserted,
            'skill_events_inserted': skill_events_inserted,
            'format_detected': parsed_data.get('format'),
            'encoding': parsed_data.get('encoding')
        }

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Database persistence failed: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

    finally:
        cur.close()
        conn.close()


def clear_all_data():
    """
    Clear all employee/skill data from database
    WARNING: Use only for testing or fresh uploads
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Delete in correct order (foreign keys)
        cur.execute("DELETE FROM skill_events")
        cur.execute("DELETE FROM employees")
        cur.execute("DELETE FROM skills")
        conn.commit()
        print("[DB] All data cleared")
        return {'success': True}
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to clear data: {e}")
        return {'success': False, 'error': str(e)}
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    # Test database writer
    print("Testing database writer...")

    # Example parsed data structure
    test_data = {
        'success': True,
        'format': 'format6_personnel_stats',
        'employees': {
            'TEST001': {
                'skills': [
                    {'name': 'Python Programming', 'acquired_date': datetime.now(), 'category': 'Technical'},
                    {'name': 'Data Analysis', 'acquired_date': datetime.now(), 'category': 'Technical'}
                ],
                'hire_date': datetime.now(),
                'department': 'Engineering',
                'position': 'Software Developer'
            }
        },
        'total_employees': 1,
        'encoding': 'utf-8'
    }

    result = persist_parsed_data_to_db(test_data)
    print(f"Test result: {result}")
