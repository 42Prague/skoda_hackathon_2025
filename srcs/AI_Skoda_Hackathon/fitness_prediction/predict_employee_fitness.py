#!/usr/bin/env python3
"""
Employee Fitness Prediction System
Predicts employee fitness for target positions using Azure OpenAI
"""

import pandas as pd
import json
import sys
import os
import re
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from azure_openai_cli import azure_openai_cli

# Load environment variables from .env file
load_dotenv()

class EmployeeFitnessPredictor:
    def __init__(self, data_dir=None):
        # Default to ../data folder (outside fitness_prediction folder) if not specified
        # Data files are now stored in the project root's data/ folder, not in fitness_prediction/data/
        if data_dir is None:
            # Get the directory of this script (fitness_prediction/), 
            # then go up one level to project root, then into data folder
            script_dir = Path(__file__).parent
            data_dir = script_dir.parent / "data"
        self.data_dir = Path(data_dir)
        # Verify data directory exists
        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}. Please ensure the data folder exists in the project root.")
        self.employees = None
        self.positions = None
        self.qualifications = None
        self.courses = None
        self.skills_mapping = None
        self.competencies = None
        self.course_participation = None
        
    def load_data(self):
        """Load all CSV data files"""
        print("📂 Loading data files...")
        
        try:
            # Employee master data
            self.employees = pd.read_csv(
                self.data_dir / "ERP_SK1.Start_month - SE.csv"
            )
            print(f"  ✓ Loaded {len(self.employees)} employees")
            
            # Position assignments
            self.positions = pd.read_csv(
                self.data_dir / "250828_Export_AI_Skill_Coatch_RE_RHRHAZ00_S_T.csv",
                encoding='utf-8-sig',  # Handle BOM
                on_bad_lines='skip',
                low_memory=False
            )
            print(f"  ✓ Loaded {len(self.positions)} position assignments")
            
            # Qualifications
            self.qualifications = pd.read_csv(
                self.data_dir / "ZHRPD_VZD_STA_016_RE_RHRHAZ00.csv"
            )
            print(f"  ✓ Loaded {len(self.qualifications)} qualifications")
            
            # Course participation
            self.course_participation = pd.read_csv(
                self.data_dir / "ZHRPD_VZD_STA_007.csv"
            )
            print(f"  ✓ Loaded {len(self.course_participation)} course participations")
            
            # Skills mapping
            self.skills_mapping = pd.read_csv(
                self.data_dir / "Skill_mapping.csv"
            )
            print(f"  ✓ Loaded {len(self.skills_mapping)} skill mappings")
            
            # Competencies (position requirements)
            self.competencies = pd.read_csv(
                self.data_dir / "ZPE_KOM_KVAL.csv"
            )
            print(f"  ✓ Loaded {len(self.competencies)} competencies")
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            raise
    
    def get_employee_profile(self, personal_number):
        """Build comprehensive employee profile"""
        # Convert personal_number to int for matching
        try:
            personal_num_int = int(personal_number)
        except (ValueError, TypeError):
            return None
        
        # Filter employee data
        emp_data = self.employees[
            self.employees['persstat_start_month.personal_number'] == personal_num_int
        ]
        
        if emp_data.empty:
            return None
        
        emp = emp_data.iloc[0]
        
        # Get current position - VarPole contains task IDs, not personal numbers
        # We'll use the planned_position from employee data instead
        # If needed, we can match via other fields later
        current_positions = pd.DataFrame()  # Placeholder for now
        
        # Get qualifications - ID P might be different format, try matching
        # Note: ID P might not directly match personal_number format
        emp_qualifications = self.qualifications[
            self.qualifications['ID P'] == personal_num_int
        ]
        
        # Get course participations - use ID účastníka field
        emp_courses = self.course_participation[
            self.course_participation['ID účastníka'] == personal_num_int
        ]
        
        # Map courses to skills
        if not emp_courses.empty:
            course_ids = emp_courses['Typ akce'].dropna().unique()
            # Convert to same type for matching
            course_ids = [int(x) for x in course_ids if pd.notna(x)]
            skills_from_courses = self.skills_mapping[
                self.skills_mapping['ID Kurzu'].isin(course_ids)
            ]['Kompetence / Skill'].dropna().unique().tolist()
        else:
            skills_from_courses = []
        
        # Build profile
        profile = {
            'personal_number': str(personal_num_int),
            'current_profession': emp.get('persstat_start_month.profession', 'N/A'),
            'planned_profession': emp.get('persstat_start_month.planned_profession', 'N/A'),
            'planned_position': emp.get('persstat_start_month.planned_position', 'N/A'),
            'education_branch': emp.get('persstat_start_month.basic_branch_of_education_name', 'N/A'),
            'education_category': emp.get('persstat_start_month.education_category_name', 'N/A'),
            'field_of_study': emp.get('persstat_start_month.field_of_study_name', 'N/A'),
            'qualifications': emp_qualifications['Název Q'].dropna().unique().tolist() if not emp_qualifications.empty else [],
            'courses_completed': emp_courses['Označení typu akce'].dropna().unique().tolist() if not emp_courses.empty else [],
            'skills_from_courses': skills_from_courses,
            'num_qualifications': len(emp_qualifications),
            'num_courses': len(emp_courses)
        }
        
        return profile
    
    def get_position_requirements(self, position_id):
        """Get required competencies/skills for a position"""
        position_comp = self.competencies[
            self.competencies['Číslo FM'] == position_id
        ]
        
        if position_comp.empty:
            return []
        
        return position_comp['Kvalifikace'].dropna().unique().tolist()
    
    def format_profile_for_ai(self, profile, target_position=None, position_requirements=None):
        """Format employee profile as text for AI analysis"""
        text = f"""EMPLOYEE PROFILE
================
Personal Number: {profile['personal_number']}
Current Profession: {profile['current_profession']}
Planned Profession: {profile['planned_profession']}
Planned Position: {profile['planned_position']}

EDUCATION
---------
Branch: {profile['education_branch']}
Category: {profile['education_category']}
Field of Study: {profile['field_of_study']}

QUALIFICATIONS ({profile['num_qualifications']} total)
---------------
{chr(10).join(f"  • {q}" for q in profile['qualifications'][:20])}
{"  ... (showing first 20)" if len(profile['qualifications']) > 20 else ""}

COURSES COMPLETED ({profile['num_courses']} total)
------------------
{chr(10).join(f"  • {c}" for c in profile['courses_completed'][:20])}
{"  ... (showing first 20)" if len(profile['courses_completed']) > 20 else ""}

SKILLS FROM COURSES
-------------------
{chr(10).join(f"  • {s}" for s in profile['skills_from_courses'][:20]) if profile['skills_from_courses'] else "  None"}
"""
        
        if target_position:
            text += f"""
TARGET POSITION
---------------
Position ID: {target_position}
"""
        
        if position_requirements:
            text += f"""
POSITION REQUIREMENTS
---------------------
{chr(10).join(f"  • {r}" for r in position_requirements[:20])}
{"  ... (showing first 20)" if len(position_requirements) > 20 else ""}
"""
        
        return text
    
    def predict_fitness(self, personal_number, target_position_id=None, 
                       custom_position_description=None,
                       api_url=None, api_key=None, api_version=None, deployment_name=None):
        """Predict employee fitness for target position using Azure OpenAI"""
        
        # Get employee profile
        profile = self.get_employee_profile(personal_number)
        if not profile:
            return {"error": f"Employee {personal_number} not found"}
        
        # Get position requirements if target position specified
        position_requirements = None
        if target_position_id:
            position_requirements = self.get_position_requirements(target_position_id)
        elif custom_position_description:
            position_requirements = [custom_position_description]  # Use custom description
        
        # Format profile for AI
        profile_text = self.format_profile_for_ai(profile, target_position_id, position_requirements)
        
        # Create AI prompt
        if (target_position_id or custom_position_description) and position_requirements:
            # Add custom position description if provided
            position_section = ""
            if custom_position_description:
                position_section = f"""
TARGET POSITION DESCRIPTION
----------------------------
{custom_position_description}
"""
            
            user_message = f"""Analyze the following employee profile and assess their fitness for the target position.

{profile_text}
{position_section}

Please provide:
1. Fitness Score (0-100): Overall match between employee profile and position requirements
2. Strengths: What makes this employee a good fit
3. Gaps: Missing skills, qualifications, or experience
4. Recommendations: Specific courses, training, or qualifications to bridge gaps
5. Risk Assessment: Any concerns or red flags

Format your response as:
FITNESS SCORE: [0-100]
STRENGTHS: [list]
GAPS: [list]
RECOMMENDATIONS: [list]
RISK ASSESSMENT: [text]
"""
        else:
            user_message = f"""Analyze the following employee profile and provide insights about their career development potential.

{profile_text}

Please provide:
1. Career Profile Summary: Overview of employee's background
2. Key Strengths: Notable skills, qualifications, and experience
3. Career Trajectory: Analysis of current vs planned position
4. Development Recommendations: Suggested areas for growth
5. Potential Positions: Types of positions this employee might be suited for

Format your response clearly with sections.
"""
        
        system_message = """You are a career development expert for Škoda Auto specializing in employee-position matching and career development. 
You analyze employee profiles considering their education, qualifications, completed courses, skills, and experience.
Provide practical, actionable insights based on the data provided."""
        
        # Call Azure OpenAI
        if not all([api_url, api_key, api_version, deployment_name]):
            return {
                "error": "Azure OpenAI credentials not provided",
                "profile": profile,
                "profile_text": profile_text
            }
        
        print(f"\n🤖 Calling Azure OpenAI for employee {personal_number}...")
        print("=" * 60)
        
        # Call the API and get response
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        params = {
            "api-version": api_version
        }
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": user_message})
        
        data = {
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                f"{api_url}/openai/deployments/{deployment_name}/chat/completions",
                headers=headers,
                params=params,
                json=data,
                timeout=30
            )
            
            fitness_score = None
            ai_response = ""
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    ai_response = result["choices"][0]["message"]["content"]
                    print("✅ Response from Azure OpenAI:")
                    print("-" * 60)
                    print(ai_response)
                    print("-" * 60)
                    
                    # Parse fitness score from response
                    score_match = re.search(r'FITNESS SCORE:\s*(\d+)', ai_response, re.IGNORECASE)
                    if score_match:
                        fitness_score = int(score_match.group(1))
                        print(f"\n📊 Extracted Fitness Score: {fitness_score}")
                    else:
                        # Try alternative patterns
                        score_match = re.search(r'Fitness Score[:\s]+(\d+)', ai_response, re.IGNORECASE)
                        if score_match:
                            fitness_score = int(score_match.group(1))
                        else:
                            # Try to find any number between 0-100
                            score_match = re.search(r'\b([0-9]|[1-9][0-9]|100)\b', ai_response)
                            if score_match:
                                potential_score = int(score_match.group(1))
                                if 0 <= potential_score <= 100:
                                    fitness_score = potential_score
                else:
                    print("⚠️  No response content in result")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error calling API: {e}")
        
        return {
            "personal_number": personal_number,
            "profile": profile,
            "target_position_id": target_position_id,
            "position_requirements": position_requirements,
            "fitness_score": fitness_score,
            "ai_response": ai_response
        }
    
    def list_employees(self, limit=10):
        """List available employees"""
        if self.employees is None:
            self.load_data()
        
        return self.employees[['persstat_start_month.personal_number', 
                              'persstat_start_month.profession',
                              'persstat_start_month.planned_position']].head(limit)
    
    def list_positions(self, limit=10):
        """List available positions with requirements"""
        if self.competencies is None:
            self.load_data()
        
        return self.competencies.groupby('Číslo FM').first().head(limit)


