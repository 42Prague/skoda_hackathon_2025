#!/usr/bin/env python3
"""
Generate Fake Dataset for ŠKODA AI Skill Coach Smoke Testing
Creates a realistic CSV with 50-120 employees, departments, skills, qualifications
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Departments
DEPARTMENTS = [
    "Engineering",
    "Manufacturing",
    "Quality Assurance",
    "Research & Development",
    "Sales & Marketing",
    "Human Resources",
    "Finance",
    "IT Services",
    "Supply Chain",
    "Product Management"
]

# Job Families
JOB_FAMILIES = [
    "Software Engineer",
    "Mechanical Engineer",
    "Data Analyst",
    "Project Manager",
    "Quality Engineer",
    "Product Manager",
    "Business Analyst",
    "HR Specialist",
    "Financial Analyst",
    "Supply Chain Manager"
]

# Skills (mix of Czech and English)
SKILLS_POOL = [
    "Python", "Java", "JavaScript", "C++", "SQL", "Docker", "Kubernetes",
    "React", "Angular", "Vue.js", "Node.js", "FastAPI", "PostgreSQL",
    "MongoDB", "Redis", "AWS", "Azure", "GCP", "Machine Learning",
    "Data Science", "TensorFlow", "PyTorch", "Pandas", "NumPy",
    "CAD", "SolidWorks", "AutoCAD", "CATIA", "ANSYS", "FEA",
    "Agile", "Scrum", "Kanban", "JIRA", "Confluence", "Git",
    "CI/CD", "Jenkins", "GitLab", "GitHub Actions", "Terraform",
    "Ansible", "Linux", "Bash", "PowerShell", "Kubernetes",
    "Microservices", "REST API", "GraphQL", "gRPC", "WebSocket",
    "Test Automation", "Selenium", "Cypress", "Jest", "Pytest",
    "Business Intelligence", "Tableau", "Power BI", "Excel",
    "Project Management", "Risk Management", "Stakeholder Management",
    "Německý jazyk", "Anglický jazyk", "Český jazyk", "Francouzský jazyk",
    "Komunikace", "Prezentace", "Vedení týmu", "Řešení problémů"
]

# Qualification Types
QUALIFICATION_TYPES = [
    "Bachelor's Degree",
    "Master's Degree",
    "PhD",
    "Professional Certification",
    "Industry Training",
    "Internal Training",
    "Škoda Academy Module"
]

# Training Courses
TRAINING_COURSES = [
    "Advanced Python Programming",
    "Docker & Kubernetes Fundamentals",
    "Agile Project Management",
    "Data Science Bootcamp",
    "Machine Learning Basics",
    "Cloud Architecture",
    "DevOps Best Practices",
    "Leadership Development",
    "Communication Skills",
    "Advanced Excel",
    "SQL Mastery",
    "React Advanced Patterns",
    "Microservices Architecture",
    "Test Automation",
    "Business Intelligence",
    "Pokročilý Python",
    "Základy Dockeru",
    "Agilní metodiky",
    "Datová analýza",
    "Vedení týmů"
]


def generate_employee_id(index: int) -> str:
    """Generate employee ID."""
    return f"EMP-{index:03d}"


def generate_name() -> tuple[str, str]:
    """Generate Czech or English name."""
    first_names_cz = ["Jan", "Petr", "Tomáš", "Martin", "Lukáš", "Jakub", "David", "Michal", "Pavel", "Jiří",
                     "Marie", "Jana", "Petra", "Lucie", "Kateřina", "Anna", "Eva", "Martina", "Tereza", "Veronika"]
    first_names_en = ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Joseph", "Thomas", "Charles",
                      "Sarah", "Emily", "Jessica", "Amanda", "Melissa", "Nicole", "Michelle", "Ashley", "Jennifer", "Lisa"]
    last_names_cz = ["Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Horák", "Němec", "Pospíšil", "Hájek"]
    last_names_en = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    if random.random() < 0.6:  # 60% Czech names
        return random.choice(first_names_cz), random.choice(last_names_cz)
    else:
        return random.choice(first_names_en), random.choice(last_names_cz)


def generate_skills() -> str:
    """Generate comma-separated skills."""
    num_skills = random.randint(5, 15)
    selected_skills = random.sample(SKILLS_POOL, min(num_skills, len(SKILLS_POOL)))
    return ", ".join(selected_skills)


def generate_qualifications() -> str:
    """Generate qualifications."""
    num_quals = random.randint(1, 3)
    quals = []
    for _ in range(num_quals):
        qual_type = random.choice(QUALIFICATION_TYPES)
        if "Degree" in qual_type:
            field = random.choice(["Computer Science", "Engineering", "Business", "Mathematics", "Physics"])
            quals.append(f"{qual_type} in {field}")
        else:
            quals.append(qual_type)
    return "; ".join(quals)


def generate_learning_history(employee_id: str) -> list[dict]:
    """Generate learning history records."""
    num_courses = random.randint(2, 8)
    history = []
    base_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_courses):
        course_date = base_date + timedelta(days=random.randint(0, 365))
        course = random.choice(TRAINING_COURSES)
        status = random.choice(["Completed", "In Progress", "Completed"])
        history.append({
            "course_name": course,
            "completion_date": course_date.strftime("%Y-%m-%d"),
            "status": status,
            "provider": random.choice(["Škoda Academy", "Coursera", "Udemy", "Internal", "External"])
        })
    
    return history


def generate_dataset(num_employees: int = 80, output_path: str = "fake_skoda_dataset.csv"):
    """Generate fake dataset CSV."""
    output_file = Path(output_path)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "employee_id",
            "first_name",
            "last_name",
            "email",
            "department",
            "job_family",
            "job_title",
            "hire_date",
            "skills",
            "qualifications",
            "years_experience",
            "location",
            "manager_id",
            "salary_range",
            "performance_rating"
        ])
        
        # Generate employees
        managers = []
        learning_history_all = {}
        
        for i in range(1, num_employees + 1):
            emp_id = generate_employee_id(i)
            first_name, last_name = generate_name()
            email = f"{first_name.lower()}.{last_name.lower()}@skoda-auto.cz"
            department = random.choice(DEPARTMENTS)
            job_family = random.choice(JOB_FAMILIES)
            job_title = f"{job_family} {random.choice(['Junior', 'Mid', 'Senior', 'Lead', 'Principal'])}"
            hire_date = (datetime.now() - timedelta(days=random.randint(30, 3650))).strftime("%Y-%m-%d")
            skills = generate_skills()
            qualifications = generate_qualifications()
            years_experience = random.randint(1, 20)
            location = random.choice(["Mladá Boleslav", "Praha", "Kvasiny", "Vrchlabí"])
            manager_id = random.choice(managers) if managers and random.random() < 0.7 else ""
            salary_range = random.choice(["30-50k", "50-70k", "70-90k", "90-120k", "120k+"])
            performance_rating = random.choice(["Exceeds", "Meets", "Below"])
            
            # Track managers (first 20% are managers)
            if i <= num_employees * 0.2:
                managers.append(emp_id)
            
            # Generate learning history
            learning_history_all[emp_id] = generate_learning_history(emp_id)
            
            writer.writerow([
                emp_id,
                first_name,
                last_name,
                email,
                department,
                job_family,
                job_title,
                hire_date,
                skills,
                qualifications,
                years_experience,
                location,
                manager_id,
                salary_range,
                performance_rating
            ])
    
    # Generate learning history CSV
    learning_history_file = output_file.parent / "fake_learning_history.csv"
    with open(learning_history_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["employee_id", "course_name", "completion_date", "status", "provider"])
        
        for emp_id, history in learning_history_all.items():
            for record in history:
                writer.writerow([
                    emp_id,
                    record["course_name"],
                    record["completion_date"],
                    record["status"],
                    record["provider"]
                ])
    
    print(f"✅ Generated dataset: {output_file}")
    print(f"   - Employees: {num_employees}")
    print(f"   - Learning history: {learning_history_file}")
    print(f"   - Total size: {output_file.stat().st_size / 1024:.2f} KB")
    
    return output_file, learning_history_file


if __name__ == "__main__":
    import sys
    num_employees = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    output_path = sys.argv[2] if len(sys.argv) > 2 else "fake_skoda_dataset.csv"
    
    generate_dataset(num_employees, output_path)

