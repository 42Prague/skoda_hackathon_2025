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
        
    def get_skill_breadth(self, employee_id: int) -> Optional[int]:
        """
        Get personalized skill breadth for an employee
        
        Args:
            employee_id: ID of the employee
        """
        employee = self.data_accesser.get_employee_data(employee_id)
        if not employee:
            return None

    def get_employee_diagram(self, employee_id: int) -> Optional[Dict[str, float]]:
        """
        Get skill diagram data for an employee
        
        Args:
            employee_id: ID of the employee
        """
        employee = self.employee_service._find_employee_by_id(employee_id)
        if not employee:
            return None
        
        # Example diagram data (could be expanded)
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
    
    
    def get_skill_suggestions(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate comprehensive skill suggestions for an employee
        
        Args:
            employee_id: ID of the employee
            
        Returns:
            Dictionary with different types of suggestions
        """
        employee_dict = self.employee_service.get_employee_by_id(employee_id)
        if not employee_dict:
            return None
        
        employee = self.employee_service._find_employee_by_id(employee_id)
        
        # Generate different types of suggestions
        similar_role_suggestions = self._get_similar_role_suggestions(employee)
        trending_suggestions = self._get_trending_suggestions(employee)
        advancement_suggestions = self._get_advancement_suggestions(employee)
        complementary_suggestions = self._get_complementary_suggestions(employee)
        
        return {
            "employee": employee_dict,
            "suggestions": {
                "similar_roles": {
                    "skills": similar_role_suggestions[:5],
                    "explanation": "Skills commonly found in similar positions"
                },
                "trending": {
                    "skills": trending_suggestions[:3],
                    "explanation": "Currently trending skills in your department"
                },
                "career_advancement": {
                    "skills": advancement_suggestions[:4],
                    "explanation": "Skills that could accelerate career growth"
                },
                "complementary": {
                    "skills": complementary_suggestions[:3],
                    "explanation": "Skills that complement your existing expertise"
                }
            },
            "priority_score": self._calculate_priority_scores(
                employee, similar_role_suggestions + advancement_suggestions
            )
        }
    
    def _get_similar_role_suggestions(self, employee: Employee) -> List[str]:
        """Get suggestions based on similar roles"""
        similar_employees = self._find_similar_employees(employee)
        
        # Collect skills from similar employees
        skill_counts = Counter()
        for similar_emp in similar_employees:
            for skill in similar_emp.skills:
                if not employee.has_skill(skill):
                    skill_counts[skill] += 1
        
        # Return skills that appear in multiple similar employees
        return [skill for skill, count in skill_counts.most_common() if count > 1]
    
    def _get_trending_suggestions(self, employee: Employee) -> List[str]:
        """Get trending skills in employee's department"""
        dept_employees = self.employee_service.get_employees_by_department(employee.department)
        
        # Count skills in department
        skill_counts = Counter()
        for emp in dept_employees:
            if emp.employee_id != employee.employee_id:
                for skill in emp.skills:
                    if not employee.has_skill(skill):
                        skill_counts[skill] += 1
        
        return [skill for skill, _ in skill_counts.most_common(10)]
    
    def _get_advancement_suggestions(self, employee: Employee) -> List[str]:
        """Get skills for career advancement"""
        # Find employees with more experience in same department
        advanced_employees = [
            emp for emp in self.employee_service.employees
            if (emp.department == employee.department and 
                emp.experience_years > employee.experience_years and
                emp.employee_id != employee.employee_id)
        ]
        
        skill_counts = Counter()
        for emp in advanced_employees:
            for skill in emp.skills:
                if not employee.has_skill(skill):
                    # Weight by experience difference
                    weight = min(emp.experience_years - employee.experience_years, 5)
                    skill_counts[skill] += weight
        
        return [skill for skill, _ in skill_counts.most_common()]
    
    def _get_complementary_suggestions(self, employee: Employee) -> List[str]:
        """Get skills that complement existing skills"""
        # Define skill relationships (this could be enhanced with ML)
        skill_relationships = {
            'python': ['data science', 'machine learning', 'flask', 'django'],
            'javascript': ['react', 'node.js', 'typescript', 'vue.js'],
            'sql': ['database design', 'data analysis', 'reporting'],
            'project management': ['agile', 'scrum', 'leadership'],
            'leadership': ['communication', 'team building', 'mentoring']
        }
        
        complementary_skills = set()
        for skill in employee.skills:
            if skill in skill_relationships:
                complementary_skills.update(skill_relationships[skill])
        
        # Remove skills already possessed
        return [skill for skill in complementary_skills if not employee.has_skill(skill)]
    
    def _find_similar_employees(self, employee: Employee) -> List[Employee]:
        """Find employees with similar roles or departments"""
        similar = []
        
        for emp in self.employee_service.employees:
            if emp.employee_id == employee.employee_id:
                continue
            
            similarity_score = self._calculate_similarity(employee, emp)
            if similarity_score > 0.3:  # Threshold for similarity
                similar.append(emp)
        
        return sorted(similar, key=lambda e: self._calculate_similarity(employee, e), reverse=True)
    
    def _calculate_similarity(self, emp1: Employee, emp2: Employee) -> float:
        """Calculate similarity score between two employees"""
        score = 0.0
        
        # Department match
        if emp1.department.lower() == emp2.department.lower():
            score += 0.4
        
        # Position similarity (check for common words)
        pos1_words = set(emp1.position.lower().split())
        pos2_words = set(emp2.position.lower().split())
        position_overlap = len(pos1_words & pos2_words) / len(pos1_words | pos2_words)
        score += position_overlap * 0.3
        
        # Experience similarity
        exp_diff = abs(emp1.experience_years - emp2.experience_years)
        exp_similarity = max(0, 1 - exp_diff / 10)  # Normalize to 0-1
        score += exp_similarity * 0.3
        
        return min(score, 1.0)
    
    def _calculate_priority_scores(self, employee: Employee, suggested_skills: List[str]) -> Dict[str, float]:
        """Calculate priority scores for suggested skills"""
        scores = {}
        
        for skill in suggested_skills[:10]:  # Top 10 skills
            score = 0.0
            
            # Frequency in similar roles
            similar_employees = self._find_similar_employees(employee)
            skill_frequency = sum(1 for emp in similar_employees if emp.has_skill(skill))
            score += (skill_frequency / len(similar_employees)) * 0.4 if similar_employees else 0
            
            # Market demand (simplified - could integrate with job market APIs)
            high_demand_skills = ['python', 'javascript', 'sql', 'machine learning', 'cloud computing']
            if skill.lower() in high_demand_skills:
                score += 0.3
            
            # Career advancement potential
            advanced_employees = [
                emp for emp in self.employee_service.employees
                if emp.experience_years > employee.experience_years
            ]
            advancement_frequency = sum(1 for emp in advanced_employees if emp.has_skill(skill))
            score += (advancement_frequency / len(advanced_employees)) * 0.3 if advanced_employees else 0
            
            scores[skill] = round(score, 2)
        
        return scores
    
    def analyze_skills_gap(self, department: Optional[str] = None, 
                          position: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive skills gap analysis
        
        Args:
            department: Filter by department
            position: Filter by position
            
        Returns:
            Detailed analysis of skills gaps
        """
        # Get target employees
        employees = self.employee_service.get_employees(
            department=department,
            position=position
        )
        
        if not employees:
            return {"error": "No employees found matching criteria"}
        
        # Convert to Employee objects for analysis
        employee_objects = [
            self.employee_service._find_employee_by_id(emp['employee_id'])
            for emp in employees
        ]
        
        # Analyze skills
        all_skills = []
        for emp in employee_objects:
            all_skills.extend(emp.skills)
        
        skill_analysis = self._perform_detailed_skill_analysis(employee_objects, all_skills)
        
        return {
            "scope": f"Department: {department}" if department else "Organization-wide",
            "total_employees": len(employees),
            "analysis": skill_analysis,
            "recommendations": self._generate_gap_recommendations(skill_analysis),
            "risk_assessment": self._assess_skill_risks(skill_analysis)
        }
    
    def _perform_detailed_skill_analysis(self, employees: List[Employee], all_skills: List[str]) -> List[Dict]:
        """Perform detailed analysis of skills"""
        skill_counts = Counter(all_skills)
        total_employees = len(employees)
        
        analysis = []
        for skill, count in skill_counts.most_common():
            coverage = (count / total_employees) * 100
            
            # Calculate skill depth (average experience of people with this skill)
            skill_holders = [emp for emp in employees if emp.has_skill(skill)]
            avg_experience = sum(emp.experience_years for emp in skill_holders) / len(skill_holders)
            
            analysis.append({
                "skill": skill,
                "employee_count": count,
                "coverage_percentage": round(coverage, 1),
                "average_experience": round(avg_experience, 1),
                "gap_level": self._determine_gap_level(coverage),
                "risk_level": self._assess_skill_risk(coverage, len(skill_holders))
            })
        
        return analysis
    
    def _determine_gap_level(self, coverage: float) -> str:
        """Determine gap level based on coverage"""
        if coverage >= 75:
            return "Low"
        elif coverage >= 50:
            return "Medium"
        elif coverage >= 25:
            return "High"
        else:
            return "Critical"
    
    def _assess_skill_risk(self, coverage: float, holder_count: int) -> str:
        """Assess risk level for a skill"""
        if coverage < 25 or holder_count == 1:
            return "High"
        elif coverage < 50 or holder_count == 2:
            return "Medium"
        else:
            return "Low"
    
    def _generate_gap_recommendations(self, skill_analysis: List[Dict]) -> List[str]:
        """Generate recommendations based on gap analysis"""
        recommendations = []
        
        critical_gaps = [s for s in skill_analysis if s["gap_level"] == "Critical"]
        high_risks = [s for s in skill_analysis if s["risk_level"] == "High"]
        
        if critical_gaps:
            skills_list = ", ".join([s["skill"] for s in critical_gaps[:3]])
            recommendations.append(f"URGENT: Address critical skill gaps in: {skills_list}")
        
        if high_risks:
            skills_list = ", ".join([s["skill"] for s in high_risks[:3]])
            recommendations.append(f"HIGH PRIORITY: Reduce single points of failure in: {skills_list}")
        
        # Find well-covered skills for knowledge sharing
        well_covered = [s for s in skill_analysis if s["gap_level"] == "Low" and s["coverage_percentage"] > 80]
        if well_covered:
            skills_list = ", ".join([s["skill"] for s in well_covered[:2]])
            recommendations.append(f"LEVERAGE: Use expertise in {skills_list} for mentoring")
        
        return recommendations
    
    def _assess_skill_risks(self, skill_analysis: List[Dict]) -> Dict[str, Any]:
        """Assess overall risk levels"""
        total_skills = len(skill_analysis)
        critical_count = len([s for s in skill_analysis if s["gap_level"] == "Critical"])
        high_risk_count = len([s for s in skill_analysis if s["risk_level"] == "High"])
        
        overall_risk = "Low"
        if critical_count > 0 or high_risk_count > total_skills * 0.3:
            overall_risk = "High"
        elif high_risk_count > total_skills * 0.1:
            overall_risk = "Medium"
        
        return {
            "overall_risk": overall_risk,
            "critical_gaps": critical_count,
            "high_risk_skills": high_risk_count,
            "risk_score": round((critical_count * 2 + high_risk_count) / total_skills * 100, 1)
        }
    
    def get_skill_trends(self, department: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending skills with growth indicators"""
        employees = self.employee_service.get_employees(department=department)
        
        # This is simplified - in real implementation, you'd track skills over time
        skill_counts = Counter()
        for emp_data in employees:
            for skill in emp_data['skills']:
                skill_counts[skill] += 1
        
        trends = []
        for skill, count in skill_counts.most_common(limit):
            # Simplified trend calculation (in real app, you'd have historical data)
            trend_direction = "stable"  # Could be "growing", "declining", "stable"
            
            trends.append({
                "skill": skill,
                "employee_count": count,
                "trend_direction": trend_direction,
                "market_demand": self._get_market_demand_indicator(skill)
            })
        
        return trends
    
    def _get_market_demand_indicator(self, skill: str) -> str:
        """Get market demand indicator for a skill (simplified)"""
        high_demand = ['python', 'javascript', 'sql', 'machine learning', 'cloud computing', 'react']
        medium_demand = ['java', 'html', 'css', 'project management', 'scrum']
        
        if skill.lower() in high_demand:
            return "High"
        elif skill.lower() in medium_demand:
            return "Medium"
        else:
            return "Low"
    
    def check_team_compatibility(self, employee_ids: List[int]) -> Dict[str, Any]:
        """Check skill compatibility and coverage for a team"""
        team_members = []
        for emp_id in employee_ids:
            emp = self.employee_service._find_employee_by_id(emp_id)
            if emp:
                team_members.append(emp)
        
        if not team_members:
            return {"error": "No valid employees found"}
        
        # Analyze team composition
        all_team_skills = set()
        skill_overlap = {}
        
        for emp in team_members:
            all_team_skills.update(emp.skills)
            for skill in emp.skills:
                skill_overlap[skill] = skill_overlap.get(skill, 0) + 1
        
        return {
            "team_size": len(team_members),
            "total_unique_skills": len(all_team_skills),
            "skill_coverage": {
                "well_covered": [skill for skill, count in skill_overlap.items() if count > 1],
                "single_person_skills": [skill for skill, count in skill_overlap.items() if count == 1]
            },
            "experience_distribution": {
                "average_experience": round(sum(emp.experience_years for emp in team_members) / len(team_members), 1),
                "experience_range": [min(emp.experience_years for emp in team_members), 
                                   max(emp.experience_years for emp in team_members)]
            },
            "recommendations": self._generate_team_recommendations(team_members, skill_overlap)
        }
    
    def _generate_team_recommendations(self, team_members: List[Employee], 
                                     skill_overlap: Dict[str, int]) -> List[str]:
        """Generate recommendations for team improvement"""
        recommendations = []
        
        single_skills = [skill for skill, count in skill_overlap.items() if count == 1]
        if single_skills:
            recommendations.append(f"Consider cross-training in: {', '.join(single_skills[:3])}")
        
        exp_levels = [emp.experience_years for emp in team_members]
        if max(exp_levels) - min(exp_levels) > 5:
            recommendations.append("Good experience distribution - leverage senior members for mentoring")
        
        return recommendations
