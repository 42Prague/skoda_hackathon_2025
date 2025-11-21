"""
Data models for the Skill Gap Analysis AI System
"""
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional
from datetime import datetime


@dataclass
class Skill:
    """Represents a skill with metadata"""
    skill_id: str
    name: str
    category: str = "General"
    level_required: int = 1  # 1-5 proficiency level
    
    def __hash__(self):
        return hash(self.skill_id)
    
    def __eq__(self, other):
        if isinstance(other, Skill):
            return self.skill_id == other.skill_id
        return False


@dataclass
class Course:
    """Represents a training course"""
    course_id: str
    title: str
    provider: str
    duration_minutes: int
    skills_taught: List[Skill] = field(default_factory=list)
    description: str = ""
    url: str = ""
    competencies: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.course_id)


@dataclass
class Employee:
    """Represents an employee with their skills and learning history"""
    employee_id: str
    name: str
    current_position: str
    current_skills: List[Skill] = field(default_factory=list)
    completed_courses: List[Course] = field(default_factory=list)
    planned_position: Optional[str] = None
    department: str = ""
    education_background: str = ""
    
    def get_skill_names(self) -> Set[str]:
        """Get set of skill names the employee has"""
        return {skill.name for skill in self.current_skills}
    
    def get_total_learning_hours(self) -> float:
        """Calculate total learning hours completed"""
        total_minutes = sum(course.duration_minutes for course in self.completed_courses)
        return total_minutes / 60.0


@dataclass
class Position:
    """Represents a job position with required skills"""
    position_id: str
    title: str
    required_skills: List[Skill] = field(default_factory=list)
    optional_skills: List[Skill] = field(default_factory=list)
    description: str = ""
    
    def get_required_skill_names(self) -> Set[str]:
        """Get set of required skill names"""
        return {skill.name for skill in self.required_skills}
    
    def get_all_skill_names(self) -> Set[str]:
        """Get all skills (required + optional)"""
        return self.get_required_skill_names() | {skill.name for skill in self.optional_skills}


@dataclass
class SkillGap:
    """Represents a skill gap analysis result"""
    employee: Employee
    target_position: Position
    missing_required_skills: List[Skill]
    missing_optional_skills: List[Skill]
    matched_skills: List[Skill]
    gap_percentage: float  # 0-100
    readiness_score: float  # 0-100
    
    def get_priority_skills(self) -> List[Skill]:
        """Get skills to prioritize (missing required skills first)"""
        return self.missing_required_skills + self.missing_optional_skills


