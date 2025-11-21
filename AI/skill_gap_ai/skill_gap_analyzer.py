"""
Skill Gap Analysis Engine
Analyzes employee skills vs position requirements
"""
import numpy as np
from typing import List, Dict, Tuple
from data_models import Employee, Position, Skill, SkillGap


class SkillGapAnalyzer:
    """Analyzes skill gaps between employees and positions"""
    
    def __init__(self):
        self.skill_similarity_cache = {}
    
    def analyze_employee(self, employee: Employee, target_position: Position) -> SkillGap:
        """
        Analyze skill gap for a single employee against a target position
        
        Args:
            employee: Employee to analyze
            target_position: Target position to compare against
            
        Returns:
            SkillGap object with detailed analysis
        """
        employee_skills = employee.get_skill_names()
        required_skills = target_position.get_required_skill_names()
        optional_skills = {s.name for s in target_position.optional_skills}
        
        # Find matched and missing skills
        matched_required = []
        missing_required = []
        
        for skill in target_position.required_skills:
            if self._has_skill_or_similar(skill.name, employee_skills):
                matched_required.append(skill)
            else:
                missing_required.append(skill)
        
        missing_optional = []
        for skill in target_position.optional_skills:
            if not self._has_skill_or_similar(skill.name, employee_skills):
                missing_optional.append(skill)
        
        # Calculate gap percentage (based on required skills only)
        total_required = len(target_position.required_skills)
        if total_required > 0:
            gap_percentage = (len(missing_required) / total_required) * 100
            readiness_score = 100 - gap_percentage
        else:
            gap_percentage = 0
            readiness_score = 100
        
        # Bonus points for optional skills
        matched_optional = len(target_position.optional_skills) - len(missing_optional)
        if len(target_position.optional_skills) > 0:
            optional_bonus = (matched_optional / len(target_position.optional_skills)) * 10
            readiness_score = min(100, readiness_score + optional_bonus)
        
        return SkillGap(
            employee=employee,
            target_position=target_position,
            missing_required_skills=missing_required,
            missing_optional_skills=missing_optional,
            matched_skills=matched_required,
            gap_percentage=round(gap_percentage, 2),
            readiness_score=round(readiness_score, 2)
        )
    
    def _has_skill_or_similar(self, required_skill: str, employee_skills: set) -> bool:
        """
        Check if employee has the skill or a similar one
        Uses fuzzy matching for flexibility
        """
        required_lower = required_skill.lower()
        
        # Exact match
        if required_skill in employee_skills:
            return True
        
        # Category-based matching - if required skill is a category, check if employee has any skill in that category
        for emp_skill in employee_skills:
            emp_lower = emp_skill.lower()
            
            # Check containment in both directions
            if required_lower in emp_lower or emp_lower in required_lower:
                return True
            
            # Check for word overlap (more lenient matching)
            req_words = set(required_lower.split())
            emp_words = set(emp_lower.split())
            
            # If at least 50% of words match, consider it a match
            if req_words & emp_words:
                overlap = len(req_words & emp_words)
                if overlap / len(req_words) >= 0.5:
                    return True
        
        return False
    
    def batch_analyze(self, employees: List[Employee], positions: Dict[str, Position]) -> Dict[str, List[SkillGap]]:
        """
        Analyze multiple employees against multiple positions
        
        Returns:
            Dictionary mapping position_id to list of SkillGap analyses
        """
        results = {}
        
        for pos_id, position in positions.items():
            position_results = []
            for employee in employees:
                gap = self.analyze_employee(employee, position)
                position_results.append(gap)
            
            # Sort by readiness score (descending)
            position_results.sort(key=lambda x: x.readiness_score, reverse=True)
            results[pos_id] = position_results
        
        return results
    
    def get_top_candidates(self, position: Position, employees: List[Employee], top_n: int = 10) -> List[Tuple[Employee, SkillGap]]:
        """
        Get top N candidates for a position based on readiness score
        
        Returns:
            List of (Employee, SkillGap) tuples sorted by readiness
        """
        gaps = [self.analyze_employee(emp, position) for emp in employees]
        gaps.sort(key=lambda x: x.readiness_score, reverse=True)
        
        return [(gap.employee, gap) for gap in gaps[:top_n]]


