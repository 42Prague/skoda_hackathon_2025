"""
Promotion Readiness Service
---------------------------
Computes promotion readiness scores, gaps, timelines, and training recommendations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from swx_api.app.models.skoda_models import JobFamilyRecord, QualificationRecord
from swx_api.app.models.skill_models import EmployeeRecord, LearningHistory
from swx_api.core.middleware.logging_middleware import logger


class PromotionReadinessService:
    """Service for computing promotion readiness."""
    
    async def calculate_promotion_readiness(
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any],
        employee_record: EmployeeRecord,
        target_role: Optional[Dict[str, Any]] = None,
        target_job_family_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate promotion readiness for an employee.
        
        Args:
            session: Async database session
            employee_data: Employee data dict
            employee_record: EmployeeRecord object
            target_role: Optional target role requirements dict
            target_job_family_id: Optional target job family ID
            
        Returns:
            Dict with readiness_score, gaps, timeline, training_actions
        """
        employee_id = employee_data.get("employee_id")
        employee_skills = set(employee_data.get("skills") or [])
        employee_skills_lower = {s.lower() for s in employee_skills}
        
        # Get target role requirements
        target_requirements = await self._get_target_requirements(
            session,
            target_role,
            target_job_family_id,
            employee_record
        )
        
        if not target_requirements:
            # Use heuristic: assume next level requires 50% more skills
            target_requirements = {
                "required_skills": [],
                "preferred_skills": list(employee_skills)[:5],  # Assume need 5 more
                "required_qualifications": [],
                "preferred_qualifications": [],
            }
        
        # Get employee qualifications
        employee_quals = await self._get_employee_qualifications(session, employee_id)
        employee_qual_ids = {q.qualification_id for q in employee_quals}
        
        # Get employee learning history
        learning_history = await self._get_employee_learning_history(session, employee_id)
        
        # Calculate readiness components
        skills_readiness = self._calculate_skills_readiness(
            employee_skills_lower,
            target_requirements.get("required_skills", []),
            target_requirements.get("preferred_skills", [])
        )
        
        qualifications_readiness = self._calculate_qualifications_readiness(
            employee_qual_ids,
            target_requirements.get("required_qualifications", []),
            target_requirements.get("preferred_qualifications", [])
        )
        
        experience_readiness = self._calculate_experience_readiness(
            employee_data,
            employee_record,
            target_requirements
        )
        
        learning_readiness = self._calculate_learning_readiness(learning_history)
        
        # Weighted readiness score
        readiness_score = (
            skills_readiness["score"] * 0.40 +
            qualifications_readiness["score"] * 0.30 +
            experience_readiness["score"] * 0.20 +
            learning_readiness["score"] * 0.10
        )
        
        readiness_score = min(100, max(0, round(readiness_score, 2)))
        
        # Combine gaps
        missing_skills = skills_readiness["missing_skills"]
        missing_qualifications = qualifications_readiness["missing_qualifications"]
        
        # Estimate timeline
        timeline = self._estimate_readiness_timeline(
            readiness_score,
            missing_skills,
            missing_qualifications,
            learning_history
        )
        
        # Training recommendations
        training_actions = self._generate_training_actions(
            missing_skills,
            missing_qualifications,
            skills_readiness,
            qualifications_readiness
        )
        
        # Readiness level
        readiness_level = self._map_to_readiness_level(readiness_score)
        
        return {
            "readiness_score": readiness_score,
            "readiness_level": readiness_level,
            "readiness_components": {
                "skills": skills_readiness,
                "qualifications": qualifications_readiness,
                "experience": experience_readiness,
                "learning": learning_readiness,
            },
            "missing_skills": missing_skills,
            "missing_qualifications": missing_qualifications,
            "estimated_timeline": timeline,
            "training_actions": training_actions,
            "target_role": target_requirements.get("role_name", "Next Level"),
            "computed_at": datetime.utcnow().isoformat(),
        }
    
    async def get_team_promotion_candidates(
        self,
        session: AsyncSession,
        team_data: List[Dict[str, Any]],
        employee_records: List[EmployeeRecord],
        target_job_family_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get promotion readiness for all team members."""
        # Batch fetch all qualifications and learning history to avoid N+1 queries
        employee_ids = [emp.get("employee_id") for emp in team_data]
        all_qualifications = await self._get_team_qualifications(session, employee_ids)
        all_learning_history = await self._get_team_learning_history(session, employee_ids)
        
        # Group by employee_id for fast lookup
        quals_by_employee = {}
        for qual in all_qualifications:
            if qual.employee_id not in quals_by_employee:
                quals_by_employee[qual.employee_id] = []
            quals_by_employee[qual.employee_id].append(qual)
        
        learning_by_employee = {}
        for lh in all_learning_history:
            if lh.employee_id not in learning_by_employee:
                learning_by_employee[lh.employee_id] = []
            learning_by_employee[lh.employee_id].append(lh)
        
        candidates = []
        
        for emp_data, emp_record in zip(team_data, employee_records):
            emp_id = emp_data.get("employee_id")
            
            # Use batch-fetched data (override methods to use cached data)
            readiness = await self._calculate_readiness_with_cached_data(
                session,
                emp_data,
                emp_record,
                quals_by_employee.get(emp_id, []),
                learning_by_employee.get(emp_id, []),
                target_job_family_id
            )
            
            candidates.append({
                "employee_id": emp_id,
                "readiness_score": readiness["readiness_score"],
                "readiness_level": readiness["readiness_level"],
                "estimated_timeline": readiness["estimated_timeline"],
                "missing_skills_count": len(readiness["missing_skills"]),
                "missing_qualifications_count": len(readiness["missing_qualifications"]),
            })
        
        # Sort by readiness score (highest first)
        candidates.sort(key=lambda x: x["readiness_score"], reverse=True)
        
        # Team summary
        ready_now = sum(1 for c in candidates if c["readiness_score"] >= 80)
        ready_soon = sum(1 for c in candidates if 65 <= c["readiness_score"] < 80)
        developing = sum(1 for c in candidates if c["readiness_score"] < 65)
        
        return {
            "pipeline_summary": {
                "ready_now": ready_now,
                "ready_soon": ready_soon,
                "developing": developing,
                "total_candidates": len(candidates),
            },
            "candidates": candidates,
            "computed_at": datetime.utcnow().isoformat(),
        }
    
    async def _get_team_qualifications(
        self,
        session: AsyncSession,
        employee_ids: List[str]
    ) -> List[QualificationRecord]:
        """Batch fetch all qualifications for team."""
        if not employee_ids:
            return []
        statement = select(QualificationRecord).where(
            QualificationRecord.employee_id.in_(employee_ids)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def _get_team_learning_history(
        self,
        session: AsyncSession,
        employee_ids: List[str]
    ) -> List[LearningHistory]:
        """Batch fetch all learning history for team."""
        if not employee_ids:
            return []
        statement = select(LearningHistory).where(
            LearningHistory.employee_id.in_(employee_ids)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def _calculate_readiness_with_cached_data(
        self,
        session: AsyncSession,
        employee_data: Dict[str, Any],
        employee_record: EmployeeRecord,
        employee_quals: List[QualificationRecord],
        learning_history: List[LearningHistory],
        target_job_family_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate readiness using pre-fetched data (avoids N+1 queries)."""
        employee_id = employee_data.get("employee_id")
        employee_skills = set(employee_data.get("skills") or [])
        employee_skills_lower = {s.lower() for s in employee_skills}
        
        # Get target role requirements
        target_requirements = await self._get_target_requirements(
            session,
            None,
            target_job_family_id,
            employee_record
        )
        
        if not target_requirements:
            target_requirements = {
                "required_skills": [],
                "preferred_skills": list(employee_skills)[:5],
                "required_qualifications": [],
                "preferred_qualifications": [],
            }
        
        # Use pre-fetched qualifications
        employee_qual_ids = {q.qualification_id for q in employee_quals}
        
        # Calculate readiness components
        skills_readiness = self._calculate_skills_readiness(
            employee_skills_lower,
            target_requirements.get("required_skills", []),
            target_requirements.get("preferred_skills", [])
        )
        
        qualifications_readiness = self._calculate_qualifications_readiness(
            employee_qual_ids,
            target_requirements.get("required_qualifications", []),
            target_requirements.get("preferred_qualifications", [])
        )
        
        experience_readiness = self._calculate_experience_readiness(
            employee_data,
            employee_record,
            target_requirements
        )
        
        learning_readiness = self._calculate_learning_readiness(learning_history)
        
        # Weighted readiness score
        readiness_score = (
            skills_readiness["score"] * 0.40 +
            qualifications_readiness["score"] * 0.30 +
            experience_readiness["score"] * 0.20 +
            learning_readiness["score"] * 0.10
        )
        
        readiness_score = min(100, max(0, round(readiness_score, 2)))
        
        missing_skills = skills_readiness["missing_skills"]
        missing_qualifications = qualifications_readiness["missing_qualifications"]
        
        timeline = self._estimate_readiness_timeline(
            readiness_score,
            missing_skills,
            missing_qualifications,
            learning_history
        )
        
        training_actions = self._generate_training_actions(
            missing_skills,
            missing_qualifications,
            skills_readiness,
            qualifications_readiness
        )
        
        readiness_level = self._map_to_readiness_level(readiness_score)
        
        return {
            "readiness_score": readiness_score,
            "readiness_level": readiness_level,
            "missing_skills": missing_skills,
            "missing_qualifications": missing_qualifications,
            "estimated_timeline": timeline,
            "training_actions": training_actions,
        }
    
    async def _get_target_requirements(
        self,
        session: AsyncSession,
        target_role: Optional[Dict[str, Any]],
        target_job_family_id: Optional[str],
        employee_record: EmployeeRecord
    ) -> Optional[Dict[str, Any]]:
        """Get target role requirements."""
        if target_role:
            return target_role
        
        if target_job_family_id:
            statement = select(JobFamilyRecord).where(
                JobFamilyRecord.job_family_id == target_job_family_id
            )
            result = await session.execute(statement)
            job_family = result.scalars().first()
            
            if job_family:
                return {
                    "role_name": job_family.job_family_name_en or job_family.job_family_name_cz,
                    "required_skills": job_family.required_skills or [],
                    "preferred_skills": job_family.preferred_skills or [],
                    "required_qualifications": job_family.required_qualifications or [],
                }
        
        # Try to infer next level from current job family
        current_job_family_id = getattr(employee_record, "pers_job_family_id", None)
        if current_job_family_id:
            # Heuristic: assume next level has similar requirements + more
            # This would ideally use a hierarchy, but for hackathon, use current role requirements
            statement = select(JobFamilyRecord).where(
                JobFamilyRecord.job_family_id == current_job_family_id
            )
            result = await session.execute(statement)
            current_job_family = result.scalars().first()
            
            if current_job_family:
                return {
                    "role_name": f"Next Level ({current_job_family.job_family_name_en or current_job_family.job_family_name_cz})",
                    "required_skills": (current_job_family.required_skills or []) + ["Leadership", "Mentoring"],
                    "preferred_skills": (current_job_family.preferred_skills or []) + ["Architecture", "Design Patterns"],
                    "required_qualifications": current_job_family.required_qualifications or [],
                }
        
        return None
    
    async def _get_employee_qualifications(
        self,
        session: AsyncSession,
        employee_id: str
    ) -> List[QualificationRecord]:
        """Get employee qualifications."""
        statement = select(QualificationRecord).where(
            QualificationRecord.employee_id == employee_id
        )
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def _get_employee_learning_history(
        self,
        session: AsyncSession,
        employee_id: str
    ) -> List[LearningHistory]:
        """Get employee learning history."""
        statement = select(LearningHistory).where(
            LearningHistory.employee_id == employee_id
        )
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    def _calculate_skills_readiness(
        self,
        employee_skills_lower: set,
        required_skills: List[str],
        preferred_skills: List[str]
    ) -> Dict[str, Any]:
        """Calculate skills readiness component."""
        if not required_skills and not preferred_skills:
            return {
                "score": 70.0,  # Default if no requirements
                "missing_skills": [],
                "matched_skills": [],
            }
        
        required_matched = sum(
            1 for skill in required_skills
            if skill.lower() in employee_skills_lower
        )
        preferred_matched = sum(
            1 for skill in preferred_skills
            if skill.lower() in employee_skills_lower
        )
        
        required_score = (required_matched / len(required_skills) * 100) if required_skills else 100
        preferred_score = (preferred_matched / len(preferred_skills) * 50) if preferred_skills else 0
        
        # Weighted: required (70%) + preferred (30%)
        total_score = (required_score * 0.70) + (preferred_score * 0.30)
        
        missing_required = [s for s in required_skills if s.lower() not in employee_skills_lower]
        missing_preferred = [s for s in preferred_skills if s.lower() not in employee_skills_lower]
        missing_skills = missing_required + missing_preferred
        
        matched_skills = [
            s for s in (required_skills + preferred_skills)
            if s.lower() in employee_skills_lower
        ]
        
        return {
            "score": round(total_score, 2),
            "required_match": required_matched,
            "required_total": len(required_skills),
            "preferred_match": preferred_matched,
            "preferred_total": len(preferred_skills),
            "missing_skills": missing_skills,
            "matched_skills": matched_skills,
        }
    
    def _calculate_qualifications_readiness(
        self,
        employee_qual_ids: set,
        required_qualifications: List[str],
        preferred_qualifications: List[str]
    ) -> Dict[str, Any]:
        """Calculate qualifications readiness component."""
        if not required_qualifications and not preferred_qualifications:
            return {
                "score": 80.0,  # Default if no requirements
                "missing_qualifications": [],
                "matched_qualifications": [],
            }
        
        required_matched = sum(1 for qid in required_qualifications if qid in employee_qual_ids)
        preferred_matched = sum(1 for qid in preferred_qualifications if qid in employee_qual_ids)
        
        required_score = (required_matched / len(required_qualifications) * 100) if required_qualifications else 100
        preferred_score = (preferred_matched / len(preferred_qualifications) * 50) if preferred_qualifications else 0
        
        total_score = (required_score * 0.70) + (preferred_score * 0.30)
        
        missing_required = [qid for qid in required_qualifications if qid not in employee_qual_ids]
        missing_preferred = [qid for qid in preferred_qualifications if qid not in employee_qual_ids]
        missing_qualifications = missing_required + missing_preferred
        
        matched_qualifications = [
            qid for qid in (required_qualifications + preferred_qualifications)
            if qid in employee_qual_ids
        ]
        
        return {
            "score": round(total_score, 2),
            "required_match": required_matched,
            "required_total": len(required_qualifications),
            "preferred_match": preferred_matched,
            "preferred_total": len(preferred_qualifications),
            "missing_qualifications": missing_qualifications,
            "matched_qualifications": matched_qualifications,
        }
    
    def _calculate_experience_readiness(
        self,
        employee_data: Dict[str, Any],
        employee_record: EmployeeRecord,
        target_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate experience readiness component."""
        # Heuristic: estimate experience from metadata or use default
        # In production, this would use actual tenure/experience data
        metadata = employee_data.get("metadata", {}) or {}
        
        # Assume 3+ years = good experience (80 score)
        # 2-3 years = developing (60 score)
        # <2 years = beginner (40 score)
        estimated_experience_years = metadata.get("experience_years", 2.5)
        
        if estimated_experience_years >= 3:
            experience_score = 80
        elif estimated_experience_years >= 2:
            experience_score = 60
        else:
            experience_score = 40
        
        return {
            "score": float(experience_score),
            "estimated_years": estimated_experience_years,
        }
    
    def _calculate_learning_readiness(
        self,
        learning_history: List[LearningHistory]
    ) -> Dict[str, Any]:
        """Calculate learning readiness component."""
        # Recent learning activity (last 12 months) indicates readiness
        if not learning_history:
            return {
                "score": 50.0,
                "recent_courses": 0,
            }
        
        # Count courses in last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        recent_courses = sum(
            1 for lh in learning_history
            if lh.completion_status == "completed" and 
               lh.end_date and 
               lh.end_date >= twelve_months_ago
        )
        
        # Score based on recent learning (10+ courses = excellent)
        if recent_courses >= 10:
            learning_score = 90
        elif recent_courses >= 5:
            learning_score = 75
        elif recent_courses >= 2:
            learning_score = 60
        else:
            learning_score = 50
        
        return {
            "score": float(learning_score),
            "recent_courses": recent_courses,
            "total_courses": len(learning_history),
        }
    
    def _estimate_readiness_timeline(
        self,
        readiness_score: float,
        missing_skills: List[str],
        missing_qualifications: List[str],
        learning_history: List[LearningHistory]
    ) -> str:
        """Estimate timeline to readiness."""
        if readiness_score >= 80:
            return "Ready now"
        elif readiness_score >= 65:
            months = 3 + len(missing_skills) * 2
            return f"3-{months} months"
        elif readiness_score >= 50:
            months = 6 + len(missing_skills) * 3 + len(missing_qualifications) * 2
            return f"6-{min(18, months)} months"
        else:
            months = 12 + len(missing_skills) * 4 + len(missing_qualifications) * 3
            return f"12-{min(24, months)} months"
    
    def _generate_training_actions(
        self,
        missing_skills: List[str],
        missing_qualifications: List[str],
        skills_readiness: Dict[str, Any],
        qualifications_readiness: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate training action recommendations."""
        actions = []
        
        # Priority 1: Required skills
        for skill in missing_skills[:5]:  # Top 5
            actions.append({
                "priority": "high",
                "type": "skill_training",
                "action": f"Complete training in {skill}",
                "estimated_duration": "2-4 weeks",
            })
        
        # Priority 2: Required qualifications
        for qual_id in missing_qualifications[:3]:  # Top 3
            actions.append({
                "priority": "high",
                "type": "certification",
                "action": f"Obtain certification: {qual_id}",
                "estimated_duration": "1-3 months",
            })
        
        # Priority 3: Preferred skills
        if len(actions) < 5:
            preferred_missing = [
                s for s in missing_skills
                if s not in [a["action"].split()[-1] for a in actions if "skill" in a["type"]]
            ]
            for skill in preferred_missing[:3]:
                actions.append({
                    "priority": "medium",
                    "type": "skill_training",
                    "action": f"Develop skills in {skill}",
                    "estimated_duration": "4-8 weeks",
                })
        
        return actions[:8]  # Max 8 actions
    
    def _map_to_readiness_level(self, score: float) -> str:
        """Map readiness score to level."""
        if score >= 80:
            return "Ready Now"
        elif score >= 65:
            return "Ready Soon"
        elif score >= 50:
            return "Developing"
        else:
            return "Early Stage"

