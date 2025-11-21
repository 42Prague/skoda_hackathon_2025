"""
Training Plan Schemas
---------------------
Pydantic schemas for AI Training Plan Generator feature.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class WeeklyBreakdownItem(BaseModel):
    """Single week in the training plan."""

    week: int = Field(..., ge=1, description="Week number")
    focus_skills: List[str] = Field(default_factory=list, description="Skills to focus on this week")
    courses: List[str] = Field(default_factory=list, description="Courses to complete this week")
    practice_tasks: List[str] = Field(default_factory=list, description="Practice tasks for this week")
    milestones: List[str] = Field(default_factory=list, description="Milestones to achieve")


class CourseItem(BaseModel):
    """Course recommendation."""

    name: str = Field(..., description="Course name")
    provider: str = Field(..., description="Course provider")
    duration_hours: int = Field(..., ge=0, description="Duration in hours")
    type: str = Field(..., description="Course type (Online, In-person, Workshop, etc.)")
    priority: Literal["high", "medium", "low"] = Field(..., description="Priority level")
    skoda_academy: bool = Field(default=False, description="Whether it's a Škoda Academy module")


class SkillProgressionItem(BaseModel):
    """Skill progression mapping."""

    skill: str = Field(..., description="Skill name")
    current_level: str = Field(..., description="Current skill level")
    target_level: str = Field(..., description="Target skill level")
    weeks_to_master: int = Field(..., ge=0, description="Weeks needed to master")
    dependencies: List[str] = Field(default_factory=list, description="Prerequisite skills")


class MentorItem(BaseModel):
    """Mentor recommendation."""

    name: str = Field(..., description="Mentor name or role")
    expertise: List[str] = Field(default_factory=list, description="Areas of expertise")
    availability: str = Field(..., description="Availability description")
    recommended_for: List[str] = Field(default_factory=list, description="Skills/areas to mentor on")


class RiskItem(BaseModel):
    """Risk factor."""

    risk: str = Field(..., description="Risk description")
    severity: Literal["high", "medium", "low"] = Field(..., description="Risk severity")
    mitigation: str = Field(..., description="Mitigation strategy")


class InternalModuleItem(BaseModel):
    """Internal Škoda Academy module."""

    module: str = Field(..., description="Module name")
    department: str = Field(..., description="Department offering the module")
    duration: str = Field(..., description="Module duration")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")


class PracticeTaskItem(BaseModel):
    """Practice task."""

    task: str = Field(..., description="Task description")
    skill: str = Field(..., description="Related skill")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(..., description="Difficulty level")
    estimated_hours: int = Field(..., ge=0, description="Estimated hours to complete")


class TrainingPlanRequest(BaseModel):
    """Request schema for training plan generation."""

    employee_id: Optional[str] = Field(default=None, description="Employee identifier (optional)")
    skills: List[str] = Field(default_factory=list, description="Current skills")
    gaps: List[str] = Field(default_factory=list, description="Skill gaps to address")
    desired_role: str = Field(..., description="Target role for training")


class TrainingPlanResponse(BaseModel):
    """Response schema for training plan."""

    plan_overview: str = Field(..., description="Overview of the training plan")
    weekly_breakdown: List[WeeklyBreakdownItem] = Field(default_factory=list, description="Weekly plan breakdown")
    courses: List[CourseItem] = Field(default_factory=list, description="Recommended courses")
    skill_progression_map: List[SkillProgressionItem] = Field(default_factory=list, description="Skill progression mapping")
    mentors: List[MentorItem] = Field(default_factory=list, description="Recommended mentors")
    risks: List[RiskItem] = Field(default_factory=list, description="Risk factors")
    time_to_readiness: int = Field(..., ge=0, description="Time to readiness in weeks")
    internal_modules: List[InternalModuleItem] = Field(default_factory=list, description="Internal Škoda Academy modules")
    practice_tasks: List[PracticeTaskItem] = Field(default_factory=list, description="Practice tasks")
    ai_mode: str = Field(..., description="AI mode: 'featherless' or 'heuristic'")

