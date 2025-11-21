"""
Async Cross-Team Skill Similarity Analysis
-------------------------------------------
Generates similarity matrix between teams, identifies cross-support opportunities,
and detects skill redundancies. All methods are async for consistency.
"""

import json
import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional

from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("team_similarity")


class TeamSimilarityService:
    """Async service for analyzing team skill similarities."""
    
    def __init__(self):
        pass
    
    def analyze_team_similarity(
        self,
        all_employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze similarity between teams/departments (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await analyze_team_similarity_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._analyze_team_similarity_async(all_employees))

    async def analyze_team_similarity_async(
        self,
        all_employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Async version of analyze_team_similarity - use this in async contexts."""
        return await self._analyze_team_similarity_async(all_employees)

    async def _analyze_team_similarity_async(
        self,
        all_employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze similarity between teams/departments.
        
        Args:
            all_employees: List of employee records with department and skills
            
        Returns:
            Dictionary with:
            - similarity_matrix: Pairwise similarity scores between teams
            - cross_support_opportunities: Teams that can support each other
            - skill_redundancies: Skills duplicated across teams
            - cross_training_opportunities: Training opportunities between teams
        """
        try:
            # Group employees by department
            department_employees = defaultdict(list)
            for emp in all_employees:
                dept = emp.get("department", "Unknown")
                department_employees[dept].append(emp)
            
            departments = list(department_employees.keys())
            
            # Build skill profiles for each department
            department_profiles = {}
            for dept, employees in department_employees.items():
                department_profiles[dept] = self._build_department_profile(dept, employees)
            
            # Compute similarity matrix
            similarity_matrix = self._compute_similarity_matrix(department_profiles)
            
            # Identify cross-support opportunities
            cross_support = self._identify_cross_support(similarity_matrix, department_profiles)
            
            # Detect skill redundancies
            skill_redundancies = self._detect_skill_redundancies(department_profiles)
            
            # Identify cross-training opportunities
            cross_training = self._identify_cross_training(similarity_matrix, department_profiles)
            
            return {
                "similarity_matrix": similarity_matrix,
                "cross_support_opportunities": cross_support,
                "skill_redundancies": skill_redundancies,
                "cross_training_opportunities": cross_training,
                "total_departments": len(departments),
                "analyzed_at": json.dumps({"$date": None}),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing team similarity: {e}", exc_info=True)
            return {
                "similarity_matrix": {},
                "cross_support_opportunities": [],
                "skill_redundancies": [],
                "cross_training_opportunities": [],
                "error": str(e)
            }
    
    def _build_department_profile(
        self,
        department: str,
        employees: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build skill profile for a department."""
        skill_counter: Counter = Counter()
        employee_skills: Dict[str, List[str]] = {}
        
        for emp in employees:
            emp_id = emp.get("employee_id", "unknown")
            skills = emp.get("skills", [])
            employee_skills[emp_id] = skills
            skill_counter.update(skills)
        
        # Calculate skill coverage (percentage of employees with each skill)
        team_size = len(employees)
        skill_coverage = {
            skill: count / team_size if team_size > 0 else 0
            for skill, count in skill_counter.items()
        }
        
        return {
            "department": department,
            "team_size": team_size,
            "skills": list(skill_counter.keys()),
            "skill_frequency": dict(skill_counter),
            "skill_coverage": skill_coverage,
            "unique_skill_count": len(skill_counter),
            "employee_skills": employee_skills
        }
    
    def _compute_similarity_matrix(
        self,
        department_profiles: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Compute pairwise similarity scores between departments."""
        departments = list(department_profiles.keys())
        matrix = {}
        
        for dept1 in departments:
            matrix[dept1] = {}
            profile1 = department_profiles[dept1]
            skills1 = set(profile1["skills"])
            
            for dept2 in departments:
                if dept1 == dept2:
                    matrix[dept1][dept2] = 1.0
                else:
                    profile2 = department_profiles[dept2]
                    skills2 = set(profile2["skills"])
                    
                    # Jaccard similarity
                    intersection = len(skills1 & skills2)
                    union = len(skills1 | skills2)
                    jaccard = intersection / union if union > 0 else 0.0
                    
                    # Weighted similarity (consider skill coverage)
                    weighted_sim = self._compute_weighted_similarity(profile1, profile2)
                    
                    # Combined similarity
                    combined = (jaccard * 0.4) + (weighted_sim * 0.6)
                    
                    matrix[dept1][dept2] = round(combined, 3)
        
        return matrix
    
    def _compute_weighted_similarity(
        self,
        profile1: Dict[str, Any],
        profile2: Dict[str, Any]
    ) -> float:
        """Compute weighted similarity based on skill coverage."""
        coverage1 = profile1.get("skill_coverage", {})
        coverage2 = profile2.get("skill_coverage", {})
        
        common_skills = set(coverage1.keys()) & set(coverage2.keys())
        
        if not common_skills:
            return 0.0
        
        # Average coverage similarity for common skills
        similarities = []
        for skill in common_skills:
            cov1 = coverage1[skill]
            cov2 = coverage2[skill]
            # Use minimum coverage as similarity measure
            similarities.append(min(cov1, cov2))
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _identify_cross_support(
        self,
        similarity_matrix: Dict[str, Dict[str, float]],
        department_profiles: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify teams that can cross-support each other."""
        opportunities = []
        threshold = 0.3  # Minimum similarity for cross-support
        
        departments = list(similarity_matrix.keys())
        
        for i, dept1 in enumerate(departments):
            for dept2 in departments[i+1:]:
                similarity = similarity_matrix[dept1][dept2]
                
                if similarity >= threshold:
                    # Find complementary skills
                    profile1 = department_profiles[dept1]
                    profile2 = department_profiles[dept2]
                    
                    skills1 = set(profile1["skills"])
                    skills2 = set(profile2["skills"])
                    
                    # Skills dept1 has that dept2 needs
                    dept1_can_help = skills1 - skills2
                    # Skills dept2 has that dept1 needs
                    dept2_can_help = skills2 - skills1
                    
                    if dept1_can_help or dept2_can_help:
                        opportunities.append({
                            "team1": dept1,
                            "team2": dept2,
                            "similarity_score": similarity,
                            "team1_can_support_team2": list(dept1_can_help)[:5],
                            "team2_can_support_team1": list(dept2_can_help)[:5],
                            "shared_skills": list(skills1 & skills2)[:10],
                            "support_potential": "high" if similarity >= 0.5 else "medium"
                        })
        
        # Sort by similarity score
        opportunities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return opportunities[:20]  # Top 20
    
    def _detect_skill_redundancies(
        self,
        department_profiles: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect skills that are duplicated across multiple teams."""
        # Count how many departments have each skill
        skill_department_map = defaultdict(list)
        
        for dept, profile in department_profiles.items():
            skills = profile.get("skills", [])
            for skill in skills:
                skill_department_map[skill].append(dept)
        
        redundancies = []
        for skill, departments in skill_department_map.items():
            if len(departments) > 1:  # Skill exists in multiple departments
                # Calculate average coverage
                total_coverage = 0
                for dept in departments:
                    profile = department_profiles[dept]
                    coverage = profile.get("skill_coverage", {}).get(skill, 0)
                    total_coverage += coverage
                
                avg_coverage = total_coverage / len(departments)
                
                redundancies.append({
                    "skill": skill,
                    "departments": departments,
                    "department_count": len(departments),
                    "average_coverage": round(avg_coverage, 3),
                    "redundancy_level": "high" if len(departments) >= 3 else "medium"
                })
        
        # Sort by department count
        redundancies.sort(key=lambda x: x["department_count"], reverse=True)
        
        return redundancies
    
    def _identify_cross_training(
        self,
        similarity_matrix: Dict[str, Dict[str, float]],
        department_profiles: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify cross-training opportunities between teams."""
        opportunities = []
        threshold = 0.2  # Minimum similarity for cross-training
        
        departments = list(similarity_matrix.keys())
        
        for i, dept1 in enumerate(departments):
            for dept2 in departments[i+1:]:
                similarity = similarity_matrix[dept1][dept2]
                
                if similarity >= threshold:
                    profile1 = department_profiles[dept1]
                    profile2 = department_profiles[dept2]
                    
                    skills1 = set(profile1["skills"])
                    skills2 = set(profile2["skills"])
                    
                    # Skills dept1 can learn from dept2
                    dept1_can_learn = skills2 - skills1
                    # Skills dept2 can learn from dept1
                    dept2_can_learn = skills1 - skills2
                    
                    if dept1_can_learn or dept2_can_learn:
                        opportunities.append({
                            "source_team": dept1,
                            "target_team": dept2,
                            "similarity_score": similarity,
                            "skills_to_transfer": {
                                f"{dept1}_to_{dept2}": list(dept2_can_learn)[:5],
                                f"{dept2}_to_{dept1}": list(dept1_can_learn)[:5]
                            },
                            "training_potential": "high" if similarity >= 0.4 else "medium",
                            "recommended_approach": "Mentorship program" if similarity >= 0.5 else "Workshop series"
                        })
        
        # Sort by similarity score
        opportunities.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return opportunities[:15]  # Top 15