class DataLoader:
    """Load and preprocess data from Excel files"""
    
    @staticmethod
    def load_employees_from_excel(df: pd.DataFrame) -> List[Employee]:
        """
        Load employees from the persstat_start_month data
        Expected columns: personal_number, user_name, profession, planned_position, etc.
        """
        employees = []
        
        # Group by employee to consolidate their data
        employee_groups = df.groupby('persstat_start_month.personal_number')
        
        for emp_id, group in employee_groups:
            if pd.isna(emp_id):
                continue
                
            # Get first row for basic info
            row = group.iloc[0]
            
            # Extract skills from profession, planned position, and education
            skills = []
            skill_set = set()
            
            # Add current profession as a skill
            if pd.notna(row.get('persstat_start_month.profession')):
                profession = str(row.get('persstat_start_month.profession'))
                if profession and profession not in skill_set:
                    skills.append(Skill(
                        skill_id=f"skill_prof_{len(skills)}",
                        name=profession,
                        category="Professional"
                    ))
                    skill_set.add(profession)
            
            # Add education as skills
            if pd.notna(row.get('persstat_start_month.basic_branch_of_education_grou2')):
                education = str(row.get('persstat_start_month.basic_branch_of_education_grou2'))
                if education and education not in skill_set:
                    skills.append(Skill(
                        skill_id=f"skill_edu_{len(skills)}",
                        name=education,
                        category="Education"
                    ))
                    skill_set.add(education)
            
            # Add field of study as skill
            if pd.notna(row.get('persstat_start_month.field_of_study_name')):
                field_of_study = str(row.get('persstat_start_month.field_of_study_name'))
                if field_of_study and field_of_study not in skill_set:
                    skills.append(Skill(
                        skill_id=f"skill_fos_{len(skills)}",
                        name=field_of_study,
                        category="Education"
                    ))
                    skill_set.add(field_of_study)
            
            employee = Employee(
                employee_id=str(int(emp_id)),
                name=str(row.get('persstat_start_month.user_name', f'Employee_{emp_id}')),
                current_position=str(row.get('persstat_start_month.profession', 'Unknown')),
                planned_position=str(row.get('persstat_start_month.planned_position', None)) if pd.notna(row.get('persstat_start_month.planned_position')) else None,
                department=str(row.get('Oddělení', '')) if 'Oddělení' in row and pd.notna(row.get('Oddělení')) else '',
                education_background=str(row.get('persstat_start_month.basic_branch_of_education_grou2', '')) if pd.notna(row.get('persstat_start_month.basic_branch_of_education_grou2')) else '',
                current_skills=skills
            )
            
            employees.append(employee)
        
        return employees
    
    @staticmethod
    def load_courses_from_excel(df: pd.DataFrame) -> List[Course]:
        """
        Load courses from the data
        Expected columns: ID Kurzu, Název D, Téma, Kompetence / Skill, etc.
        """
        courses = []
        
        # Filter rows with course data
        course_data = df[df['ID Kurzu'].notna()].copy()
        
        if len(course_data) == 0:
            return courses
        
        # Group by course ID to consolidate
        course_groups = course_data.groupby('ID Kurzu')
        
        for course_id, group in course_groups:
            row = group.iloc[0]
            
            # Extract skills/competencies
            competencies = []
            if 'Kompetence / Skill' in row and pd.notna(row['Kompetence / Skill']):
                comp_str = str(row['Kompetence / Skill'])
                competencies = [c.strip() for c in comp_str.split(',') if c.strip()]
            
            # Calculate duration
            duration = 0
            if 'Verified Learning Minutes' in row and pd.notna(row['Verified Learning Minutes']):
                duration = int(row['Verified Learning Minutes'])
            elif 'Estimated Learning Minutes' in row and pd.notna(row['Estimated Learning Minutes']):
                duration = int(row['Estimated Learning Minutes'])
            
            course = Course(
                course_id=str(course_id),
                title=str(row.get('Název D', row.get('Content Title', f'Course_{course_id}'))),
                provider=str(row.get('Content Provider', 'Internal')),
                duration_minutes=duration,
                competencies=competencies,
                url=str(row.get('Content URL', '')) if pd.notna(row.get('Content URL')) else ''
            )
            
            courses.append(course)
        
        return courses
    
    @staticmethod
    def extract_skills_from_data(df: pd.DataFrame) -> List[Skill]:
        """
        Extract unique skills from the dataset
        """
        skills = set()
        
        # Extract from Kompetence / Skill column
        if 'Kompetence / Skill' in df.columns:
            comp_data = df['Kompetence / Skill'].dropna()
            for comp_str in comp_data:
                if pd.notna(comp_str):
                    comps = [c.strip() for c in str(comp_str).split(',') if c.strip()]
                    skills.update(comps)
        
        # Extract from profession if it contains skill info
        if 'persstat_start_month.profession' in df.columns:
            professions = df['persstat_start_month.profession'].dropna().unique()
            for prof in professions:
                if pd.notna(prof):
                    skills.add(str(prof))
        
        # Convert to Skill objects
        skill_objects = []
        for i, skill_name in enumerate(sorted(skills)):
            if skill_name and skill_name.lower() not in ['nan', 'none', '']:
                skill_objects.append(Skill(
                    skill_id=f"skill_{i:04d}",
                    name=skill_name,
                    category="Technical" if any(tech in skill_name.lower() for tech in ['it', 'programming', 'software', 'data']) else "General"
                ))
        
        return skill_objects
    
    @staticmethod
    def create_position_requirements() -> Dict[str, Position]:
        """
        Create position requirements based on common roles
        This should be customized based on your organization's needs
        """
        positions = {}
        
        # Generic positions that will match broader skill categories
        positions['specialist'] = Position(
            position_id='pos_001',
            title='Specialist',
            required_skills=[
                Skill('sk_001', 'Professional', 'Professional', 2),
                Skill('sk_002', 'Education', 'Education', 2),
            ],
            optional_skills=[
                Skill('sk_003', 'Technical', 'Technical', 1),
                Skill('sk_004', 'Management', 'Management', 1),
            ]
        )
        
        positions['senior_specialist'] = Position(
            position_id='pos_002',
            title='Senior Specialist',
            required_skills=[
                Skill('sk_005', 'Professional', 'Professional', 3),
                Skill('sk_006', 'Education', 'Education', 3),
                Skill('sk_007', 'Technical', 'Technical', 2),
            ],
            optional_skills=[
                Skill('sk_008', 'Management', 'Management', 2),
                Skill('sk_009', 'Leadership', 'Leadership', 2),
            ]
        )
        
        positions['manager'] = Position(
            position_id='pos_003',
            title='Manager',
            required_skills=[
                Skill('sk_010', 'Management', 'Management', 3),
                Skill('sk_011', 'Leadership', 'Leadership', 3),
                Skill('sk_012', 'Professional', 'Professional', 2),
            ],
            optional_skills=[
                Skill('sk_013', 'Technical', 'Technical', 2),
                Skill('sk_014', 'Strategic Planning', 'Strategic', 2),
            ]
        )
        
        return positions
