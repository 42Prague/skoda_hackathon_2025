"""
Employee Model
Simple class to represent an employee with their skills and information.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
import json

@dataclass
class Employee:
    """
    Employee class to store employee information
    
    Attributes:
        name: Employee's full name
        position: Job position/title
        skills: List of skills (strings)
        experience_years: Years of experience
        department: Department name
        employee_id: Unique identifier (auto-generated)
    """
    name: str
    position: str
    skills: List[str]
    experience_years: int = 0
    department: str = "Unknown"
    employee_id: int = None
    
    def __post_init__(self):
        """Initialize after creation"""
        # Convert skills to lowercase for consistency
        self.skills = [skill.lower().strip() for skill in self.skills]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert employee to dictionary format"""
        return {
            "employee_id": self.employee_id,
            "name": self.name,
            "position": self.position,
            "skills": self.skills,
            "experience_years": self.experience_years,
            "department": self.department,
            "skills_count": len(self.skills)
        }
    
    def has_skill(self, skill: str) -> bool:
        """Check if employee has a specific skill"""
        return skill.lower().strip() in self.skills
    
    def add_skill(self, skill: str) -> None:
        """Add a new skill to employee"""
        skill_clean = skill.lower().strip()
        if skill_clean not in self.skills:
            self.skills.append(skill_clean)
    
    def remove_skill(self, skill: str) -> bool:
        """Remove a skill from employee. Returns True if removed, False if not found"""
        skill_clean = skill.lower().strip()
        if skill_clean in self.skills:
            self.skills.remove(skill_clean)
            return True
        return False
    
    def get_skill_level(self, skill: str) -> str:
        """
        Get skill level based on experience (simple logic for now)
        You can enhance this later with more sophisticated analysis
        """
        if not self.has_skill(skill):
            return "Not Available"
        
        if self.experience_years < 2:
            return "Beginner"
        elif self.experience_years < 5:
            return "Intermediate"
        else:
            return "Advanced"
    
    def __str__(self) -> str:
        """String representation of employee"""
        return f"Employee(id={self.employee_id}, name='{self.name}', position='{self.position}', skills={len(self.skills)})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return self.__str__()

# Example usage and sample data
def create_sample_employees() -> List[Employee]:
    """Create some sample employees for testing"""
    return [
        Employee(
            name="John Doe",
            position="Software Developer",
            skills=["Python", "JavaScript", "SQL", "Git"],
            experience_years=3,
            department="IT"
        ),
        Employee(
            name="Jane Smith",
            position="Data Analyst",
            skills=["Python", "R", "Excel", "Tableau", "SQL"],
            experience_years=5,
            department="Analytics"
        ),
        Employee(
            name="Mike Johnson",
            position="Frontend Developer",
            skills=["JavaScript", "React", "CSS", "HTML", "TypeScript"],
            experience_years=2,
            department="IT"
        ),
        Employee(
            name="Sarah Wilson",
            position="Project Manager",
            skills=["Project Management", "Scrum", "Leadership", "Communication"],
            experience_years=7,
            department="Management"
        )
    ]
