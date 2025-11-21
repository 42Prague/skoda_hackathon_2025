"""
Skill Service
Advanced business logic for skill analysis and recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from services.employee_service import EmployeeService
from models.employee import Employee
import math
from data.data_accesser import DataAccesser
from .skill_analyzer import SkillAnalyzer
from data.data_accesser import g_data_accesser

class SkillService:
    """
    Service class for advanced skill analysis and recommendations
    Contains sophisticated business logic for skill-related operations
    """

    def __init__(self):
        """Initialize with employee service"""
        self.employee_service = EmployeeService()
        self.data_accesser = DataAccesser()
        self.skill_analyzer = SkillAnalyzer()

    def get_employee_diagram(self, employee_id: int) -> Optional[Dict[str, float]]:
        """
        Get skill diagram data for an employee
        
        Args:
            employee_id: ID of the employee
        """
        employee = g_data_accesser.get_employee_data(employee_id)
        if not employee:
            return None
    
        # Example diagram data (could be expanded)
        # diagram_data = {
        #     "breadth": self.skill_analyzer.get_breadth(employee),
        #     "depth": self.skill_analyzer.get_skill_depth(employee),
        #     "learning_intensity": self.skill_analyzer.get_learning_intensity(employee),
        #     "qualification_strength": self.skill_analyzer.get_qualification_strength(employee),
        #     "job_requirement_coverage": self.skill_analyzer.get_job_requirement_coverage(employee),
        #     "skill_gap_index": self.skill_analyzer.get_skill_gap_index(employee),
        #     "recent_learning_index": self.skill_analyzer.get_recent_learning_index(employee),
        # }
        
        diagram_data = {
            "breadth": self.skill_analyzer.get_breadth(employee),
            "depth": self.skill_analyzer.get_skill_depth(employee),
            "learning_intensity": self.skill_analyzer.get_learning_intensity(employee),
            "qualification_strength": self.skill_analyzer.get_qualification_strength(employee),
            "job_requirement_coverage": self.skill_analyzer.get_job_requirement_coverage(employee),
            "skill_gap_index": self.skill_analyzer.get_skill_gap_index(employee),
            "recent_learning_index": self.skill_analyzer.get_recent_learning_index(employee),
        }
        
        return diagram_data