def main():
    """Main function"""
    # Use data folder from project root (outside fitness_prediction folder)
    # Data files are stored in: project_root/data/ (not fitness_prediction/data/)
    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    predictor = EmployeeFitnessPredictor(data_dir=str(data_dir))
    
    # Handle list commands
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        predictor.load_data()
        if sys.argv[2] == "employees":
            print("\n📋 Available Employees (first 20):")
            print(predictor.list_employees(20))
        elif sys.argv[2] == "positions":
            print("\n📋 Available Positions (first 20):")
            print(predictor.list_positions(20))
        return
    
    # Get credentials from environment variables or command line arguments
    api_url = os.getenv('AZURE_OPENAI_API_URL')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION')
    deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    
    # Parse arguments
    custom_position_description = None
    target_position_id = None
    
    # Check for --position-desc or --position-file flags
    if '--position-desc' in sys.argv:
        idx = sys.argv.index('--position-desc')
        if idx + 1 < len(sys.argv):
            custom_position_description = sys.argv[idx + 1]
            # Remove the flag and value from sys.argv for backward compatibility
            sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
    elif '--position-file' in sys.argv:
        idx = sys.argv.index('--position-file')
        if idx + 1 < len(sys.argv):
            position_file = sys.argv[idx + 1]
            try:
                with open(position_file, 'r', encoding='utf-8') as f:
                    custom_position_description = f.read().strip()
            except Exception as e:
                print(f"❌ Error reading position file: {e}")
                sys.exit(1)
            # Remove the flag and value from sys.argv
            sys.argv = sys.argv[:idx] + sys.argv[idx+2:]
    
    # Check if first argument looks like a URL (explicit credentials mode)
    if len(sys.argv) >= 5 and sys.argv[1].startswith('http'):
        # Explicit credentials mode: <api_url> <api_key> <api_version> <deployment> <employee_id> [position_id]
        api_url = sys.argv[1]
        api_key = sys.argv[2]
        api_version = sys.argv[3]
        deployment_name = sys.argv[4]
        personal_number = sys.argv[5] if len(sys.argv) > 5 else None
        if len(sys.argv) > 6 and not custom_position_description:
            try:
                target_position_id = int(sys.argv[6])
            except ValueError:
                # If not a number, treat as custom description
                custom_position_description = sys.argv[6]
    elif len(sys.argv) >= 2:
        # Environment variable mode: <employee_id> [position_id or position_description]
        personal_number = sys.argv[1]
        if len(sys.argv) > 2 and not custom_position_description:
            try:
                target_position_id = int(sys.argv[2])
            except ValueError:
                # If not a number, treat as custom description
                custom_position_description = sys.argv[2]
    else:
        # Show usage
        if not all([api_url, api_key, api_version, deployment_name]):
            print("Usage: python predict_employee_fitness.py <personal_number> [target_position_id]")
            print("   or: python predict_employee_fitness.py <personal_number> --position-desc \"<description>\"")
            print("   or: python predict_employee_fitness.py <personal_number> --position-file <file_path>")
            print("\nOr with explicit credentials:")
            print("  python predict_employee_fitness.py <api_url> <api_key> <api_version> <deployment_name> <personal_number> [target_position_id]")
            print("\nEnvironment variables (from .env file):")
            print("  AZURE_OPENAI_API_URL")
            print("  AZURE_OPENAI_API_KEY")
            print("  AZURE_OPENAI_API_VERSION")
            print("  AZURE_OPENAI_DEPLOYMENT")
            print("\nTo list available employees:")
            print("  python predict_employee_fitness.py list employees")
            print("\nTo list available positions:")
            print("  python predict_employee_fitness.py list positions")
            sys.exit(1)
        else:
            print("Usage: python predict_employee_fitness.py <personal_number> [target_position_id]")
            print("   or: python predict_employee_fitness.py <personal_number> --position-desc \"<description>\"")
            print("   or: python predict_employee_fitness.py <personal_number> --position-file <file_path>")
            print("\nExample:")
            print("  python predict_employee_fitness.py 4241")
            print("  python predict_employee_fitness.py 4241 20002503")
            print("  python predict_employee_fitness.py 4241 --position-desc \"IT Specialist role...\"")
            sys.exit(1)
    
    if not all([api_url, api_key, api_version, deployment_name]):
        print("❌ Error: Missing Azure OpenAI credentials")
        print("   Please set environment variables in .env file or provide as arguments")
        sys.exit(1)
    
    if not personal_number:
        print("❌ Error: Employee personal number required")
        sys.exit(1)
    
    # Load data
    predictor.load_data()
    
    # Make prediction
    result = predictor.predict_fitness(
        personal_number,
        target_position_id,
        custom_position_description=custom_position_description,
        api_url=api_url,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment_name
    )
    
    if "error" in result:
        print(f"\n❌ Error: {result['error']}")
        if "profile_text" in result:
            print("\n📄 Employee Profile (for reference):")
            print(result['profile_text'])


if __name__ == "__main__":
    main()

