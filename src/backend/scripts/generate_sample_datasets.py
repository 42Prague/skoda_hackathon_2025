"""
Generate Sample Employee Datasets for Testing
---------------------------------------------
Creates multiple synthetic employee datasets for comprehensive testing.
"""

import csv
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


# Sample data pools
DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "HR", "Finance", 
    "Operations", "IT", "Manufacturing", "Quality Assurance", "Customer Support"
]

SKILL_SETS = {
    "Engineering": [
        "Python", "JavaScript", "Java", "C++", "React", "Node.js", 
        "Docker", "Kubernetes", "AWS", "SQL", "Git", "CI/CD"
    ],
    "Sales": [
        "CRM", "Negotiation", "Communication", "Presentation", 
        "Lead Generation", "Customer Relations", "Salesforce", "HubSpot"
    ],
    "Marketing": [
        "SEO", "Content Writing", "Social Media", "Analytics", 
        "Google Ads", "Email Marketing", "Brand Management", "Copywriting"
    ],
    "HR": [
        "Recruitment", "Talent Management", "Employee Relations", 
        "Performance Management", "Compensation", "Benefits", "Training"
    ],
    "Finance": [
        "Accounting", "Financial Analysis", "Budgeting", "Excel", 
        "SAP", "QuickBooks", "Auditing", "Tax Planning"
    ],
    "IT": [
        "Linux", "Networking", "Security", "System Administration", 
        "Troubleshooting", "Help Desk", "Cloud Infrastructure"
    ],
    "Manufacturing": [
        "Lean Manufacturing", "Six Sigma", "Quality Control", 
        "Process Improvement", "Equipment Maintenance", "Safety"
    ],
    "Quality Assurance": [
        "Testing", "QA Automation", "Selenium", "JIRA", 
        "Test Planning", "Bug Tracking", "Regression Testing"
    ],
    "Operations": [
        "Process Management", "Supply Chain", "Logistics", 
        "Vendor Management", "Project Management", "Agile"
    ],
    "Customer Support": [
        "Customer Service", "Problem Solving", "Ticketing Systems", 
        "Product Knowledge", "Escalation Management", "Documentation"
    ]
}

ROLES = {
    "Engineering": ["Junior Engineer", "Software Engineer", "Senior Engineer", "Tech Lead", "Engineering Manager"],
    "Sales": ["Sales Representative", "Senior Sales Rep", "Sales Manager", "Regional Manager", "VP Sales"],
    "Marketing": ["Marketing Coordinator", "Marketing Specialist", "Marketing Manager", "Marketing Director", "CMO"],
    "HR": ["HR Coordinator", "HR Specialist", "HR Manager", "HR Director", "CHRO"],
    "Finance": ["Accountant", "Senior Accountant", "Finance Manager", "Finance Director", "CFO"],
    "IT": ["IT Support", "System Administrator", "IT Manager", "IT Director", "CTO"],
    "Manufacturing": ["Production Worker", "Line Supervisor", "Production Manager", "Plant Manager", "VP Operations"],
    "Quality Assurance": ["QA Tester", "QA Engineer", "QA Manager", "QA Director", "VP Quality"],
    "Operations": ["Operations Coordinator", "Operations Manager", "Operations Director", "VP Operations", "COO"],
    "Customer Support": ["Support Agent", "Senior Support Agent", "Support Manager", "Support Director", "VP Support"]
}

NAMES = [
    "Jan Novák", "Marie Svobodová", "Tomáš Dvořák", "Eva Černá", "Petr Procházka",
    "Jana Krejčí", "Martin Veselý", "Lucie Horáková", "Pavel Novotný", "Hana Pokorná",
    "Michal Pospíšil", "Lenka Fialová", "David Havlíček", "Martina Doležalová", "Ondřej Jelínek",
    "Kateřina Kovářová", "Jakub Václavík", "Jitka Říhová", "Lukáš Musil", "Michaela Sedláčková",
    "Martin Marek", "Eliška Kubíčková", "Matěj Kratochvíl", "Tereza Konečná", "Filip Valenta",
    "Adéla Holubová", "Vojtěch Bláha", "Nikola Malá", "Dominik Soukup", "Barbora Čížková"
]

EMAIL_DOMAINS = ["skoda-auto.cz", "volkswagen.cz", "mazda.cz", "toyota.cz"]


def generate_employee_id(index: int, prefix: str = "EMP") -> str:
    """Generate employee ID."""
    return f"{prefix}{index:05d}"


def generate_skills(department: str, num_skills: int = None) -> List[str]:
    """Generate random skills for a department."""
    available_skills = SKILL_SETS.get(department, SKILL_SETS["Engineering"])
    
    if num_skills is None:
        num_skills = random.randint(3, min(8, len(available_skills)))
    
    return random.sample(available_skills, min(num_skills, len(available_skills)))


