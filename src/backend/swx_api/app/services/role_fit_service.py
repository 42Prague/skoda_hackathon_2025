"""
Async Team Fit / Role Fit Matching Engine
------------------------------------------
Computes fit scores between employees and roles, identifies gaps,
and suggests training paths using async LLM.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from swx_api.app.services.llm_client import LLMClient, LLMConfig
from swx_api.app.services.ai.ai_role_fit_service import AIRoleFitService
from swx_api.core.middleware.logging_middleware import logger

logger = logging.getLogger("role_fit")


class RoleFitService:
    """Async service for matching employees to roles."""
    
    def __init__(self):
        self.llm_config = LLMConfig.from_env()
        self.ai_role_fit_service = AIRoleFitService()
    
    def compute_role_fit(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any],
        skill_importance: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Compute fit score between employee and role (sync/async compatible).
        
        Can be called from sync or async contexts. In sync contexts, automatically
        runs the async implementation.
        """
        try:
            import asyncio
            loop = asyncio.get_running_loop()
            raise RuntimeError("Cannot call sync wrapper from async context - use await compute_role_fit_async()")
        except RuntimeError as e:
            if "Cannot call sync wrapper" in str(e):
                raise
            # No event loop running, run in sync mode
            import asyncio
            return asyncio.run(self._compute_role_fit_async(employee_profile, role_definition, skill_importance))

    async def compute_role_fit_async(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any],
        skill_importance: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Async version of compute_role_fit - use this in async contexts."""
        return await self._compute_role_fit_async(employee_profile, role_definition, skill_importance)

    async def _compute_role_fit_async(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any],
        skill_importance: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Compute fit score between employee and role.
        
        Args:
            employee_profile: Employee data with skills, experience, etc.
            role_definition: Role requirements with mandatory/preferred skills
            skill_importance: Optional skill importance weights (0-1)
            
        Returns:
            Dictionary with:
            - fit_score: Overall fit score (0-100)
            - missing_mandatory_skills: List of missing mandatory skills
            - missing_preferred_skills: List of missing preferred skills
            - suggested_training: List of training recommendations
            - readiness_level: "ready" | "almost-ready" | "not-ready"
            - detailed_analysis: Detailed breakdown
        """
        try:
            # Extract requirements
            mandatory_skills = role_definition.get("mandatory_skills", [])
            preferred_skills = role_definition.get("preferred_skills", [])
            employee_skills = employee_profile.get("skills", [])
            
            # Compute skill matches
            mandatory_matches = self._match_skills(employee_skills, mandatory_skills)
            preferred_matches = self._match_skills(employee_skills, preferred_skills)
            
            # Calculate fit score
            fit_score = self._calculate_fit_score(
                mandatory_matches,
                preferred_matches,
                mandatory_skills,
                preferred_skills,
                skill_importance
            )
            
            # Identify missing skills
            missing_mandatory = [s for s in mandatory_skills if s not in mandatory_matches["matched"]]
            missing_preferred = [s for s in preferred_skills if s not in preferred_matches["matched"]]
            
            # Determine readiness level
            readiness_level = self._determine_readiness(fit_score, missing_mandatory)
            
            # Generate training suggestions
            suggested_training = self._generate_training_suggestions(
                missing_mandatory,
                missing_preferred,
                employee_profile,
                role_definition
            )
            
            # Get AI-powered detailed analysis (async)
            detailed_analysis = await self._get_detailed_analysis(
                employee_profile,
                role_definition,
                fit_score,
                missing_mandatory,
                missing_preferred
            )
            
            return {
                "fit_score": fit_score,
                "missing_mandatory_skills": missing_mandatory,
                "missing_preferred_skills": missing_preferred,
                "suggested_training": suggested_training,
                "readiness_level": readiness_level,
                "detailed_analysis": detailed_analysis,
                "matched_mandatory_skills": mandatory_matches["matched"],
                "matched_preferred_skills": preferred_matches["matched"],
                "analyzed_at": "Role fit analysis completed",
            }
            
        except Exception as e:
            logger.error(f"Error computing role fit: {e}", exc_info=True)
            return self._fallback_role_fit(employee_profile, role_definition)
    
    def _match_skills(
        self,
        employee_skills: List[str],
        required_skills: List[str]
    ) -> Dict[str, Any]:
        """Match employee skills to required skills."""
        employee_skills_lower = [s.lower() for s in employee_skills]
        required_skills_lower = [s.lower() for s in required_skills]
        
        matched = []
        partial_matches = []
        
        for req_skill in required_skills:
            req_lower = req_skill.lower()
            
            # Exact match
            if req_lower in employee_skills_lower:
                matched.append(req_skill)
            else:
                # Partial match (substring)
                for emp_skill in employee_skills:
                    if req_lower in emp_skill.lower() or emp_skill.lower() in req_lower:
                        partial_matches.append({
                            "required": req_skill,
                            "employee_skill": emp_skill,
                            "match_type": "partial"
                        })
                        break
        
        return {
            "matched": matched,
            "partial_matches": partial_matches,
            "match_count": len(matched),
            "match_rate": len(matched) / len(required_skills) if required_skills else 0
        }
    
    def _calculate_fit_score(
        self,
        mandatory_matches: Dict[str, Any],
        preferred_matches: Dict[str, Any],
        mandatory_skills: List[str],
        preferred_skills: List[str],
        skill_importance: Optional[Dict[str, float]] = None
    ) -> int:
        """Calculate overall fit score (0-100)."""
        if not mandatory_skills and not preferred_skills:
            return 50  # Neutral score if no requirements
        
        # Weight: mandatory skills 70%, preferred skills 30%
        mandatory_weight = 0.7
        preferred_weight = 0.3
        
        # Calculate mandatory score
        mandatory_score = mandatory_matches["match_rate"] * 100
        
        # Calculate preferred score
        preferred_score = preferred_matches["match_rate"] * 100 if preferred_skills else 100
        
        # Apply skill importance weights if provided
        if skill_importance:
            mandatory_weighted = 0
            mandatory_total = 0
            for skill in mandatory_skills:
                weight = skill_importance.get(skill, 1.0)
                if skill in mandatory_matches["matched"]:
                    mandatory_weighted += weight
                mandatory_total += weight
            
            if mandatory_total > 0:
                mandatory_score = (mandatory_weighted / mandatory_total) * 100
        
        # Combine scores
        fit_score = (mandatory_score * mandatory_weight) + (preferred_score * preferred_weight)
        
        # Round to integer
        return int(round(fit_score))
    
    def _determine_readiness(
        self,
        fit_score: int,
        missing_mandatory: List[str]
    ) -> str:
        """Determine readiness level."""
        if missing_mandatory:
            if fit_score >= 80:
                return "almost-ready"
            else:
                return "not-ready"
        else:
            if fit_score >= 90:
                return "ready"
            elif fit_score >= 70:
                return "almost-ready"
            else:
                return "not-ready"
    
    def _generate_training_suggestions(
        self,
        missing_mandatory: List[str],
        missing_preferred: List[str],
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate training recommendations."""
        suggestions = []
        
        # Priority: missing mandatory skills
        for skill in missing_mandatory[:5]:  # Top 5
            suggestions.append({
                "skill": skill,
                "priority": "high",
                "type": "mandatory",
                "recommended_courses": self._suggest_courses(skill),
                "estimated_duration": "4-8 weeks",
                "reason": f"Required for role: {role_definition.get('role_name', 'target role')}"
            })
        
        # Secondary: missing preferred skills
        for skill in missing_preferred[:3]:  # Top 3
            suggestions.append({
                "skill": skill,
                "priority": "medium",
                "type": "preferred",
                "recommended_courses": self._suggest_courses(skill),
                "estimated_duration": "2-4 weeks",
                "reason": "Would enhance role performance"
            })
        
        return suggestions
    
    def _suggest_courses(self, skill: str) -> List[str]:
        """Suggest courses for a skill (placeholder - can be enhanced with course database)."""
        # Simple mapping
        course_map = {
            "python": ["Python Fundamentals", "Advanced Python", "Python for Data Science"],
            "javascript": ["JavaScript Basics", "Modern JavaScript", "React Development"],
            "sql": ["SQL Fundamentals", "Advanced SQL", "Database Design"],
            "docker": ["Docker Basics", "Container Orchestration", "DevOps with Docker"],
        }
        
        skill_lower = skill.lower()
        for key, courses in course_map.items():
            if key in skill_lower:
                return courses
        
        return [f"{skill} Fundamentals", f"Advanced {skill}"]
    
    async def _get_detailed_analysis(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any],
        fit_score: int,
        missing_mandatory: List[str],
        missing_preferred: List[str]
    ) -> Dict[str, Any]:
        """Get AI-powered detailed analysis with async support."""
        try:
            prompt = self._build_analysis_prompt(
                employee_profile,
                role_definition,
                fit_score,
                missing_mandatory,
                missing_preferred
            )
            
            schema = {
                "summary": str,
                "strengths": list,
                "gaps": list,
                "recommendations": list,
                "career_path": str
            }
            
            # Use async LLM client
            async with LLMClient(self.llm_config) as llm:
                result = await llm.call_llm(
                    prompt=prompt,
                    schema=schema,
                    system_message="You are an expert HR and career development analyst.",
                    temperature=0.7,
                    max_tokens=1500
                )
            
            return result
        except Exception as e:
            logger.warning(f"AI analysis failed: {e}")
        
        # Fallback analysis
        return {
            "summary": f"Fit score: {fit_score}/100. {'Ready' if fit_score >= 90 else 'Needs training'}.",
            "strengths": employee_profile.get("skills", [])[:3],
            "gaps": missing_mandatory[:3],
            "recommendations": [f"Focus on learning {skill}" for skill in missing_mandatory[:3]],
            "career_path": "Focus on acquiring missing mandatory skills"
        }
    
    def _build_analysis_prompt(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any],
        fit_score: int,
        missing_mandatory: List[str],
        missing_preferred: List[str]
    ) -> str:
        """Build prompt for detailed analysis."""
        return f"""Analyze the fit between an employee and a role.

Employee Profile:
- Skills: {', '.join(employee_profile.get('skills', []))}
- Department: {employee_profile.get('department', 'Unknown')}
- Experience: {employee_profile.get('experience_years', 'Unknown')} years

Role Requirements:
- Role: {role_definition.get('role_name', 'Target Role')}
- Mandatory Skills: {', '.join(role_definition.get('mandatory_skills', []))}
- Preferred Skills: {', '.join(role_definition.get('preferred_skills', []))}

Current Fit Score: {fit_score}/100
Missing Mandatory Skills: {', '.join(missing_mandatory)}
Missing Preferred Skills: {', '.join(missing_preferred)}

Provide a detailed analysis with:
{{
  "summary": "brief summary of fit",
  "strengths": ["key strengths"],
  "gaps": ["key gaps"],
  "recommendations": ["actionable recommendations"],
  "career_path": "suggested career development path"
}}

Response (JSON only):"""
    
    def _fallback_role_fit(
        self,
        employee_profile: Dict[str, Any],
        role_definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback role fit when main method fails."""
        employee_skills = employee_profile.get("skills", [])
        mandatory_skills = role_definition.get("mandatory_skills", [])
        preferred_skills = role_definition.get("preferred_skills", [])
        
        mandatory_matches = self._match_skills(employee_skills, mandatory_skills)
        preferred_matches = self._match_skills(employee_skills, preferred_skills)
        
        fit_score = self._calculate_fit_score(
            mandatory_matches,
            preferred_matches,
            mandatory_skills,
            preferred_skills
        )
        
        missing_mandatory = [s for s in mandatory_skills if s not in mandatory_matches["matched"]]
        missing_preferred = [s for s in preferred_skills if s not in preferred_matches["matched"]]
        
        readiness_level = self._determine_readiness(fit_score, missing_mandatory)
        
        return {
            "fit_score": fit_score,
            "missing_mandatory_skills": missing_mandatory,
            "missing_preferred_skills": missing_preferred,
            "suggested_training": self._generate_training_suggestions(
                missing_mandatory,
                missing_preferred,
                employee_profile,
                role_definition
            ),
            "readiness_level": readiness_level,
            "detailed_analysis": {
                "summary": f"Basic fit analysis: {fit_score}/100",
                "strengths": employee_skills[:3],
                "gaps": missing_mandatory[:3],
                "recommendations": [f"Learn {skill}" for skill in missing_mandatory[:3]]
            },
            "fallback": True
        }
