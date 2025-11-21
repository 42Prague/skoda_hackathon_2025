"""
Career Path Service
-------------------
Using Azure OpenAI + employee skills/qualifications to predict career paths.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from swx_api.app.models.skoda_models import JobFamilyRecord, QualificationRecord
from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.services.ai_orchestrator import AIOrchestrator
from swx_api.core.middleware.logging_middleware import logger


class CareerPathService:
    """Service for generating career paths using AI."""
    
    def __init__(self):
        self.orchestrator = AIOrchestrator()
    
    async def generate_career_path(
        self,
        session: AsyncSession,
        employee_id: str,
        employee_data: Dict[str, Any],
        employee_record: EmployeeRecord
    ) -> Dict[str, Any]:
        """
        Generate career path for employee using Azure AI.
        
        Args:
            session: Async database session
            employee_id: Employee ID
            employee_data: Employee data dict
            employee_record: EmployeeRecord object
            
        Returns:
            Dict with top 3 roles, readiness, gaps, training, timeline
        """
        # Get all job families for context
        job_families = await self._get_all_job_families(session)
        
        # Prepare employee context
        employee_skills = employee_data.get("skills", []) or []
        employee_department = employee_data.get("department", "Unknown")
        current_role = getattr(employee_record, "pers_job_family_id", None) or "Unknown"
        
        # Get employee qualifications (from database, not metadata)
        qual_statement = select(QualificationRecord).where(
            QualificationRecord.employee_id == employee_id
        )
        qual_result = await session.execute(qual_statement)
        employee_quals = list(qual_result.scalars().all())
        qualification_ids = [q.qualification_id for q in employee_quals]
        
        # Use AI to predict top 3 roles
        try:
            ai_result = await self.orchestrator.run(
                prompt_name="career_path",
                variables={
                    "employee_id": employee_id,
                    "current_role": current_role,
                    "current_department": employee_department,
                    "skills": employee_skills,
                    "qualifications": qualification_ids,  # Use actual qualification IDs
                    "job_families": [
                        {
                            "id": jf.job_family_id,
                            "name": jf.job_family_name_en or jf.job_family_name_cz,
                            "required_skills": jf.required_skills or [],
                            "preferred_skills": jf.preferred_skills or [],
                        }
                        for jf in job_families[:20]  # Limit to 20 for prompt size
                    ],
                },
                schema={
                    "top_roles": list,  # List of {role_name, readiness_percentage, skill_gaps, required_trainings, timeline}
                    "career_insights": str,
                },
                max_completion_tokens=2048,
            )
            
            # Extract AI-generated roles
            ai_roles = ai_result.get("top_roles", [])
            
            # Enrich with actual job family data
            enriched_roles = []
            for ai_role in ai_roles[:3]:  # Top 3 only
                role_name = ai_role.get("role_name", "Unknown")
                readiness_pct = ai_role.get("readiness_percentage", 50)
                skill_gaps = ai_role.get("skill_gaps", [])
                required_trainings = ai_role.get("required_trainings", [])
                timeline = ai_role.get("timeline", "12-18 months")
                
                # Find matching job family
                matching_jf = None
                for jf in job_families:
                    if role_name.lower() in (jf.job_family_name_en or "").lower() or \
                       role_name.lower() in (jf.job_family_name_cz or "").lower():
                        matching_jf = jf
                        break
                
                enriched_roles.append({
                    "role_name": role_name,
                    "job_family_id": matching_jf.job_family_id if matching_jf else None,
                    "readiness_percentage": readiness_pct,
                    "readiness_level": self._map_readiness_level(readiness_pct),
                    "skill_gaps": skill_gaps,
                    "required_trainings": required_trainings,
                    "timeline_to_reach": timeline,
                    "path_step": len(enriched_roles) + 1,  # Step 1, 2, 3
                })
            
            # If AI failed or returned empty, use fallback
            if not enriched_roles:
                enriched_roles = self._fallback_career_path(employee_skills, job_families)
            
            # Ensure exactly 3 roles (pad if needed)
            while len(enriched_roles) < 3:
                idx = len(enriched_roles) + 1
                enriched_roles.append({
                    "role_name": f"Career Path Option {idx}",
                    "job_family_id": None,
                    "readiness_percentage": 50.0 - (idx * 5),
                    "readiness_level": "Developing",
                    "skill_gaps": ["Skill development needed"],
                    "required_trainings": ["Professional development course"],
                    "timeline_to_reach": f"{6 + idx * 6}-{12 + idx * 6} months",
                    "path_step": idx,
                })
            
            return {
                "employee_id": employee_id,
                "current_role": current_role,
                "career_paths": enriched_roles[:3],  # Always exactly 3
                "career_insights": ai_result.get("career_insights", "Generated career path recommendations"),
                "computed_at": datetime.utcnow().isoformat(),
                "ai_generated": True,
            }
            
        except Exception as exc:
            logger.error(f"Career path AI generation failed: {exc}", exc_info=True)
            # Fallback to heuristic
            fallback_paths = self._fallback_career_path(employee_skills, job_families)
            # Ensure exactly 3 roles
            while len(fallback_paths) < 3:
                idx = len(fallback_paths) + 1
                fallback_paths.append({
                    "role_name": f"Career Path Option {idx}",
                    "job_family_id": None,
                    "readiness_percentage": 50.0 - (idx * 5),
                    "readiness_level": "Developing",
                    "skill_gaps": ["Skill development needed"],
                    "required_trainings": ["Professional development course"],
                    "timeline_to_reach": f"{6 + idx * 6}-{12 + idx * 6} months",
                    "path_step": idx,
                })
            return {
                "employee_id": employee_id,
                "current_role": current_role,
                "career_paths": fallback_paths[:3],  # Always exactly 3
                "career_insights": "Career path generated using heuristic analysis",
                "computed_at": datetime.utcnow().isoformat(),
                "ai_generated": False,
            }
    
    async def _get_all_job_families(self, session: AsyncSession) -> List[JobFamilyRecord]:
        """Get all job family records."""
        statement = select(JobFamilyRecord)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    def _fallback_career_path(
        self,
        employee_skills: List[str],
        job_families: List[JobFamilyRecord]
    ) -> List[Dict[str, Any]]:
        """Fallback career path using heuristics if AI fails."""
        employee_skills_lower = {s.lower() for s in employee_skills}
        
        # Score job families by skill match
        scored_roles = []
        for jf in job_families[:20]:  # Limit to 20
            required = jf.required_skills or []
            preferred = jf.preferred_skills or []
            
            required_match = sum(
                1 for skill in required
                if skill.lower() in employee_skills_lower
            )
            preferred_match = sum(
                1 for skill in preferred
                if skill.lower() in employee_skills_lower
            )
            
            required_score = (required_match / len(required) * 100) if required else 0
            preferred_score = (preferred_match / len(preferred) * 50) if preferred else 0
            total_score = (required_score * 0.70) + (preferred_score * 0.30)
            
            missing_skills = [
                skill for skill in required
                if skill.lower() not in employee_skills_lower
            ]
            
            scored_roles.append({
                "job_family": jf,
                "score": total_score,
                "missing_skills": missing_skills,
            })
        
        # Sort by score and take top 3 (deterministic - always same order for same input)
        scored_roles.sort(key=lambda x: (x["score"], x["job_family"].job_family_id), reverse=True)
        
        paths = []
        for idx, sr in enumerate(scored_roles[:3], 1):
            jf = sr["job_family"]
            readiness = min(95, sr["score"] + 10)  # Add 10% for optimism
            missing = sr["missing_skills"][:5]  # Top 5 missing
            
            paths.append({
                "role_name": jf.job_family_name_en or jf.job_family_name_cz,
                "job_family_id": jf.job_family_id,
                "readiness_percentage": round(readiness, 2),
                "readiness_level": self._map_readiness_level(readiness),
                "skill_gaps": missing,
                "required_trainings": [f"{s} training course" for s in missing[:3]],
                "timeline_to_reach": f"{6 + idx * 6}-{12 + idx * 6} months",
                "path_step": idx,
            })
        
        # Guarantee at least 3 roles (pad with generic if needed)
        while len(paths) < 3:
            idx = len(paths) + 1
            paths.append({
                "role_name": f"Career Path Option {idx}",
                "job_family_id": None,
                "readiness_percentage": 50.0 - (idx * 5),
                "readiness_level": "Developing",
                "skill_gaps": ["Skill development needed"],
                "required_trainings": ["Professional development course"],
                "timeline_to_reach": f"{6 + idx * 6}-{12 + idx * 6} months",
                "path_step": idx,
            })
        
        return paths[:3]  # Always return exactly 3
    
    def _map_readiness_level(self, percentage: float) -> str:
        """Map readiness percentage to level."""
        if percentage >= 80:
            return "Ready Soon"
        elif percentage >= 60:
            return "Developing"
        elif percentage >= 40:
            return "Early Stage"
        else:
            return "Long Term"