def generate_training_history(employee_id: str, num_trainings: int = None) -> List[Dict[str, Any]]:
    """Generate training history."""
    if num_trainings is None:
        num_trainings = random.randint(0, 5)
    
    trainings = []
    start_date = datetime.now() - timedelta(days=365 * 2)
    
    for i in range(num_trainings):
        training_date = start_date + timedelta(days=random.randint(0, 730))
        trainings.append({
            "training_id": f"TRAIN{random.randint(1000, 9999)}",
            "course_name": random.choice(["Python Basics", "JavaScript Advanced", "Leadership Training", "Agile Methodology", "Project Management"]),
            "completed_date": training_date.strftime("%Y-%m-%d"),
            "status": random.choice(["completed", "in_progress", "certified"]),
            "hours": random.randint(8, 40)
        })
    
    return sorted(trainings, key=lambda x: x["completed_date"], reverse=True)


def generate_employee(index: int, department: str, include_pii: bool = True) -> Dict[str, Any]:
    """Generate a single employee record."""
    employee_id = generate_employee_id(index)
    skills = generate_skills(department)
    years_experience = random.randint(0, 20)
    role = random.choice(ROLES.get(department, ROLES["Engineering"]))
    
    employee = {
        "employee_id": employee_id,
        "department": department,
        "skills": ", ".join(skills),
        "years_experience": years_experience,
        "current_role": role,
        "hire_date": (datetime.now() - timedelta(days=years_experience * 365 + random.randint(0, 365))).strftime("%Y-%m-%d"),
    }
    
    if include_pii:
        name = random.choice(NAMES)
        employee["name"] = name
        employee["email"] = f"{name.split()[0].lower()}.{name.split()[1].lower()}@{random.choice(EMAIL_DOMAINS)}"
        employee["phone"] = f"+420 {random.randint(600, 799)} {random.randint(100, 999)} {random.randint(100, 999)}"
    
    # Add some missing values (10% chance)
    if random.random() < 0.1:
        employee["years_experience"] = None
    
    return employee


def generate_manufacturing_dataset(output_path: Path, num_employees: int = 50, include_pii: bool = True):
    """Generate manufacturing employee dataset."""
    employees = []
    
    for i in range(num_employees):
        dept = random.choice(["Manufacturing", "Engineering", "Quality Assurance", "Operations"])
        employee = generate_employee(i, dept, include_pii)
        employees.append(employee)
    
    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated manufacturing dataset: {output_path} ({num_employees} employees)")


def generate_ev_transformation_dataset(output_path: Path, num_employees: int = 75, include_pii: bool = True):
    """Generate EV transformation dataset."""
    employees = []
    ev_skills = ["EV Technology", "Battery Systems", "Charging Infrastructure", "Electric Motor Design", "Power Electronics"]
    
    for i in range(num_employees):
        dept = random.choice(["Engineering", "IT", "Operations"])
        employee = generate_employee(i, dept, include_pii)
        
        # Add EV-specific skills
        if random.random() < 0.3:  # 30% have EV skills
            ev_skill = random.choice(ev_skills)
            current_skills = employee["skills"].split(", ")
            current_skills.append(ev_skill)
            employee["skills"] = ", ".join(current_skills)
        
        employee["transformation_status"] = random.choice(["in_training", "ready", "needs_training"])
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated EV transformation dataset: {output_path} ({num_employees} employees)")


def generate_it_team_dataset(output_path: Path, num_employees: int = 30, include_pii: bool = True):
    """Generate IT team skills dataset."""
    employees = []
    
    for i in range(num_employees):
        employee = generate_employee(i, "IT", include_pii)
        employee["certifications"] = random.choice(["AWS Certified", "Azure Certified", "Cisco Certified", "None"])
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated IT team dataset: {output_path} ({num_employees} employees)")


def generate_leadership_training_dataset(output_path: Path, num_employees: int = 25, include_pii: bool = True):
    """Generate leadership training dataset."""
    employees = []
    leadership_skills = ["Leadership", "Team Management", "Strategic Planning", "Change Management", "Coaching"]
    
    for i in range(num_employees):
        dept = random.choice(DEPARTMENTS)
        employee = generate_employee(i, dept, include_pii)
        
        # All have some leadership skills
        leadership_skill = random.choice(leadership_skills)
        current_skills = employee["skills"].split(", ")
        current_skills.append(leadership_skill)
        employee["skills"] = ", ".join(current_skills)
        
        employee["leadership_level"] = random.choice(["junior", "mid", "senior", "executive"])
        employee["training_history"] = json.dumps(generate_training_history(employee["employee_id"]))
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated leadership training dataset: {output_path} ({num_employees} employees)")


