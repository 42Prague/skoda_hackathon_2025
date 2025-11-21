"""Pydantic models for the skills taxonomy system."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class SkillCategory(str, Enum):
    """Skill category enumeration."""
    TECHNICAL = "technical"
    DOMAIN = "domain"
    SOFT = "soft"


class SkillLevel(str, Enum):
    """Skill level enumeration."""
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"


class ExtractedSkill(BaseModel):
    """Skill extracted from job description by LLM."""
    name: str = Field(..., description="Skill name")
    category: SkillCategory = Field(..., description="Skill category")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")
    required: bool = Field(default=True, description="Whether skill is required")
    level: Optional[SkillLevel] = Field(None, description="Required skill level")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize skill name."""
        return v.strip()


class SkillExtractionResponse(BaseModel):
    """Response from LLM skill extraction."""
    skills: List[ExtractedSkill] = Field(..., description="List of extracted skills")


class NormalizedSkill(BaseModel):
    """Normalized skill with canonical form."""
    canonical_name: str = Field(..., description="Canonical skill name")
    original_name: str = Field(..., description="Original extracted name")
    category: SkillCategory = Field(..., description="Skill category")
    aliases: List[str] = Field(default_factory=list, description="Skill aliases")
    embedding: Optional[List[float]] = Field(None, description="Skill embedding vector")
    cluster_id: Optional[int] = Field(None, description="Cluster ID from normalization")


class Job(BaseModel):
    """Job posting model."""
    id: str = Field(..., description="Unique job identifier")
    title: str = Field(..., description="Job title")
    description: str = Field(..., description="Job description text")
    company: Optional[str] = Field(None, description="Company name")
    location: Optional[str] = Field(None, description="Job location")
    salary: Optional[str] = Field(None, description="Salary range")


class Skill(BaseModel):
    """Skill node in the database."""
    canonical_name: str = Field(..., description="Canonical skill name")
    category: SkillCategory = Field(..., description="Skill category")
    aliases: List[str] = Field(default_factory=list, description="Skill aliases")
    embedding: Optional[List[float]] = Field(None, description="Skill embedding vector")
    parent_skills: List[str] = Field(
        default_factory=list,
        description="Parent skills in hierarchy"
    )
    child_skills: List[str] = Field(
        default_factory=list,
        description="Child skills in hierarchy"
    )


class JobSkillRelationship(BaseModel):
    """Relationship between job and skill."""
    job_id: str = Field(..., description="Job identifier")
    skill_name: str = Field(..., description="Skill canonical name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    required: bool = Field(default=True, description="Whether skill is required")
    level: Optional[SkillLevel] = Field(None, description="Required skill level")


class ValidatedSkill(BaseModel):
    """Skill validated against database."""
    original: str = Field(..., description="Original skill name from input")
    canonical: str = Field(..., description="Canonical name in database")
    match_type: str = Field(..., description="Type of match: exact, alias, semantic")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Match confidence")


class SkillValidationResponse(BaseModel):
    """Response from skill validation."""
    validated_skills: List[ValidatedSkill] = Field(
        default_factory=list,
        description="Successfully validated skills"
    )
    semantic_matches: Dict[str, str] = Field(
        default_factory=dict,
        description="Semantic matches: original -> canonical"
    )
    unmatched: List[str] = Field(
        default_factory=list,
        description="Skills that couldn't be matched"
    )
    coverage: float = Field(..., ge=0.0, le=1.0, description="Percentage of skills matched")


class JobMatch(BaseModel):
    """Job matching result."""
    job: Job = Field(..., description="Matched job")
    matched_skills: List[str] = Field(..., description="Skills that matched")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Overall match score")
    total_required_skills: int = Field(..., description="Total skills required by job")
    coverage: float = Field(..., ge=0.0, le=1.0, description="Percentage of required skills matched")


class FindJobsRequest(BaseModel):
    """Request to find jobs by skills."""
    skills: List[str] = Field(..., min_length=1, description="List of skills")
    match_all: bool = Field(default=False, description="Whether to match all skills or any")
    include_parents: bool = Field(
        default=True,
        description="Include parent skills in matching"
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class FindSkillsRequest(BaseModel):
    """Request to find skills by job title."""
    job_title: str = Field(..., min_length=1, description="Job title to search")
    include_children: bool = Field(
        default=True,
        description="Include child skills in results"
    )


class ExtractSkillsRequest(BaseModel):
    """Request to extract and validate skills from text."""
    text: str = Field(..., min_length=1, description="Text to extract skills from")


class SystemStats(BaseModel):
    """System statistics."""
    total_jobs: int = Field(..., description="Total number of jobs")
    total_skills: int = Field(..., description="Total number of unique skills")
    total_relationships: int = Field(..., description="Total job-skill relationships")
    avg_skills_per_job: float = Field(..., description="Average skills per job")
    skill_categories: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of skills by category"
    )
    hierarchical_skills: int = Field(
        default=0,
        description="Number of skills with parent/child relationships"
    )


class SearchSkillsRequest(BaseModel):
    """Request to search for skills by name/pattern."""
    query: str = Field(..., min_length=1, description="Skill name or pattern to search")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    min_similarity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity for semantic matches"
    )
    include_exact: bool = Field(default=True, description="Include exact matches")
    include_aliases: bool = Field(default=True, description="Include alias matches")
    include_semantic: bool = Field(default=True, description="Include semantic matches")


class SkillSearchResult(BaseModel):
    """Single skill search result."""
    canonical_name: str = Field(..., description="Canonical skill name")
    match_type: str = Field(..., description="Type of match: exact, alias, or semantic")
    similarity: Optional[float] = Field(None, description="Similarity score for semantic matches")
    category: str = Field(..., description="Skill category")
    aliases: List[str] = Field(default_factory=list, description="Skill aliases")
    parent_skills: List[str] = Field(default_factory=list, description="Parent skills")
    child_skills: List[str] = Field(default_factory=list, description="Child skills")


class SearchSkillsResponse(BaseModel):
    """Response for skill search."""
    results: List[SkillSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")


class SearchJobsRequest(BaseModel):
    """Request to search for jobs by title or keywords."""
    query: str = Field(..., min_length=1, description="Job title or keywords to search")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    search_in_description: bool = Field(
        default=False,
        description="Also search in job descriptions"
    )


class JobSearchResult(BaseModel):
    """Single job search result."""
    job: Job = Field(..., description="Job details")
    score: float = Field(..., description="Relevance score from full-text search")


class SearchJobsResponse(BaseModel):
    """Response for job search."""
    results: List[JobSearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original search query")
