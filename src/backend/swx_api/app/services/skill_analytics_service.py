"""
Async Analytics Engine
---------------------
Computes employee, department, and global skill analytics.
All methods are async for consistency.
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from swx_api.app.services.ingestion_service import paths
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("skill_analytics")


class SkillAnalyticsService:
    """Async analytics service for skill data."""
    
    def __init__(self):
        self.analysis_dir = paths.analysis_dir
    
    async def analyze_employee(
        self,
        employee_id: str,
        employee_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute employee-level analytics.
        
        Returns:
            - skill_level_stats: Statistics about skill levels
            - readiness_score: Overall readiness score
            - stagnation_detected: Boolean indicating skill stagnation
        """
        skills = employee_data.get("skills", [])
        
        # Skill level stats
        skill_count = len(skills)
        skill_level_stats = {
            "total_skills": skill_count,
            "skill_diversity": len(set(skills)),
            "average_skill_depth": self._calculate_skill_depth(skills, employee_data),
        }
        
        # Readiness score (based on skill count and diversity)
        readiness_score = min(100, int((skill_count * 10) + (skill_level_stats["skill_diversity"] * 5)))
        
        # Stagnation detection (check if skills haven't changed recently)
        stagnation_detected = self._detect_stagnation(employee_data)
        
        return {
            "employee_id": employee_id,
            "skill_level_stats": skill_level_stats,
            "readiness_score": readiness_score,
            "stagnation_detected": stagnation_detected,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    async def analyze_department(
        self,
        department_name: str,
        department_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute department-level analytics.
        
        Returns:
            - team_skill_heatmap: Skills mapped to employee counts
            - skill_shortages: Skills that are missing or underrepresented
            - risk_scores: Risk assessment for the department
        """
        if not department_data:
            return {
                "department": department_name,
                "team_skill_heatmap": {},
                "skill_shortages": [],
                "risk_scores": {},
            }
        
        # Build skill frequency map
        skill_frequency: Counter = Counter()
        employee_skills: Dict[str, List[str]] = {}
        
        for emp in department_data:
            emp_id = emp.get("employee_id", "unknown")
            skills = emp.get("skills", [])
            employee_skills[emp_id] = skills
            skill_frequency.update(skills)
        
        # Team skill heatmap
        team_skill_heatmap = {
            skill: count for skill, count in skill_frequency.most_common(50)
        }
        
        # Skill shortages (skills with low coverage)
        total_employees = len(department_data)
        skill_shortages = [
            skill for skill, count in skill_frequency.items()
            if count < max(1, total_employees * 0.2)  # Less than 20% coverage
        ]
        
        # Risk scores
        risk_scores = {
            "low_skill_coverage": len(skill_shortages),
            "average_skills_per_employee": sum(len(skills) for skills in employee_skills.values()) / max(total_employees, 1),
            "skill_concentration_risk": self._calculate_concentration_risk(skill_frequency, total_employees),
        }
        
        return {
            "department": department_name,
            "employee_count": total_employees,
            "team_skill_heatmap": team_skill_heatmap,
            "skill_shortages": skill_shortages[:20],  # Top 20 shortages
            "risk_scores": risk_scores,
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    async def analyze_global(
        self,
        all_employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute global analytics across all employees.
        
        Returns:
            - total_employees: Total number of employees
            - total_skills: Total unique skills
            - skill_frequency: Frequency of each skill
            - department_distribution: Skills per department
            - trends: Skill trends over time
        """
        if not all_employees:
            return {
                "total_employees": 0,
                "total_skills": 0,
                "skill_frequency": {},
                "department_distribution": {},
                "trends": {},
            }
        
        # Build skill frequency
        skill_frequency: Counter = Counter()
        department_skills: Dict[str, Counter] = defaultdict(Counter)
        
        for emp in all_employees:
            skills = emp.get("skills", [])
            department = emp.get("department", "Unknown")
            skill_frequency.update(skills)
            department_skills[department].update(skills)
        
        # Department distribution
        department_distribution = {
            dept: {
                "employee_count": sum(1 for e in all_employees if e.get("department") == dept),
                "unique_skills": len(skills),
                "top_skills": [skill for skill, _ in skills.most_common(10)],
            }
            for dept, skills in department_skills.items()
        }
        
        return {
            "total_employees": len(all_employees),
            "total_skills": len(skill_frequency),
            "skill_frequency": dict(skill_frequency.most_common(100)),
            "department_distribution": department_distribution,
            "trends": {},  # Would require historical data
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    async def analyze_trends(
        self,
        all_employees: List[Dict[str, Any]],
        period_months: int = 6
    ) -> Dict[str, Any]:
        """
        Analyze skill trends over time.
        
        Args:
            all_employees: List of employee data
            period_months: Time period in months
            
        Returns:
            Trend analysis dictionary
        """
        # For now, return basic trend data
        # In production, this would analyze historical data
        skill_frequency: Counter = Counter()
        for emp in all_employees:
            skill_frequency.update(emp.get("skills", []))
        
        return {
            "period_months": period_months,
            "top_growing_skills": [skill for skill, _ in skill_frequency.most_common(20)],
            "trend_analysis": "Historical trend analysis would require time-series data",
            "analyzed_at": datetime.utcnow().isoformat(),
        }
    
    def _calculate_skill_depth(self, skills: List[str], employee_data: Dict[str, Any]) -> float:
        """Calculate average skill depth (placeholder)."""
        # In production, this would analyze skill proficiency levels
        return float(len(skills)) * 0.5
    
    def _detect_stagnation(self, employee_data: Dict[str, Any]) -> bool:
        """Detect if employee skills have stagnated."""
        # In production, this would check historical skill changes
        return False
    
    def _calculate_concentration_risk(
        self,
        skill_frequency: Counter,
        total_employees: int
    ) -> float:
        """Calculate risk from skill concentration."""
        if not skill_frequency or total_employees == 0:
            return 0.0
        
        # Risk increases if few employees have critical skills
        max_frequency = max(skill_frequency.values()) if skill_frequency else 0
        concentration_ratio = max_frequency / total_employees if total_employees > 0 else 0
        
        # High risk if > 50% of employees depend on one person for a skill
        return min(100.0, concentration_ratio * 200)
