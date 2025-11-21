"""
Manager Dashboard Analytics
Provides team-level insights, skill coverage, ROI analysis, and strategic planning
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from data_models import Employee, Position, Course, Skill, SkillGap


class ManagerDashboard:
    """Comprehensive analytics for managers to track team development"""
    
    def __init__(self):
        self.analytics_cache = {}
    
    def generate_team_overview(self, team: List[Employee], skill_gaps: List[SkillGap]) -> Dict:
        """
        Generate comprehensive team overview
        
        Returns:
            Dictionary with team metrics and insights
        """
        # Basic team metrics
        total_employees = len(team)
        avg_readiness = np.mean([gap.readiness_score for gap in skill_gaps]) if skill_gaps else 0
        
        # Categorize employees by readiness
        ready = [gap for gap in skill_gaps if gap.readiness_score >= 80]
        developing = [gap for gap in skill_gaps if 50 <= gap.readiness_score < 80]
        needs_development = [gap for gap in skill_gaps if gap.readiness_score < 50]
        
        # Calculate total training completed
        total_training_hours = sum(emp.get_total_learning_hours() for emp in team)
        avg_training_hours = total_training_hours / total_employees if total_employees > 0 else 0
        
        # Identify high performers
        high_performers = sorted(skill_gaps, key=lambda x: x.readiness_score, reverse=True)[:5]
        
        # Identify employees needing support
        needs_support = sorted(skill_gaps, key=lambda x: x.readiness_score)[:5]
        
        return {
            'team_size': total_employees,
            'avg_readiness_score': round(avg_readiness, 2),
            'ready_count': len(ready),
            'developing_count': len(developing),
            'needs_development_count': len(needs_development),
            'total_training_hours': round(total_training_hours, 1),
            'avg_training_hours_per_employee': round(avg_training_hours, 1),
            'high_performers': [
                {
                    'employee': gap.employee.name,
                    'position': gap.target_position.title,
                    'readiness': gap.readiness_score
                } for gap in high_performers
            ],
            'needs_support': [
                {
                    'employee': gap.employee.name,
                    'position': gap.target_position.title,
                    'readiness': gap.readiness_score,
                    'missing_skills': len(gap.missing_required_skills)
                } for gap in needs_support
            ]
        }
    
    def calculate_skill_coverage_matrix(self, team: List[Employee], 
                                       critical_skills: List[Skill]) -> pd.DataFrame:
        """
        Create a skill coverage matrix showing which employees have which skills
        
        Returns:
            DataFrame with employees as rows, skills as columns
        """
        # Initialize matrix
        matrix_data = []
        
        for employee in team:
            emp_skills = employee.get_skill_names()
            row = {
                'Employee': employee.name,
                'Position': employee.current_position
            }
            
            for skill in critical_skills:
                row[skill.name] = 1 if skill.name in emp_skills else 0
            
            matrix_data.append(row)
        
        df = pd.DataFrame(matrix_data)
        
        # Add summary row
        if len(df) > 0:
            summary = {'Employee': 'TOTAL', 'Position': 'Coverage'}
            for skill in critical_skills:
                summary[skill.name] = df[skill.name].sum()
            
            df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
        
        return df
    
    def analyze_training_roi(self, team: List[Employee], skill_gaps: List[SkillGap],
                            recommended_courses: Dict[str, Dict]) -> Dict:
        """
        Analyze return on investment for training programs
        
        Returns:
            Dictionary with ROI metrics
        """
        # Calculate current skill deficit (hours needed to fill gaps)
        total_training_needed = 0
        total_employees_with_gaps = 0
        
        for emp_id, recommendation in recommended_courses.items():
            if recommendation['estimated_hours'] > 0:
                total_training_needed += recommendation['estimated_hours']
                total_employees_with_gaps += 1
        
        # Estimate costs (example: $50/hour for training)
        cost_per_hour = 50
        total_training_cost = total_training_needed * cost_per_hour
        
        # Estimate productivity gains
        # Assume: each 10% readiness increase = 5% productivity gain
        current_avg_readiness = np.mean([gap.readiness_score for gap in skill_gaps]) if skill_gaps else 0
        potential_readiness = 90  # Target after training
        readiness_gain = potential_readiness - current_avg_readiness
        productivity_gain_percent = (readiness_gain / 10) * 5
        
        # Calculate break-even (example calculation)
        avg_salary = 60000  # Annual salary
        productivity_value = (productivity_gain_percent / 100) * avg_salary * len(team)
        months_to_breakeven = (total_training_cost / productivity_value) * 12 if productivity_value > 0 else 999
        
        return {
            'total_training_hours_needed': round(total_training_needed, 1),
            'employees_needing_training': total_employees_with_gaps,
            'estimated_training_cost': round(total_training_cost, 2),
            'avg_hours_per_employee': round(total_training_needed / max(total_employees_with_gaps, 1), 1),
            'current_avg_readiness': round(current_avg_readiness, 2),
            'target_readiness': potential_readiness,
            'expected_productivity_gain_percent': round(productivity_gain_percent, 2),
            'estimated_annual_value': round(productivity_value, 2),
            'months_to_breakeven': round(months_to_breakeven, 1) if months_to_breakeven < 999 else 'N/A'
        }
    
    def identify_succession_risks(self, team: List[Employee], 
                                  critical_positions: List[Position]) -> List[Dict]:
        """
        Identify succession planning risks (key positions with no backup)
        
        Returns:
            List of positions at risk
        """
        risks = []
        
        for position in critical_positions:
            # Count qualified employees
            qualified = [emp for emp in team if emp.current_position == position.title]
            
            # Count potential successors (employees with >70% readiness)
            from skill_gap_analyzer import SkillGapAnalyzer
            analyzer = SkillGapAnalyzer()
            
            potential_successors = []
            for emp in team:
                if emp.current_position != position.title:
                    gap = analyzer.analyze_employee(emp, position)
                    if gap.readiness_score >= 70:
                        potential_successors.append({
                            'employee': emp.name,
                            'current_position': emp.current_position,
                            'readiness': gap.readiness_score
                        })
            
            risk_level = 'HIGH' if len(potential_successors) == 0 else 'MEDIUM' if len(potential_successors) == 1 else 'LOW'
            
            risks.append({
                'position': position.title,
                'current_holders': len(qualified),
                'potential_successors_count': len(potential_successors),
                'potential_successors': potential_successors[:3],  # Top 3
                'risk_level': risk_level
            })
        
        # Sort by risk level
        risk_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        risks.sort(key=lambda x: risk_order[x['risk_level']])
        
        return risks
    
    def generate_training_priorities(self, team: List[Employee], 
                                    skill_gaps: List[SkillGap]) -> List[Dict]:
        """
        Generate training priorities based on business impact
        
        Returns:
            List of training priorities with justification
        """
        priorities = []
        
        # Count skill gaps across team
        skill_gap_count = defaultdict(int)
        skill_employees = defaultdict(list)
        
        for gap in skill_gaps:
            for skill in gap.missing_required_skills:
                skill_gap_count[skill.name] += 1
                skill_employees[skill.name].append(gap.employee.name)
        
        # Calculate priority score
        for skill_name, gap_count in skill_gap_count.items():
            # Priority factors:
            # 1. Number of employees missing the skill (higher = more priority)
            # 2. Percentage of team missing the skill
            team_size = len(team)
            gap_percentage = (gap_count / team_size) * 100 if team_size > 0 else 0
            
            # Priority score (0-100)
            priority_score = min(100, gap_percentage + (gap_count * 5))
            
            priority_level = 'CRITICAL' if priority_score >= 70 else 'HIGH' if priority_score >= 40 else 'MEDIUM'
            
            priorities.append({
                'skill': skill_name,
                'employees_missing': gap_count,
                'percentage_of_team': round(gap_percentage, 1),
                'priority_score': round(priority_score, 1),
                'priority_level': priority_level,
                'affected_employees': skill_employees[skill_name][:5]  # Sample
            })
        
        # Sort by priority score
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return priorities
    
    def generate_quarterly_plan(self, team: List[Employee], 
                               recommended_courses: Dict[str, Dict],
                               quarter_hours: int = 40) -> Dict:
        """
        Generate a quarterly training plan based on available hours per employee
        
        Args:
            team: List of employees
            recommended_courses: Course recommendations per employee
            quarter_hours: Available training hours per employee per quarter
            
        Returns:
            Quarterly training plan
        """
        plan = {
            'quarter': 'Q1 2025',  # Customize as needed
            'total_budget_hours': len(team) * quarter_hours,
            'employee_plans': [],
            'group_training_sessions': [],
            'overflow_to_next_quarter': []
        }
        
        for emp_id, recommendations in recommended_courses.items():
            # Find employee
            employee = next((e for e in team if e.employee_id == emp_id), None)
            if not employee:
                continue
            
            # Prioritize courses that fit in quarter
            courses_this_quarter = []
            courses_next_quarter = []
            hours_allocated = 0
            
            for course_info in recommendations.get('priority_courses', []):
                course_hours = course_info['hours']
                if hours_allocated + course_hours <= quarter_hours:
                    courses_this_quarter.append({
                        'course': course_info['course'].title,
                        'skill': course_info['skill'].name,
                        'hours': course_hours
                    })
                    hours_allocated += course_hours
                else:
                    courses_next_quarter.append({
                        'course': course_info['course'].title,
                        'skill': course_info['skill'].name,
                        'hours': course_hours
                    })
            
            plan['employee_plans'].append({
                'employee': employee.name,
                'courses_this_quarter': courses_this_quarter,
                'hours_allocated': round(hours_allocated, 1),
                'utilization_percent': round((hours_allocated / quarter_hours) * 100, 1)
            })
            
            if courses_next_quarter:
                plan['overflow_to_next_quarter'].append({
                    'employee': employee.name,
                    'pending_courses': courses_next_quarter
                })
        
        return plan
    
    def export_report(self, team: List[Employee], skill_gaps: List[SkillGap],
                     recommendations: Dict, output_format: str = 'dict') -> Dict:
        """
        Export comprehensive report for managers
        
        Returns:
            Complete report dictionary
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'team_overview': self.generate_team_overview(team, skill_gaps),
            'training_roi': self.analyze_training_roi(team, skill_gaps, recommendations),
            'training_priorities': self.generate_training_priorities(team, skill_gaps)[:10],
            'summary_stats': {
                'total_employees': len(team),
                'total_skill_gaps': sum(len(gap.missing_required_skills) for gap in skill_gaps),
                'avg_gap_percentage': round(np.mean([gap.gap_percentage for gap in skill_gaps]), 2) if skill_gaps else 0
            }
        }
        
        return report
