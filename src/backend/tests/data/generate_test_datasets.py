"""
Test Dataset Generator
---------------------
Generate test datasets for E2E and load testing.
"""

import csv
import json
import random
from pathlib import Path
from typing import List, Dict

# Skills pool (35 skills as required)
SKILLS_POOL = [
    "Python", "JavaScript", "React", "Node.js", "SQL", "Docker", "Kubernetes",
    "AWS", "Azure", "Java", "C++", "Go", "Rust", "TypeScript", "Vue.js",
    "Angular", "MongoDB", "PostgreSQL", "Redis", "Kafka", "GraphQL",
    "REST API", "Microservices", "CI/CD", "Git", "Linux", "Agile", "Scrum",
    "Project Management", "Data Analysis", "Machine Learning", "Deep Learning",
    "NLP", "Computer Vision", "Statistics"
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "IT"
]


def generate_e2e_dataset(output_path: Path, num_employees: int = 200):
    """Generate E2E test dataset with 200 employees, 35 skills, PII, missing values."""
    rows = []
    rows.append("employee_id,department,skills,email,years_experience,location\n")
    
    for i in range(num_employees):
        emp_id = f"EMP{i:03d}"
        dept = random.choice(DEPARTMENTS)
        
        # Inconsistent skill naming
        num_skills = random.randint(3, 10)
        selected_skills = random.sample(SKILLS_POOL, k=num_skills)
        
        # Add inconsistent naming variants
        skill_variants = {
            "Python": ["python", "Python", "PYTHON", "Python3"],
            "JavaScript": ["javascript", "JS", "js", "JavaScript"],
            "React": ["react", "React", "ReactJS", "react.js"]
        }
        
        skills_list = []
        for skill in selected_skills:
            if skill in skill_variants:
                skills_list.append(random.choice(skill_variants[skill]))
            else:
                skills_list.append(skill)
        
        skills_str = ",".join(skills_list)
        
        # PII with some missing (10% missing emails, 5% missing years, 15% missing location)
        email = f"emp{i:03d}@example.com" if random.random() > 0.1 else ""
        years = random.randint(1, 15) if random.random() > 0.05 else ""
        location = random.choice(["Prague", "Brno", "Ostrava"]) if random.random() > 0.15 else ""
        
        rows.append(f"{emp_id},{dept},{skills_str},{email},{years},{location}\n")
    
    output_path.write_text("".join(rows))
    print(f"Generated E2E dataset: {output_path} ({num_employees} employees)")


def generate_load_test_dataset(output_path: Path, num_employees: int = 2000):
    """Generate load test dataset with 2000 employees."""
    rows = []
    rows.append("employee_id,department,skills,email,years_experience\n")
    
    for i in range(num_employees):
        emp_id = f"LOAD{i:04d}"
        dept = random.choice(DEPARTMENTS)
        num_skills = random.randint(3, 8)
        selected_skills = random.sample(SKILLS_POOL, k=num_skills)
        skills_str = ",".join(selected_skills)
        email = f"load{i:04d}@example.com"
        years = random.randint(1, 15)
        
        rows.append(f"{emp_id},{dept},{skills_str},{email},{years}\n")
    
    output_path.write_text("".join(rows))
    print(f"Generated load test dataset: {output_path} ({num_employees} employees)")


def generate_json_dataset(output_path: Path, num_employees: int = 50):
    """Generate JSON format dataset."""
    employees = []
    
    for i in range(num_employees):
        emp_id = f"JSON{i:03d}"
        dept = random.choice(DEPARTMENTS)
        num_skills = random.randint(3, 8)
        selected_skills = random.sample(SKILLS_POOL, k=num_skills)
        
        employee = {
            "employee_id": emp_id,
            "department": dept,
            "skills": selected_skills,
            "email": f"{emp_id.lower()}@example.com",
            "years_experience": random.randint(1, 15)
        }
        employees.append(employee)
    
    output_path.write_text(json.dumps(employees, indent=2))
    print(f"Generated JSON dataset: {output_path} ({num_employees} employees)")


if __name__ == "__main__":
    data_dir = Path(__file__).parent
    
    # Generate E2E dataset
    e2e_path = data_dir / "e2e_dataset.csv"
    generate_e2e_dataset(e2e_path, num_employees=200)
    
    # Generate load test dataset
    load_path = data_dir / "load_test_dataset.csv"
    generate_load_test_dataset(load_path, num_employees=2000)
    
    # Generate JSON dataset
    json_path = data_dir / "test_dataset.json"
    generate_json_dataset(json_path, num_employees=50)
    
    print("\n✅ All test datasets generated successfully!")