def generate_global_mixed_dataset(output_path: Path, num_employees: int = 200, include_pii: bool = True):
    """Generate global mixed dataset."""
    employees = []
    
    for i in range(num_employees):
        dept = random.choice(DEPARTMENTS)
        employee = generate_employee(i, dept, include_pii)
        employee["location"] = random.choice(["Prague", "Brno", "Ostrava", "Plzeň", "Liberec"])
        employee["language"] = random.choice(["Czech", "English", "German", "Slovak"])
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated global mixed dataset: {output_path} ({num_employees} employees)")


def generate_messy_dataset_with_pii(output_path: Path, num_employees: int = 100, include_pii: bool = True):
    """Generate messy dataset with PII."""
    employees = []
    
    for i in range(num_employees):
        dept = random.choice(DEPARTMENTS)
        employee = generate_employee(i, dept, include_pii=True)  # Always include PII
        
        # Add inconsistent formatting
        if random.random() < 0.3:
            employee["skills"] = employee["skills"].upper()  # All caps
        elif random.random() < 0.3:
            employee["skills"] = employee["skills"].lower()  # All lowercase
        
        # Add missing values (20% chance)
        if random.random() < 0.2:
            employee["department"] = None
        if random.random() < 0.15:
            employee["skills"] = None
        
        # Add noisy columns
        employee["notes"] = random.choice(["", "Active", "On Leave", "Training", None])
        employee["last_updated"] = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d") if random.random() > 0.3 else None
        
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated messy dataset with PII: {output_path} ({num_employees} employees)")


def generate_unstructured_hr_dataset(output_path: Path, num_employees: int = 40, include_pii: bool = True):
    """Generate unstructured HR dataset."""
    employees = []
    
    for i in range(num_employees):
        dept = random.choice(DEPARTMENTS)
        employee = generate_employee(i, dept, include_pii=True)
        
        # Add unstructured fields
        employee["notes"] = f"Employee {i+1} notes: {random.choice(['Good performer', 'Needs improvement', 'Excellent', 'Average'])}"
        employee["performance_rating"] = random.choice(["Exceeds", "Meets", "Below", "N/A"])
        employee["salary_range"] = f"{random.randint(30000, 100000)} - {random.randint(50000, 150000)}"
        employee["education"] = random.choice(["Bachelor", "Master", "PhD", "High School", None])
        
        employees.append(employee)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=employees[0].keys())
        writer.writeheader()
        writer.writerows(employees)
    
    print(f"✓ Generated unstructured HR dataset: {output_path} ({num_employees} employees)")


def generate_json_dataset(output_path: Path, num_employees: int = 50):
    """Generate JSON format dataset."""
    employees = []
    
    for i in range(num_employees):
        dept = random.choice(DEPARTMENTS)
        employee = generate_employee(i, dept, include_pii=True)
        
        # Convert skills to array
        employee["skills"] = employee["skills"].split(", ")
        employee["training_history"] = generate_training_history(employee["employee_id"])
        
        employees.append(employee)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(employees, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Generated JSON dataset: {output_path} ({num_employees} employees)")


def main():
    """Generate all sample datasets."""
    print("Generating sample datasets for ŠKODA AI Skill Coach...\n")
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "sample_datasets"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate datasets
    generate_manufacturing_dataset(output_dir / "manufacturing_employees.csv", num_employees=50)
    generate_ev_transformation_dataset(output_dir / "ev_transformation_employees.csv", num_employees=75)
    generate_it_team_dataset(output_dir / "it_team_skills.csv", num_employees=30)
    generate_leadership_training_dataset(output_dir / "leadership_training.csv", num_employees=25)
    generate_global_mixed_dataset(output_dir / "global_mixed_employees.csv", num_employees=200)
    generate_messy_dataset_with_pii(output_dir / "messy_dataset_with_pii.csv", num_employees=100)
    generate_unstructured_hr_dataset(output_dir / "unstructured_hr_dataset.csv", num_employees=40)
    generate_json_dataset(output_dir / "employees.json", num_employees=50)
    
    print("\n✓ All sample datasets generated successfully!")
    print(f"\nDatasets saved to: {output_dir}")
    print("\nDataset Summary:")
    print("- manufacturing_employees.csv: 50 employees (Manufacturing, Engineering, QA, Operations)")
    print("- ev_transformation_employees.csv: 75 employees (EV transformation focus)")
    print("- it_team_skills.csv: 30 employees (IT team with certifications)")
    print("- leadership_training.csv: 25 employees (Leadership training focus)")
    print("- global_mixed_employees.csv: 200 employees (All departments, global locations)")
    print("- messy_dataset_with_pii.csv: 100 employees (Messy data with PII)")
    print("- unstructured_hr_dataset.csv: 40 employees (Unstructured HR data)")
    print("- employees.json: 50 employees (JSON format with nested data)")


if __name__ == "__main__":
    main()

