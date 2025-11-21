"""
Async Employee-to-Employee Recommendation (Mentor Finder)
---------------------------------------------------------
Finds employees who can mentor others, cover missing skills,
substitute temporarily, or share knowledge. All methods are async.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("mentor_recommendation")


class MentorRecommendationService:
    """Async service for finding mentors and skill matches between employees."""
    
    def __init__(self):
        pass
    
    def find_mentors(
        self,
        employee_id: str,
        employee_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]],
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Find potential mentors for an employee (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await find_mentors_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._find_mentors_async(employee_id, employee_data, all_employees, max_recommendations))

    async def find_mentors_async(
        self,
        employee_id: str,
        employee_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]],
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """Async version of find_mentors - use this in async contexts."""
        return await self._find_mentors_async(employee_id, employee_data, all_employees, max_recommendations)

    async def _find_mentors_async(
        self,
        employee_id: str,
        employee_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]],
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Find potential mentors for an employee.
        
        Args:
            employee_id: Target employee ID
            employee_data: Target employee data
            all_employees: All employee records
            max_recommendations: Maximum number of recommendations
            
        Returns:
            Dictionary with:
            - mentors: List of mentor recommendations
            - skill_coverage: Skills that can be covered by mentors
            - substitution_candidates: Employees who can substitute
            - knowledge_sharing: Knowledge sharing opportunities
        """
        try:
            # Filter out the target employee
            other_employees = [
                emp for emp in all_employees
                if emp.get("employee_id") != employee_id
            ]
            
            if not other_employees:
                return {
                    "mentors": [],
                    "skill_coverage": [],
                    "substitution_candidates": [],
                    "knowledge_sharing": [],
                    "employee_id": employee_id
                }
            
            # Get target employee's skills and gaps
            target_skills = set(employee_data.get("skills", []))
            target_dept = employee_data.get("department", "Unknown")
            
            # Find mentors
            mentors = self._find_mentor_candidates(
                employee_id,
                employee_data,
                other_employees,
                max_recommendations
            )
            
            # Find skill coverage
            skill_coverage = self._find_skill_coverage(
                target_skills,
                other_employees
            )
            
            # Find substitution candidates
            substitution_candidates = self._find_substitution_candidates(
                employee_id,
                employee_data,
                other_employees
            )
            
            # Find knowledge sharing opportunities
            knowledge_sharing = self._find_knowledge_sharing(
                employee_id,
                employee_data,
                other_employees
            )
            
            return {
                "employee_id": employee_id,
                "mentors": mentors,
                "skill_coverage": skill_coverage,
                "substitution_candidates": substitution_candidates,
                "knowledge_sharing": knowledge_sharing,
                "analyzed_at": json.dumps({"$date": None}),
            }
            
        except Exception as e:
            logger.error(f"Error finding mentors: {e}", exc_info=True)
            return {
                "employee_id": employee_id,
                "mentors": [],
                "skill_coverage": [],
                "substitution_candidates": [],
                "knowledge_sharing": [],
                "error": str(e)
            }
    
    def _find_mentor_candidates(
        self,
        target_id: str,
        target_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]],
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Find employees who can mentor the target."""
        target_skills = set(target_data.get("skills", []))
        target_dept = target_data.get("department", "Unknown")
        
        candidates = []
        
        for emp in all_employees:
            emp_id = emp.get("employee_id")
            emp_skills = set(emp.get("skills", []))
            emp_dept = emp.get("department", "Unknown")
            
            # Calculate compatibility score
            compatibility = self._calculate_compatibility(
                target_skills,
                emp_skills,
                target_dept,
                emp_dept
            )
            
            # Find skills the mentor can teach
            teachable_skills = emp_skills - target_skills
            
            if teachable_skills and compatibility["score"] > 0.3:
                candidates.append({
                    "employee_id": emp_id,
                    "department": emp_dept,
                    "compatibility_score": compatibility["score"],
                    "teachable_skills": list(teachable_skills)[:10],
                    "shared_skills": list(target_skills & emp_skills)[:5],
                    "skill_gap_coverage": len(teachable_skills),
                    "recommendation_reason": compatibility["reason"],
                    "mentor_type": self._determine_mentor_type(compatibility, teachable_skills)
                })
        
        # Sort by compatibility score
        candidates.sort(key=lambda x: x["compatibility_score"], reverse=True)
        
        return candidates[:max_recommendations]
    
    def _calculate_compatibility(
        self,
        target_skills: set,
        mentor_skills: set,
        target_dept: str,
        mentor_dept: str
    ) -> Dict[str, Any]:
        """Calculate compatibility score between target and potential mentor."""
        # Skill overlap (shared skills indicate similar work)
        shared_skills = target_skills & mentor_skills
        skill_overlap = len(shared_skills) / len(target_skills) if target_skills else 0
        
        # Skill gap coverage (skills mentor has that target needs)
        gap_coverage = mentor_skills - target_skills
        gap_coverage_score = len(gap_coverage) / 10.0  # Normalize
        
        # Department match (same department = higher compatibility)
        dept_match = 0.3 if target_dept == mentor_dept else 0.1
        
        # Combined score
        compatibility_score = (skill_overlap * 0.4) + (gap_coverage_score * 0.4) + (dept_match * 0.2)
        compatibility_score = min(1.0, compatibility_score)
        
        # Determine reason
        if skill_overlap > 0.5 and len(gap_coverage) > 3:
            reason = "Strong skill overlap with complementary expertise"
        elif len(gap_coverage) > 5:
            reason = "Can teach many missing skills"
        elif skill_overlap > 0.6:
            reason = "Similar skill profile, can provide guidance"
        else:
            reason = "Potential mentor with relevant skills"
        
        return {
            "score": round(compatibility_score, 3),
            "reason": reason,
            "skill_overlap": len(shared_skills),
            "gap_coverage": len(gap_coverage)
        }
    
    def _determine_mentor_type(
        self,
        compatibility: Dict[str, Any],
        teachable_skills: set
    ) -> str:
        """Determine type of mentor."""
        if len(teachable_skills) >= 5:
            return "skill_mentor"
        elif compatibility["skill_overlap"] >= 3:
            return "peer_mentor"
        else:
            return "general_mentor"
    
    def _find_skill_coverage(
        self,
        target_skills: set,
        all_employees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find employees who can cover specific skills."""
        coverage_map = {}
        
        for emp in all_employees:
            emp_id = emp.get("employee_id")
            emp_skills = set(emp.get("skills", []))
            emp_dept = emp.get("department", "Unknown")
            
            # Skills this employee can cover
            can_cover = emp_skills - target_skills
            
            if can_cover:
                for skill in can_cover:
                    if skill not in coverage_map:
                        coverage_map[skill] = []
                    
                    coverage_map[skill].append({
                        "employee_id": emp_id,
                        "department": emp_dept,
                        "skill_level": "expert"  # Placeholder
                    })
        
        # Format as list
        coverage_list = [
            {
                "skill": skill,
                "available_employees": employees[:5],  # Top 5 per skill
                "employee_count": len(employees)
            }
            for skill, employees in coverage_map.items()
        ]
        
        # Sort by employee count
        coverage_list.sort(key=lambda x: x["employee_count"], reverse=True)
        
        return coverage_list[:20]  # Top 20 skills
    
    def _find_substitution_candidates(
        self,
        target_id: str,
        target_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find employees who can substitute for the target."""
        target_skills = set(target_data.get("skills", []))
        target_dept = target_data.get("department", "Unknown")
        
        candidates = []
        
        for emp in all_employees:
            emp_id = emp.get("employee_id")
            emp_skills = set(emp.get("skills", []))
            emp_dept = emp.get("department", "Unknown")
            
            # Calculate substitution score
            skill_match = len(target_skills & emp_skills) / len(target_skills) if target_skills else 0
            dept_match = 1.0 if target_dept == emp_dept else 0.5
            
            substitution_score = (skill_match * 0.7) + (dept_match * 0.3)
            
            if substitution_score >= 0.6:  # At least 60% match
                missing_skills = target_skills - emp_skills
                extra_skills = emp_skills - target_skills
                
                candidates.append({
                    "employee_id": emp_id,
                    "department": emp_dept,
                    "substitution_score": round(substitution_score, 3),
                    "skill_match_rate": round(skill_match, 3),
                    "missing_skills": list(missing_skills)[:5],
                    "extra_skills": list(extra_skills)[:5],
                    "readiness": "ready" if substitution_score >= 0.8 else "almost-ready"
                })
        
        # Sort by substitution score
        candidates.sort(key=lambda x: x["substitution_score"], reverse=True)
        
        return candidates[:10]  # Top 10
    
    def _find_knowledge_sharing(
        self,
        target_id: str,
        target_data: Dict[str, Any],
        all_employees: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Find knowledge sharing opportunities."""
        target_skills = set(target_data.get("skills", []))
        opportunities = []
        
        for emp in all_employees:
            emp_id = emp.get("employee_id")
            emp_skills = set(emp.get("skills", []))
            emp_dept = emp.get("department", "Unknown")
            
            # Skills target can teach to this employee
            target_can_teach = target_skills - emp_skills
            # Skills this employee can teach to target
            emp_can_teach = emp_skills - target_skills
            
            if target_can_teach or emp_can_teach:
                opportunities.append({
                    "employee_id": emp_id,
                    "department": emp_dept,
                    "target_can_share": list(target_can_teach)[:5],
                    "employee_can_share": list(emp_can_teach)[:5],
                    "mutual_benefit": len(target_can_teach) > 0 and len(emp_can_teach) > 0,
                    "sharing_potential": "high" if len(target_can_teach) + len(emp_can_teach) >= 5 else "medium"
                })
        
        # Sort by sharing potential
        opportunities.sort(
            key=lambda x: len(x["target_can_share"]) + len(x["employee_can_share"]),
            reverse=True
        )
        
        return opportunities[:15]  # Top 15
