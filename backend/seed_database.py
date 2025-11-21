#!/usr/bin/env python3
"""
Seed database with test LMS data
"""
import os
import psycopg2
from datetime import datetime

# Get DATABASE_URL from environment (Fly.io sets this)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please configure DATABASE_URL with your PostgreSQL connection string. "
        "Example: postgresql://user:password@host:port/database"
    )

def parse_date(date_str):
    """Parse DD.MM.YYYY to YYYY-MM-DD"""
    day, month, year = date_str.split('.')
    return f"{year}-{month}-{day}"

def normalize_proficiency(points):
    """Convert 0-100 points to 1-5 proficiency level"""
    points = int(points)
    if points >= 95:
        return 5
    elif points >= 85:
        return 4
    elif points >= 75:
        return 3
    elif points >= 60:
        return 2
    else:
        return 1

def seed_database():
    print("🌱 Seeding database...")

    # Connect to database
    print(f"📡 Connecting to database...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Embedded test data (from test_lms_cz.csv)
    test_data = [
        {"Completed Date": "15.03.2024", "Employee ID": "EMP001", "Content Title": "Python Programování", "Content Type": "Programming", "Completion Points": "100"},
        {"Completed Date": "22.03.2024", "Employee ID": "EMP001", "Content Title": "Strojové učení - Základy", "Content Type": "Machine Learning", "Completion Points": "95"},
        {"Completed Date": "10.04.2024", "Employee ID": "EMP002", "Content Title": "CAD Design pokročilý", "Content Type": "CAD Software", "Completion Points": "90"},
        {"Completed Date": "18.04.2024", "Employee ID": "EMP002", "Content Title": "AutoCAD 2024", "Content Type": "CAD Software", "Completion Points": "88"},
        {"Completed Date": "25.04.2024", "Employee ID": "EMP003", "Content Title": "React Frontend vývoj", "Content Type": "Web Development", "Completion Points": "92"},
        {"Completed Date": "02.05.2024", "Employee ID": "EMP003", "Content Title": "TypeScript pro React", "Content Type": "Programming", "Completion Points": "94"},
        {"Completed Date": "10.05.2024", "Employee ID": "EMP004", "Content Title": "Bateriové systémy - Elektromobily", "Content Type": "E-Mobility", "Completion Points": "98"},
        {"Completed Date": "15.05.2024", "Employee ID": "EMP004", "Content Title": "Nabíjecí infrastruktura", "Content Type": "E-Mobility", "Completion Points": "96"},
        {"Completed Date": "20.05.2024", "Employee ID": "EMP005", "Content Title": "Docker a Kubernetes", "Content Type": "Cloud Computing", "Completion Points": "91"},
        {"Completed Date": "28.05.2024", "Employee ID": "EMP005", "Content Title": "AWS Certifikace", "Content Type": "Cloud Computing", "Completion Points": "93"},
        {"Completed Date": "05.06.2024", "Employee ID": "EMP006", "Content Title": "CATIA V6 pokročilý", "Content Type": "CAD Software", "Completion Points": "87"},
        {"Completed Date": "12.06.2024", "Employee ID": "EMP006", "Content Title": "Mechanický design", "Content Type": "Mechanical Engineering", "Completion Points": "89"},
        {"Completed Date": "18.06.2024", "Employee ID": "EMP007", "Content Title": "TensorFlow a PyTorch", "Content Type": "Machine Learning", "Completion Points": "97"},
        {"Completed Date": "25.06.2024", "Employee ID": "EMP007", "Content Title": "LLM integrace", "Content Type": "AI/ML", "Completion Points": "99"},
        {"Completed Date": "01.07.2024", "Employee ID": "EMP008", "Content Title": "CNC Programování", "Content Type": "Manufacturing", "Completion Points": "85"},
        {"Completed Date": "08.07.2024", "Employee ID": "EMP008", "Content Title": "Průmyslová automatizace", "Content Type": "Manufacturing", "Completion Points": "86"},
        {"Completed Date": "15.07.2024", "Employee ID": "EMP009", "Content Title": "Azure Cloud fundamentals", "Content Type": "Cloud Computing", "Completion Points": "90"},
        {"Completed Date": "22.07.2024", "Employee ID": "EMP009", "Content Title": "Node.js Backend", "Content Type": "Web Development", "Completion Points": "88"},
        {"Completed Date": "29.07.2024", "Employee ID": "EMP010", "Content Title": "Elektrický pohon", "Content Type": "E-Mobility", "Completion Points": "95"},
        {"Completed Date": "05.08.2024", "Employee ID": "EMP010", "Content Title": "ADAS systémy", "Content Type": "E-Mobility", "Completion Points": "94"},
        {"Completed Date": "12.08.2024", "Employee ID": "EMP001", "Content Title": "Java Enterprise", "Content Type": "Programming", "Completion Points": "87"},
        {"Completed Date": "19.08.2024", "Employee ID": "EMP002", "Content Title": "SolidWorks advanced", "Content Type": "CAD Software", "Completion Points": "89"},
        {"Completed Date": "26.08.2024", "Employee ID": "EMP003", "Content Title": "Next.js 14", "Content Type": "Web Development", "Completion Points": "93"},
        {"Completed Date": "02.09.2024", "Employee ID": "EMP004", "Content Title": "Lithium-ion baterie", "Content Type": "E-Mobility", "Completion Points": "96"},
        {"Completed Date": "09.09.2024", "Employee ID": "EMP005", "Content Title": "Kubernetes produkce", "Content Type": "Cloud Computing", "Completion Points": "92"},
        {"Completed Date": "16.09.2024", "Employee ID": "EMP006", "Content Title": "Konstrukční výkresy", "Content Type": "Mechanical Engineering", "Completion Points": "84"},
        {"Completed Date": "23.09.2024", "Employee ID": "EMP007", "Content Title": "Deep Learning neural sítě", "Content Type": "Machine Learning", "Completion Points": "98"},
        {"Completed Date": "30.09.2024", "Employee ID": "EMP008", "Content Title": "Robotická automatizace", "Content Type": "Manufacturing", "Completion Points": "91"},
        {"Completed Date": "07.10.2024", "Employee ID": "EMP009", "Content Title": "MongoDB databáze", "Content Type": "Database", "Completion Points": "89"},
        {"Completed Date": "14.10.2024", "Employee ID": "EMP010", "Content Title": "Charging infrastructure V2G", "Content Type": "E-Mobility", "Completion Points": "97"},
    ]

    print(f"📄 Processing {len(test_data)} training records")

    employees = set()
    skills = {}  # skill_name -> category
    skill_events = []

    for row in test_data:
        emp_id = row['Employee ID']
        skill_name = row['Content Title']
        skill_category = row['Content Type']
        event_date = parse_date(row['Completed Date'])
        proficiency = normalize_proficiency(row['Completion Points'])

        employees.add(emp_id)
        skills[skill_name] = skill_category
        skill_events.append({
            'employee_id': emp_id,
            'skill_name': skill_name,
            'event_date': event_date,
            'proficiency': proficiency
        })

    print(f"📊 Found {len(employees)} employees, {len(skills)} skills, {len(skill_events)} events")

    # Insert employees
    print("👥 Inserting employees...")
    for emp_id in employees:
        cur.execute("""
            INSERT INTO employees (employee_id, first_name, last_name, department)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (employee_id) DO NOTHING
        """, (emp_id, f"Employee", emp_id.replace('EMP', ''), 'Engineering'))

    # Insert skills
    print("🎯 Inserting skills...")
    skill_id_map = {}
    for skill_name, category in skills.items():
        cur.execute("""
            INSERT INTO skills (skill_name, skill_category)
            VALUES (%s, %s)
            ON CONFLICT (skill_name) DO UPDATE SET skill_category = EXCLUDED.skill_category
            RETURNING skill_id
        """, (skill_name, category))
        skill_id = cur.fetchone()[0]
        skill_id_map[skill_name] = skill_id

    # Insert skill events
    print("📅 Inserting skill events...")
    for event in skill_events:
        skill_id = skill_id_map[event['skill_name']]
        cur.execute("""
            INSERT INTO skill_events (employee_id, skill_id, event_date, event_type, proficiency_level, source)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            event['employee_id'],
            skill_id,
            event['event_date'],
            'training',
            event['proficiency'],
            'LMS'
        ))

    # Record upload
    print("📝 Recording upload history...")
    cur.execute("""
        INSERT INTO upload_history (filename, format_detected, rows_processed, status)
        VALUES (%s, %s, %s, %s)
    """, ('test_lms_cz.csv', 'format3_lms', len(skill_events), 'success'))

    # Commit
    conn.commit()
    cur.close()
    conn.close()

    print("✅ Database seeded successfully!")
    print(f"   - {len(employees)} employees")
    print(f"   - {len(skills)} skills")
    print(f"   - {len(skill_events)} skill events")

if __name__ == "__main__":
    seed_database()
