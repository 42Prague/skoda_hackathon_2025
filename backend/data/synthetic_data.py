"""
Generate synthetic Škoda-like employee skill data for testing
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import random

# Skill categories matching Škoda's domain
SKILL_CATEGORIES = {
    "legacy_engineering": ["CAD", "Mechanical Design", "CNC Programming", "CATIA", "AutoCAD", "Quality Control"],
    "software_cloud": ["Python", "JavaScript", "React", "AWS", "Azure", "Docker", "Kubernetes", "CI/CD", "Microservices"],
    "e_mobility": ["Battery Systems", "Electric Powertrain", "Charging Infrastructure", "Energy Management", "Thermal Management"],
    "ai_emerging": ["Machine Learning", "TensorFlow", "PyTorch", "LLM Integration", "Computer Vision", "NLP"]
}

def generate_employees(n=500):
    """Generate synthetic employee data"""
    employees = []

    for i in range(n):
        emp_id = f"EMP_{str(i+1).zfill(5)}"

        # Random department
        dept = random.choice(["Engineering", "IT", "E-Mobility", "Digital", "Quality", "Production"])

        # Hire date between 2013-2025
        start_date = datetime(2013, 1, 1)
        end_date = datetime(2025, 8, 1)
        hire_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))

        # Select 2-5 skills (weighted by category and time)
        category_weights = get_category_weights(hire_date)
        num_skills = random.randint(2, 5)

        skills = []
        for _ in range(num_skills):
            category = random.choices(list(SKILL_CATEGORIES.keys()), weights=category_weights)[0]
            skill = random.choice(SKILL_CATEGORIES[category])
            if skill not in skills:
                skills.append(skill)

        employees.append({
            "employee_id": emp_id,
            "department": dept,
            "hire_date": hire_date.strftime("%Y-%m-%d"),
            "skills": skills,
            "position": random.choice(["Junior", "Mid", "Senior", "Lead"])
        })

    return pd.DataFrame(employees)

def get_category_weights(hire_date):
    """Skills evolve over time - newer employees have more modern skills"""
    year = hire_date.year

    if year < 2017:
        return [0.5, 0.3, 0.1, 0.1]  # Heavy legacy
    elif year < 2020:
        return [0.3, 0.4, 0.2, 0.1]  # Transitioning
    elif year < 2023:
        return [0.2, 0.35, 0.3, 0.15]  # E-mobility rising
    else:
        return [0.15, 0.3, 0.3, 0.25]  # AI emerging

def generate_skill_evolution_data():
    """Generate time-series data showing skill popularity 2013-2025"""
    years = list(range(2013, 2026))

    evolution_data = []
    for category, skills in SKILL_CATEGORIES.items():
        for skill in skills:
            for year in years:
                # Simulate growth/decline patterns
                if category == "legacy_engineering":
                    trend = 100 * (0.95 ** (year - 2013))  # Declining
                elif category == "software_cloud":
                    trend = 20 + 80 * (1 - np.exp(-0.3 * (year - 2013)))  # Rapid growth then plateau
                elif category == "e_mobility":
                    trend = 5 + 95 * (1 - np.exp(-0.5 * (year - 2018)))  # Explosive growth after 2018
                elif category == "ai_emerging":
                    trend = 2 + 98 * (1 - np.exp(-0.8 * (year - 2022)))  # Explosive growth after 2022

                # Add noise
                trend += np.random.normal(0, 5)
                trend = max(0, trend)

                evolution_data.append({
                    "year": year,
                    "skill": skill,
                    "category": category,
                    "popularity": round(trend, 1)
                })

    return pd.DataFrame(evolution_data)

def save_synthetic_data():
    """Generate and save all synthetic datasets"""

    # Employee data
    employees_df = generate_employees(500)
    employees_df.to_csv("data/employees.csv", index=False)

    # Skill evolution
    evolution_df = generate_skill_evolution_data()
    evolution_df.to_csv("data/skill_evolution.csv", index=False)

    # Create skill-employee matrix (for clustering)
    all_skills = [skill for skills_list in SKILL_CATEGORIES.values() for skill in skills_list]

    skill_matrix = []
    for _, emp in employees_df.iterrows():
        row = {"employee_id": emp["employee_id"]}
        for skill in all_skills:
            row[skill] = 1 if skill in emp["skills"] else 0
        skill_matrix.append(row)

    skill_matrix_df = pd.DataFrame(skill_matrix)
    skill_matrix_df.to_csv("data/skill_matrix.csv", index=False)

    print(f"[OK] Generated {len(employees_df)} employees")
    print(f"[OK] Generated skill evolution data ({len(evolution_df)} records)")
    print(f"[OK] Generated skill matrix ({len(skill_matrix_df)} rows x {len(all_skills)} skills)")

    return employees_df, evolution_df, skill_matrix_df

if __name__ == "__main__":
    save_synthetic_data()
