"""
Team Capability Service
-----------------------
Computes team capability metrics: coverage, strength, capability vector, level.
"""

from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

from swx_api.core.middleware.logging_middleware import logger


class TeamCapabilityService:
    """Service for computing team capability metrics."""
    
    async def calculate_team_capability(
        self,
        team_data: List[Dict[str, Any]],
        job_family_requirements: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compute comprehensive team capability metrics.
        
        Args:
            team_data: List of employee data dicts with skills, department, etc.
            job_family_requirements: Optional dict mapping roles to required skills
            
        Returns:
            Dict with capability_score, capability_level, capability_vector, etc.
        """
        if not team_data:
            return self._empty_capability_response()
        
        # Extract all skills from team
        all_skills = []
        employee_skill_counts = []
        skill_frequency = Counter()
        
        for emp in team_data:
            skills = emp.get("skills", []) or []
            all_skills.extend(skills)
            employee_skill_counts.append(len(skills))
            skill_frequency.update(skills)
        
        total_employees = len(team_data)
        unique_skills = len(skill_frequency)
        
        # 1. Skill Coverage: % of employees with each skill
        skill_coverage = {
            skill: (count / total_employees * 100) 
            for skill, count in skill_frequency.items()
        }
        avg_coverage = sum(skill_coverage.values()) / len(skill_coverage) if skill_coverage else 0
        
        # 2. Skill Strength: average and max skills per employee
        avg_skills_per_employee = sum(employee_skill_counts) / total_employees if total_employees > 0 else 0
        max_skills_per_employee = max(employee_skill_counts) if employee_skill_counts else 0
        
        # 3. Capability Vector (6 dimensions)
        capability_vector = self._compute_capability_vector(
            skill_coverage,
            skill_frequency,
            total_employees,
            unique_skills,
            avg_skills_per_employee,
            job_family_requirements
        )
        
        # 4. Capability Score (0-100)
        capability_score = self._compute_capability_score(capability_vector)
        
        # 5. Capability Level (1-5)
        capability_level = self._map_to_capability_level(capability_score)
        capability_level_name = self._get_capability_level_name(capability_level)
        
        # 6. Top skills and gaps
        top_skills = [skill for skill, _ in skill_frequency.most_common(10)]
        critical_gaps = self._identify_critical_gaps(
            skill_coverage,
            job_family_requirements,
            total_employees
        )
        
        return {
            "capability_score": round(capability_score, 2),
            "capability_level": capability_level,
            "capability_level_name": capability_level_name,
            "capability_vector": capability_vector,
            "skill_coverage": skill_coverage,
            "avg_coverage": round(avg_coverage, 2),
            "skill_strength": {
                "avg_skills_per_employee": round(avg_skills_per_employee, 2),
                "max_skills_per_employee": max_skills_per_employee,
                "unique_skills_count": unique_skills,
            },
            "team_summary": {
                "total_employees": total_employees,
                "total_skills": len(all_skills),
                "unique_skills": unique_skills,
                "top_skills": top_skills,
                "critical_gaps": critical_gaps,
            },
            "computed_at": datetime.utcnow().isoformat(),
        }
    
    def _compute_capability_vector(
        self,
        skill_coverage: Dict[str, float],
        skill_frequency: Counter,
        total_employees: int,
        unique_skills: int,
        avg_skills_per_employee: float,
        job_family_requirements: Dict[str, List[str]] = None
    ) -> Dict[str, float]:
        """Compute 6-dimensional capability vector."""
        # Dimension 1: Skill Coverage (0-100)
        # skill_coverage already contains percentages (0-100 per skill)
        # Average them to get overall coverage percentage
        coverage_score = sum(skill_coverage.values()) / len(skill_coverage) if skill_coverage else 0
        coverage_score = min(100, max(0, coverage_score))
        
        # Dimension 2: Skill Diversity (0-100)
        # Normalize unique skills count (assume max 50 is excellent)
        diversity_score = min(100, (unique_skills / 50) * 100)
        
        # Dimension 3: Skill Depth (0-100)
        # Average skills per employee (assume 10+ is excellent)
        depth_score = min(100, (avg_skills_per_employee / 10) * 100)
        
        # Dimension 4: Skill Distribution (0-100)
        # Check if skills are well-distributed (not concentrated)
        if skill_frequency and total_employees > 0:
            max_concentration = max(skill_frequency.values()) / total_employees
            # Lower concentration = better distribution (100 = perfect distribution)
            distribution_score = max(0, 100 - (max_concentration * 100))
        else:
            distribution_score = 0
        
        # Dimension 5: Requirement Alignment (0-100)
        # If job family requirements provided, check alignment
        if job_family_requirements:
            alignment_score = self._compute_requirement_alignment(
                skill_coverage,
                job_family_requirements
            )
        else:
            # Default to diversity score if no requirements
            alignment_score = diversity_score
        
        # Dimension 6: Skill Maturity (0-100)
        # Based on skill coverage depth (skills with >50% coverage = mature)
        mature_skills = sum(1 for coverage in skill_coverage.values() if coverage >= 50)
        maturity_score = min(100, (mature_skills / max(1, unique_skills)) * 100) if unique_skills > 0 else 0
        
        return {
            "skill_coverage": round(coverage_score, 2),
            "skill_diversity": round(diversity_score, 2),
            "skill_depth": round(depth_score, 2),
            "skill_distribution": round(distribution_score, 2),
            "requirement_alignment": round(alignment_score, 2),
            "skill_maturity": round(maturity_score, 2),
        }
    
    def _compute_capability_score(self, capability_vector: Dict[str, float]) -> float:
        """Compute overall capability score from vector (weighted average)."""
        weights = {
            "skill_coverage": 0.25,
            "skill_diversity": 0.20,
            "skill_depth": 0.20,
            "skill_distribution": 0.15,
            "requirement_alignment": 0.15,
            "skill_maturity": 0.05,
        }
        
        weighted_sum = sum(
            capability_vector.get(dim, 0) * weight
            for dim, weight in weights.items()
        )
        
        return min(100, max(0, weighted_sum))
    
    def _map_to_capability_level(self, score: float) -> int:
        """Map capability score (0-100) to level (1-5)."""
        if score >= 90:
            return 5
        elif score >= 75:
            return 4
        elif score >= 60:
            return 3
        elif score >= 40:
            return 2
        else:
            return 1
    
    def _get_capability_level_name(self, level: int) -> str:
        """Get human-readable capability level name."""
        names = {
            1: "Beginner",
            2: "Developing",
            3: "Advanced",
            4: "Expert",
            5: "Master",
        }
        return names.get(level, "Unknown")
    
    def _compute_requirement_alignment(
        self,
        skill_coverage: Dict[str, float],
        job_family_requirements: Dict[str, List[str]]
    ) -> float:
        """Compute alignment with job family requirements."""
        all_required_skills = set()
        for required_skills in job_family_requirements.values():
            all_required_skills.update(required_skills)
        
        if not all_required_skills:
            return 50.0  # Default if no requirements
        
        covered_required = sum(
            1 for skill in all_required_skills
            if skill.lower() in [s.lower() for s in skill_coverage.keys()]
        )
        
        alignment_percentage = (covered_required / len(all_required_skills)) * 100
        return min(100, max(0, alignment_percentage))
    
    def _identify_critical_gaps(
        self,
        skill_coverage: Dict[str, float],
        job_family_requirements: Dict[str, List[str]] = None,
        total_employees: int = 0
    ) -> List[str]:
        """Identify critical skill gaps."""
        gaps = []
        
        # Gaps: skills with low coverage (<20%)
        for skill, coverage in skill_coverage.items():
            if coverage < 20:
                gaps.append(f"{skill} (only {coverage:.1f}% coverage)")
        
        # Missing required skills
        if job_family_requirements:
            all_required = set()
            for required_skills in job_family_requirements.values():
                all_required.update(required_skills)
            
            covered_skills_lower = {s.lower() for s in skill_coverage.keys()}
            missing_required = [
                skill for skill in all_required
                if skill.lower() not in covered_skills_lower
            ]
            gaps.extend(missing_required)
        
        return gaps[:10]  # Top 10 gaps
    
    def _empty_capability_response(self) -> Dict[str, Any]:
        """Return empty capability response."""
        return {
            "capability_score": 0.0,
            "capability_level": 1,
            "capability_level_name": "Beginner",
            "capability_vector": {
                "skill_coverage": 0.0,
                "skill_diversity": 0.0,
                "skill_depth": 0.0,
                "skill_distribution": 0.0,
                "requirement_alignment": 0.0,
                "skill_maturity": 0.0,
            },
            "skill_coverage": {},
            "avg_coverage": 0.0,
            "skill_strength": {
                "avg_skills_per_employee": 0.0,
                "max_skills_per_employee": 0,
                "unique_skills_count": 0,
            },
            "team_summary": {
                "total_employees": 0,
                "total_skills": 0,
                "unique_skills": 0,
                "top_skills": [],
                "critical_gaps": [],
            },
            "computed_at": datetime.utcnow().isoformat(),
        }

