from data_models import DataLoader
import pandas as pd
import os

# Load data
data_folder = 'data'
excel_files = [f for f in os.listdir(data_folder) if f.endswith('.xlsx')]
dfs = []
for file in excel_files[:3]:  # Just first 3 files
    file_path = os.path.join(data_folder, file)
    df = pd.read_excel(file_path)
    dfs.append(df)

combined_df = pd.concat(dfs, ignore_index=True)

# Load employees
employees = DataLoader.load_employees_from_excel(combined_df)

# Check what skills employees actually have
print(f'Total employees: {len(employees)}')
print(f'\nFirst 5 employees and their skills:')
for emp in employees[:5]:
    print(f'\n{emp.name} ({emp.employee_id}):')
    print(f'  Position: {emp.current_position}')
    print(f'  Education: {emp.education_background}')
    skills_str = ', '.join([s.name for s in emp.current_skills]) if emp.current_skills else 'NO SKILLS'
    print(f'  Skills ({len(emp.current_skills)}): {skills_str}')