class TeamAnalyzer:
    """Analyzes team-level skill coverage and gaps"""
    
    def __init__(self):
        self.gap_analyzer = SkillGapAnalyzer()
    
    def analyze_team_coverage(self, team: List[Employee], position_requirements: List[Position]) -> Dict:
        """
        Analyze how well a team covers required skills across positions
        
        Returns:
            Dictionary with team-level metrics
        """
        # Collect all skills from team
        team_skills = set()
        for employee in team:
            team_skills.update(employee.get_skill_names())
        
        # Collect all required skills from positions
        all_required_skills = set()
        all_optional_skills = set()
        for position in position_requirements:
            all_required_skills.update(position.get_required_skill_names())
            all_optional_skills.update({s.name for s in position.optional_skills})
        
        # Calculate coverage
        covered_required = team_skills & all_required_skills
        missing_required = all_required_skills - team_skills
        covered_optional = team_skills & all_optional_skills
        
        coverage_percentage = 0
        if len(all_required_skills) > 0:
            coverage_percentage = (len(covered_required) / len(all_required_skills)) * 100
        
        # Skill redundancy (how many people have each skill)
        skill_counts = {}
        for employee in team:
            for skill_name in employee.get_skill_names():
                skill_counts[skill_name] = skill_counts.get(skill_name, 0) + 1
        
        # Find critical skills (required but low coverage)
        critical_skills = []
        for skill in all_required_skills:
            count = skill_counts.get(skill, 0)
            if count <= 1:  # Only 0-1 people have this skill
                critical_skills.append((skill, count))
        
        return {
            'team_size': len(team),
            'total_team_skills': len(team_skills),
            'required_skills_count': len(all_required_skills),
            'covered_required_skills': len(covered_required),
            'missing_required_skills': list(missing_required),
            'coverage_percentage': round(coverage_percentage, 2),
            'critical_skills': critical_skills,  # Skills with low redundancy
            'skill_distribution': skill_counts,
            'avg_skills_per_employee': round(np.mean([len(emp.get_skill_names()) for emp in team]), 2)
        }
    
    def identify_training_priorities(self, team: List[Employee], positions: List[Position]) -> List[Dict]:
        """
        Identify which skills the team should prioritize for training
        
        Returns:
            List of skills with priority scores
        """
        # Collect all required skills
        skill_importance = {}
        
        for position in positions:
            for skill in position.required_skills:
                if skill.name not in skill_importance:
                    skill_importance[skill.name] = {
                        'skill': skill,
                        'positions_requiring': 1,
                        'employees_with_skill': 0,
                        'priority_score': 0
                    }
                else:
                    skill_importance[skill.name]['positions_requiring'] += 1
        
        # Count employees with each skill
        for employee in team:
            emp_skills = employee.get_skill_names()
            for skill_name in skill_importance.keys():
                if skill_name in emp_skills:
                    skill_importance[skill_name]['employees_with_skill'] += 1
        
        # Calculate priority score
        # Higher score = more positions need it, fewer employees have it
        team_size = len(team)
        for skill_name, data in skill_importance.items():
            positions_needing = data['positions_requiring']
            coverage = data['employees_with_skill'] / team_size if team_size > 0 else 0
            gap = 1 - coverage
            
            # Priority = (number of positions needing it) * (gap in coverage)
            priority = positions_needing * gap * 100
            data['priority_score'] = round(priority, 2)
        
        # Sort by priority score
        priorities = sorted(skill_importance.values(), key=lambda x: x['priority_score'], reverse=True)
        
        return priorities
