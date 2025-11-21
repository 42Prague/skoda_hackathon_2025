#!/usr/bin/env python3
"""
Generate Comprehensive Test Dataset for ŠKODA AI Skill Coach
Generates 100-150 employees with CZ/EN text, qualifications, hierarchy, learning history
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Departments (mix of Czech and English)
DEPARTMENTS = [
    "Engineering", "Manufacturing", "Quality Assurance", "Research & Development",
    "Sales & Marketing", "Human Resources", "Finance", "IT Services",
    "Supply Chain", "Product Management", "Výroba", "Kvalita", "Prodej"
]

JOB_FAMILIES = [
    "Software Engineer", "Mechanical Engineer", "Data Analyst", "Project Manager",
    "Quality Engineer", "Product Manager", "Business Analyst", "HR Specialist",
    "Financial Analyst", "Supply Chain Manager", "Vývojář", "Inženýr"
]

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

QUALIFICATION_TYPES = [
    "Bachelor's Degree", "Master's Degree", "PhD", "Professional Certification",
    "Industry Training", "Internal Training", "Škoda Academy Module",
    "Bakalářský titul", "Magisterský titul", "Certifikace"
]

TRAINING_COURSES = [
    "Advanced Python Programming", "Docker & Kubernetes Fundamentals",
    "Agile Project Management", "Data Science Bootcamp", "Machine Learning Basics",
    "Cloud Architecture", "DevOps Best Practices", "Leadership Development",
    "Communication Skills", "Advanced Excel", "SQL Mastery",
    "React Advanced Patterns", "Microservices Architecture", "Test Automation",
    "Business Intelligence", "Pokročilý Python", "Základy Dockeru",
    "Agilní metodiky", "Datová analýza", "Vedení týmů"
]

FIRST_NAMES_CZ = ["Jan", "Petr", "Tomáš", "Martin", "Lukáš", "Jakub", "David", "Michal", "Pavel", "Jiří",
                  "Marie", "Jana", "Petra", "Lucie", "Kateřina", "Anna", "Eva", "Martina", "Tereza", "Veronika"]

FIRST_NAMES_EN = ["John", "Michael", "David", "James", "Robert", "William", "Richard", "Joseph", "Thomas", "Charles",
                  "Sarah", "Emily", "Jessica", "Amanda", "Melissa", "Nicole", "Michelle", "Ashley", "Jennifer", "Lisa"]

LAST_NAMES = ["Novák", "Svoboda", "Novotný", "Dvořák", "Černý", "Procházka", "Horák", "Němec", "Pospíšil", "Hájek",
              "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]


def generate_name():
    """Generate Czech or English name."""
    if random.random() < 0.6:  # 60% Czech names
        return random.choice(FIRST_NAMES_CZ), random.choice(LAST_NAMES)
    else:
        return random.choice(FIRST_NAMES_EN), random.choice(LAST_NAMES)


def generate_employee_id(index: int) -> str:
    """Generate employee ID."""
    return f"EMP{str(index).zfill(3)}"


def generate_dataset(num_employees: int = 120, output_dir: Path = Path("")):
    """Generate comprehensive test dataset."""
    output_file = output_dir / "comprehensive_test_dataset.csv"
    learning_history_file = output_dir / "comprehensive_learning_history.csv"
    qualifications_file = output_dir / "comprehensive_qualifications.csv"
    org_hierarchy_file = output_dir / "comprehensive_org_hierarchy.csv"
    
    employees = []
    learning_history_all = {}
    qualifications_all = {}
    org_hierarchy_all = {}
    managers = []
    
    # Generate employees
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "employee_id", "first_name", "last_name", "email", "department",
            "job_family", "job_title", "hire_date", "skills", "years_experience",
            "location", "manager_id", "performance_rating"
        ])
        writer.writeheader()
        
        for i in range(1, num_employees + 1):
            emp_id = generate_employee_id(i)
            first_name, last_name = generate_name()
            email = f"{first_name.lower()}.{last_name.lower()}@skoda-auto.cz"
            department = random.choice(DEPARTMENTS)
            job_family = random.choice(JOB_FAMILIES)
            job_title = f"{job_family} {random.choice(['Junior', 'Mid', 'Senior', 'Lead', 'Principal', 'Junior', 'Středně pokročilý', 'Senior'])}"
            hire_date = (datetime.now() - timedelta(days=random.randint(30, 3650))).strftime("%Y-%m-%d")
            skills = ", ".join(random.sample(SKILLS_POOL, random.randint(5, 15)))
            years_experience = random.randint(1, 20)
            location = random.choice(["Mladá Boleslav", "Praha", "Kvasiny", "Vrchlabí"])
            manager_id = random.choice(managers) if managers and random.random() < 0.7 else ""
            performance_rating = random.choice(["Exceeds", "Meets", "Below", "Překračuje", "Splňuje"])
            
            # Track managers (first 20% are managers)
            if i <= num_employees * 0.2:
                managers.append(emp_id)
            
            employees.append({
                "employee_id": emp_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "department": department,
                "job_family": job_family,
                "job_title": job_title,
                "hire_date": hire_date,
                "skills": skills,
                "years_experience": years_experience,
                "location": location,
                "manager_id": manager_id,
                "performance_rating": performance_rating
            })
            
            # Generate learning history
            learning_history_all[emp_id] = []
            for j in range(random.randint(2, 8)):
                course_date = datetime.now() - timedelta(days=random.randint(1, 365))
                learning_history_all[emp_id].append({
                    "employee_id": emp_id,
                    "course_name": random.choice(TRAINING_COURSES),
                    "completion_date": course_date.strftime("%Y-%m-%d"),
                    "status": random.choice(["Completed", "In Progress", "Completed", "Dokončeno"]),
                    "provider": random.choice(["Škoda Academy", "Coursera", "Udemy", "Internal", "External"])
                })
            
            # Generate qualifications
            if random.random() > 0.3:
                qualifications_all[emp_id] = []
                for j in range(random.randint(1, 3)):
                    qualifications_all[emp_id].append({
                        "employee_id": emp_id,
                        "qualification_id": f"QUAL{random.randint(1, 20)}",
                        "qualification_name_cz": f"Kvalifikace {random.randint(1, 10)}",
                        "qualification_name_en": f"Qualification {random.randint(1, 10)}",
                        "status": random.choice(["active", "expired", "pending"])
                    })
            
            # Generate org hierarchy
            level = random.randint(1, 4)
            org_hierarchy_all[emp_id] = {
                "employee_id": emp_id,
                "level": level,
                "hierarchy_path": f"/Company/{department}/{emp_id}"
            }
            
            writer.writerow(employees[-1])
    
    # Write learning history
    with open(learning_history_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "course_name", "completion_date", "status", "provider"])
        writer.writeheader()
        for emp_id, history in learning_history_all.items():
            for record in history:
                writer.writerow(record)
    
    # Write qualifications
    with open(qualifications_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "qualification_id", "qualification_name_cz", "qualification_name_en", "status"])
        writer.writeheader()
        for emp_id, quals in qualifications_all.items():
            for qual in quals:
                writer.writerow(qual)
    
    # Write org hierarchy
    with open(org_hierarchy_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["employee_id", "level", "hierarchy_path"])
        writer.writeheader()
        for emp_id, hierarchy in org_hierarchy_all.items():
            writer.writerow(hierarchy)
    
    print(f"✅ Generated comprehensive dataset:")
    print(f"   - Employees: {num_employees} ({output_file})")
    print(f"   - Learning history: {len(sum(learning_history_all.values(), []))} records ({learning_history_file})")
    print(f"   - Qualifications: {len(sum(qualifications_all.values(), []))} records ({qualifications_file})")
    print(f"   - Org hierarchy: {len(org_hierarchy_all)} records ({org_hierarchy_file})")
    
    return output_file, learning_history_file, qualifications_file, org_hierarchy_file


if __name__ == "__main__":
    import sys
    num_employees = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("")
    
    generate_dataset(num_employees, output_dir)

