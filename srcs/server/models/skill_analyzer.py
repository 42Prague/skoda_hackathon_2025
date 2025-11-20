"""
Skill Analyzer
This class handles all the logic for analyzing employee skills and making suggestions.
"""

from typing import List, Dict, Any, Optional
from .employee import Employee, create_sample_employees
import json
from collections import Counter

class SkillAnalyzer:
    """
    Main class for analyzing employee skills and providing suggestions
    """
    
    def __init__(self):
        """Initialize the analyzer with sample data"""
        self.employees: List[Employee] = []
        self.next_id = 1
        
        # Load sample employees
        self._load_sample_data()
    
    def _load_sample_data(self):
        """Load sample employee data for testing"""
        sample_employees = create_sample_employees()
        for employee in sample_employees:
            self.add_employee(employee)
    
    def add_employee(self, employee: Employee) -> Dict[str, Any]:
        """Add a new employee to the system"""
        employee.employee_id = self.next_id
        self.next_id += 1
        self.employees.append(employee)
        return employee.to_dict()
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """Get all employees as dictionaries"""
        return [emp.to_dict() for emp in self.employees]
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get employee by ID"""
        for employee in self.employees:
            if employee.employee_id == employee_id:
                return employee.to_dict()
        return None
    
    def get_employee_object_by_id(self, employee_id: int) -> Optional[Employee]:
        """Get employee object by ID (for internal use)"""
        for employee in self.employees:
            if employee.employee_id == employee_id:
                return employee
        return None
    
    def get_skill_suggestions(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Get skill suggestions for a specific employee
        Based on what other employees in similar positions have
        """
        employee = self.get_employee_object_by_id(employee_id)
        if not employee:
            return None
        
        # Find employees in similar positions or departments
        similar_employees = self._find_similar_employees(employee)
        
        # Get skills that similar employees have but this employee doesn't
        suggested_skills = self._get_missing_skills(employee, similar_employees)
        
        # Get trending skills across the organization
        trending_skills = self._get_trending_skills()
        
        # Get skills for career advancement
        advancement_skills = self._get_advancement_skills(employee)
        
        return {
            "employee": employee.to_dict(),
            "suggestions": {
                "based_on_similar_roles": suggested_skills[:5],  # Top 5
                "trending_in_company": trending_skills[:3],      # Top 3
                "career_advancement": advancement_skills[:4],    # Top 4
                "explanation": {
                    "similar_roles": f"Skills commonly found in similar positions to {employee.position}",
                    "trending": "Skills that are becoming popular across the company",
                    "advancement": "Skills that could help with career growth"
                }
            }
        }
    
    def _find_similar_employees(self, target_employee: Employee) -> List[Employee]:
        """Find employees with similar positions or departments"""
        similar = []
        
        for employee in self.employees:
            if employee.employee_id == target_employee.employee_id:
                continue
            
            # Same department gets higher priority
            if employee.department.lower() == target_employee.department.lower():
                similar.append(employee)
            # Similar position titles
            elif any(word in employee.position.lower() 
                    for word in target_employee.position.lower().split()):
                similar.append(employee)
        
        return similar
    
    def _get_missing_skills(self, employee: Employee, similar_employees: List[Employee]) -> List[str]:
        """Get skills that similar employees have but target employee doesn't"""
        # Collect all skills from similar employees
        all_similar_skills = []
        for similar_emp in similar_employees:
            all_similar_skills.extend(similar_emp.skills)
        
        # Count frequency of skills
        skill_counts = Counter(all_similar_skills)
        
        # Find skills that target employee doesn't have
        missing_skills = []
        for skill, count in skill_counts.most_common():
            if not employee.has_skill(skill) and count > 1:  # Skill appears in multiple people
                missing_skills.append(skill)
        
        return missing_skills
    
    def _get_trending_skills(self) -> List[str]:
        """Get skills that are trending across the organization"""
        all_skills = []
        for employee in self.employees:
            all_skills.extend(employee.skills)
        
        skill_counts = Counter(all_skills)
        # Return most common skills as "trending"
        return [skill for skill, count in skill_counts.most_common(10)]
    
    def _get_advancement_skills(self, employee: Employee) -> List[str]:
        """Get skills that could help with career advancement"""
        # Simple logic: look at skills of people with more experience
        advanced_skills = []
        
        for other_employee in self.employees:
            if (other_employee.experience_years > employee.experience_years and 
                other_employee.department == employee.department):
                advanced_skills.extend(other_employee.skills)
        
        # Remove duplicates and skills already possessed
        unique_advanced = list(set(advanced_skills))
        return [skill for skill in unique_advanced if not employee.has_skill(skill)]
    
    def analyze_skills_gap(self, department: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze skills gap across the organization or specific department
        """
        # Filter employees by department if specified
        if department:
            target_employees = [emp for emp in self.employees 
                              if emp.department.lower() == department.lower()]
            analysis_scope = f"Department: {department}"
        else:
            target_employees = self.employees
            analysis_scope = "Entire Organization"
        
        if not target_employees:
            return {
                "scope": analysis_scope,
                "error": "No employees found in specified scope"
            }
        
        # Count all skills
        all_skills = []
        for employee in target_employees:
            all_skills.extend(employee.skills)
        
        skill_counts = Counter(all_skills)
        total_employees = len(target_employees)
        
        # Calculate skill coverage
        skill_analysis = []
        for skill, count in skill_counts.most_common():
            percentage = (count / total_employees) * 100
            skill_analysis.append({
                "skill": skill,
                "employee_count": count,
                "coverage_percentage": round(percentage, 1),
                "gap_level": self._determine_gap_level(percentage)
            })
        
        # Find departments and their skill distribution
        dept_analysis = {}
        if not department:  # Only if analyzing entire organization
            for employee in target_employees:
                dept = employee.department
                if dept not in dept_analysis:
                    dept_analysis[dept] = {"employees": 0, "skills": []}
                dept_analysis[dept]["employees"] += 1
                dept_analysis[dept]["skills"].extend(employee.skills)
        
        return {
            "scope": analysis_scope,
            "total_employees": total_employees,
            "total_unique_skills": len(skill_counts),
            "skill_analysis": skill_analysis,
            "department_breakdown": dept_analysis if dept_analysis else None,
            "recommendations": self._generate_recommendations(skill_analysis)
        }
    
    def _determine_gap_level(self, coverage_percentage: float) -> str:
        """Determine the gap level based on coverage percentage"""
        if coverage_percentage >= 70:
            return "Low Gap"
        elif coverage_percentage >= 40:
            return "Medium Gap"
        else:
            return "High Gap"
    
    def _generate_recommendations(self, skill_analysis: List[Dict]) -> List[str]:
        """Generate recommendations based on skill analysis"""
        recommendations = []
        
        # Find skills with high gaps
        high_gap_skills = [s for s in skill_analysis if s["gap_level"] == "High Gap"]
        if high_gap_skills:
            recommendations.append(
                f"Consider training programs for: {', '.join([s['skill'] for s in high_gap_skills[:3]])}"
            )
        
        # Find skills with good coverage
        well_covered = [s for s in skill_analysis if s["gap_level"] == "Low Gap"]
        if well_covered:
            recommendations.append(
                f"Leverage expertise in: {', '.join([s['skill'] for s in well_covered[:3]])}"
            )
        
        if not recommendations:
            recommendations.append("Consider expanding skill diversity across the team")
        
        return recommendations
