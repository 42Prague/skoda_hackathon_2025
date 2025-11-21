"""
Risk Radar Service
------------------
Detects risks: expired certifications, expiring certifications, missing training, skill gaps.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from swx_api.app.models.skoda_models import QualificationRecord
from swx_api.app.models.skill_models import EmployeeRecord
from swx_api.app.models.skoda_models import JobFamilyRecord
from swx_api.core.middleware.logging_middleware import logger


class RiskRadarService:
    """Service for detecting and scoring risks."""
    
    async def scan_team_risks(
        self,
        session: AsyncSession,
        team_data: List[Dict[str, Any]],
        employee_records: List[EmployeeRecord]
    ) -> Dict[str, Any]:
        """
        Scan team for all risks: expired certs, expiring certs, missing training, skill gaps.
        
        Args:
            session: Async database session
            team_data: List of employee data dicts
            employee_records: List of EmployeeRecord objects
            
        Returns:
            Dict with risk_summary, risk_distribution, alerts, etc.
        """
        employee_ids = [emp.get("employee_id") for emp in team_data]
        
        # Get all qualifications for team members
        qualifications = await self._get_team_qualifications(session, employee_ids)
        
        # Get job family requirements for skill gap checking
        job_families = await self._get_job_families(session)
        
        # Scan risks per employee
        employee_risks = []
        all_alerts = []
        
        for emp_data, emp_record in zip(team_data, employee_records):
            emp_id = emp_data.get("employee_id")
            emp_quals = [q for q in qualifications if q.employee_id == emp_id]
            
            # Check qualification risks
            cert_risks = self._check_certification_risks(emp_quals)
            
            # Check skill gap risks (pass qualifications)
            skill_risks = self._check_skill_gap_risks(
                emp_data,
                emp_record,
                job_families,
                emp_quals  # Pass fetched qualifications
            )
            
            # Combine risks
            all_emp_risks = cert_risks + skill_risks
            
            # Calculate employee risk score (0-100, higher = more risk)
            risk_score = self._calculate_employee_risk_score(all_emp_risks)
            
            employee_risks.append({
                "employee_id": emp_id,
                "risk_score": risk_score,
                "risk_count": len(all_emp_risks),
                "critical_count": sum(1 for r in all_emp_risks if r.get("severity") == "critical"),
                "high_count": sum(1 for r in all_emp_risks if r.get("severity") == "high"),
                "medium_count": sum(1 for r in all_emp_risks if r.get("severity") == "medium"),
                "alerts": all_emp_risks,
            })
            
            all_alerts.extend(all_emp_risks)
        
        # Team risk summary
        risk_summary = self._compute_risk_summary(employee_risks, all_alerts)
        
        # Risk distribution
        risk_distribution = self._compute_risk_distribution(employee_risks)
        
        # Ensure risk_distribution always has all severity levels (even if 0)
        if "critical" not in risk_distribution:
            risk_distribution["critical"] = 0
        if "high" not in risk_distribution:
            risk_distribution["high"] = 0
        if "medium" not in risk_distribution:
            risk_distribution["medium"] = 0
        if "low" not in risk_distribution:
            risk_distribution["low"] = 0
        
        # Ensure risk_summary has all required fields
        if "risk_level" not in risk_summary:
            risk_summary["risk_level"] = "low"
        if "critical_alerts_count" not in risk_summary:
            risk_summary["critical_alerts_count"] = 0
        if "high_alerts_count" not in risk_summary:
            risk_summary["high_alerts_count"] = 0
        if "medium_alerts_count" not in risk_summary:
            risk_summary["medium_alerts_count"] = 0
        
        return {
            "risk_summary": risk_summary,
            "risk_distribution": risk_distribution,
            "employee_risks": employee_risks,
            "total_alerts": len(all_alerts),
            "critical_alerts": [a for a in all_alerts if a.get("severity") == "critical"],
            "high_alerts": [a for a in all_alerts if a.get("severity") == "high"],
            "computed_at": datetime.utcnow().isoformat(),
        }
    
    async def _get_team_qualifications(
        self,
        session: AsyncSession,
        employee_ids: List[str]
    ) -> List[QualificationRecord]:
        """Get all qualifications for team members."""
        if not employee_ids:
            return []
        
        statement = select(QualificationRecord).where(
            QualificationRecord.employee_id.in_(employee_ids)
        )
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    async def _get_job_families(self, session: AsyncSession) -> List[JobFamilyRecord]:
        """Get all job family records."""
        statement = select(JobFamilyRecord)
        result = await session.execute(statement)
        return list(result.scalars().all())
    
    def _check_certification_risks(
        self,
        qualifications: List[QualificationRecord]
    ) -> List[Dict[str, Any]]:
        """Check for expired/expiring certifications."""
        risks = []
        today = datetime.utcnow().date()
        
        for qual in qualifications:
            if not qual.expiry_date:
                continue
            
            expiry_date = qual.expiry_date.date() if isinstance(qual.expiry_date, datetime) else qual.expiry_date
            days_until_expiry = (expiry_date - today).days
            
            # Expired
            if days_until_expiry < 0:
                risks.append({
                    "type": "expired_certification",
                    "severity": "critical",
                    "employee_id": qual.employee_id,
                    "qualification_id": qual.qualification_id,
                    "qualification_name": qual.qualification_name_en or qual.qualification_name_cz,
                    "expiry_date": expiry_date.isoformat(),
                    "days_overdue": abs(days_until_expiry),
                    "message": f"Certification '{qual.qualification_name_en or qual.qualification_name_cz}' expired {abs(days_until_expiry)} days ago",
                })
            
            # Expiring soon (within 30 days)
            elif days_until_expiry <= 30:
                risks.append({
                    "type": "expiring_certification",
                    "severity": "high",
                    "employee_id": qual.employee_id,
                    "qualification_id": qual.qualification_id,
                    "qualification_name": qual.qualification_name_en or qual.qualification_name_cz,
                    "expiry_date": expiry_date.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "message": f"Certification '{qual.qualification_name_en or qual.qualification_name_cz}' expires in {days_until_expiry} days",
                })
            
            # Expiring soon (31-90 days)
            elif days_until_expiry <= 90:
                risks.append({
                    "type": "expiring_certification",
                    "severity": "medium",
                    "employee_id": qual.employee_id,
                    "qualification_id": qual.qualification_id,
                    "qualification_name": qual.qualification_name_en or qual.qualification_name_cz,
                    "expiry_date": expiry_date.isoformat(),
                    "days_until_expiry": days_until_expiry,
                    "message": f"Certification '{qual.qualification_name_en or qual.qualification_name_cz}' expires in {days_until_expiry} days",
                })
        
        return risks
    
    def _check_skill_gap_risks(
        self,
        emp_data: Dict[str, Any],
        emp_record: EmployeeRecord,
        job_families: List[JobFamilyRecord],
        emp_quals: List[QualificationRecord]
    ) -> List[Dict[str, Any]]:
        """Check for skill gaps vs role requirements."""
        risks = []
        employee_id = emp_data.get("employee_id")
        employee_skills = set((emp_data.get("skills") or []))
        employee_skills_lower = {s.lower() for s in employee_skills}
        
        # Get employee's job family
        job_family_id = getattr(emp_record, "pers_job_family_id", None)
        
        # Find matching job family
        matching_job_family = None
        for jf in job_families:
            if jf.job_family_id == job_family_id:
                matching_job_family = jf
                break
        
        if not matching_job_family:
            return risks  # No job family match, can't check gaps
        
        # Check required skills
        required_skills = matching_job_family.required_skills or []
        missing_required = [
            skill for skill in required_skills
            if skill.lower() not in employee_skills_lower
        ]
        
        if missing_required:
            risks.append({
                "type": "missing_required_skills",
                "severity": "high",
                "employee_id": employee_id,
                "job_family": matching_job_family.job_family_name_en or matching_job_family.job_family_name_cz,
                "missing_skills": missing_required,
                "message": f"Missing {len(missing_required)} required skills for role: {', '.join(missing_required[:3])}",
            })
        
        # Check mandatory qualifications (use fetched qualifications)
        required_quals = matching_job_family.required_qualifications or []
        if required_quals:
            # Get employee qualification IDs from fetched qualifications
            emp_qual_ids = {q.qualification_id for q in emp_quals}
            
            missing_quals = [
                qual_id for qual_id in required_quals
                if qual_id not in emp_qual_ids
            ]
            
            if missing_quals:
                risks.append({
                    "type": "missing_mandatory_qualification",
                    "severity": "high",
                    "employee_id": employee_id,
                    "job_family": matching_job_family.job_family_name_en or matching_job_family.job_family_name_cz,
                    "missing_qualifications": missing_quals,
                    "message": f"Missing {len(missing_quals)} mandatory qualifications",
                })
        
        return risks
    
    def _calculate_employee_risk_score(self, risks: List[Dict[str, Any]]) -> int:
        """Calculate employee risk score (0-100, higher = more risk)."""
        if not risks:
            return 0
        
        # Weighted risk score
        severity_weights = {
            "critical": 40,
            "high": 25,
            "medium": 10,
            "low": 5,
        }
        
        total_score = sum(
            severity_weights.get(r.get("severity", "low"), 5)
            for r in risks
        )
        
        # Cap at 100
        return min(100, total_score)
    
    def _compute_risk_summary(
        self,
        employee_risks: List[Dict[str, Any]],
        all_alerts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Compute team risk summary."""
        total_employees = len(employee_risks)
        employees_with_risks = sum(1 for er in employee_risks if er["risk_score"] > 0)
        
        critical_count = sum(1 for a in all_alerts if a.get("severity") == "critical")
        high_count = sum(1 for a in all_alerts if a.get("severity") == "high")
        medium_count = sum(1 for a in all_alerts if a.get("severity") == "medium")
        
        avg_risk_score = (
            sum(er["risk_score"] for er in employee_risks) / total_employees
            if total_employees > 0 else 0
        )
        
        # Team risk level
        if avg_risk_score >= 70:
            risk_level = "critical"
        elif avg_risk_score >= 50:
            risk_level = "high"
        elif avg_risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "total_employees": total_employees,
            "employees_with_risks": employees_with_risks,
            "risk_percentage": round((employees_with_risks / total_employees * 100) if total_employees > 0 else 0, 2),
            "average_risk_score": round(avg_risk_score, 2),
            "risk_level": risk_level,
            "critical_alerts_count": critical_count,
            "high_alerts_count": high_count,
            "medium_alerts_count": medium_count,
            "total_alerts_count": len(all_alerts),
        }
    
    def _compute_risk_distribution(
        self,
        employee_risks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Compute risk distribution across team."""
        distribution = {
            "critical": 0,  # 70-100 risk score
            "high": 0,      # 50-69
            "medium": 0,    # 30-49
            "low": 0,       # 0-29
        }
        
        for er in employee_risks:
            score = er["risk_score"]
            if score >= 70:
                distribution["critical"] += 1
            elif score >= 50:
                distribution["high"] += 1
            elif score >= 30:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution

