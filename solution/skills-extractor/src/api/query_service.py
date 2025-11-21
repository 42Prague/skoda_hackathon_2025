"""Query service for skills and jobs."""

import logging
from typing import List, Dict, Any

from src.models import (
    Job,
    JobMatch,
    Skill,
    ValidatedSkill,
    SkillValidationResponse,
    ExtractedSkill,
    SkillSearchResult,
    SearchSkillsResponse,
    JobSearchResult,
    SearchJobsResponse,
)
from src.database import (
    get_all_skills,
    get_jobs_by_skills,
    get_candidate_job_titles,
    get_skills_by_job_titles,
    get_skills_by_job_title,
    find_similar_skills,
    search_skills as db_search_skills,
    search_jobs_fulltext,
)
from src.extraction import llm_client
from src.normalization import skill_normalizer

logger = logging.getLogger(__name__)


class QueryService:
    """Service for querying skills and jobs."""

    def __init__(self):
        """Initialize the query service."""
        # Cache for skills database
        self._skills_cache: Dict[str, Skill] | None = None
        self._alias_map: Dict[str, str] | None = None

    async def _load_skills_cache(self) -> None:
        """Load skills database into memory cache."""
        if self._skills_cache is None:
            logger.info("Loading skills database into cache...")
            skills = await get_all_skills()

            self._skills_cache = {s.canonical_name: s for s in skills}

            # Build alias -> canonical mapping
            self._alias_map = {}
            for skill in skills:
                # Add canonical name
                self._alias_map[skill.canonical_name.lower()] = skill.canonical_name

                # Add all aliases
                for alias in skill.aliases:
                    self._alias_map[alias.lower()] = skill.canonical_name

            logger.info(f"Loaded {len(skills)} skills into cache")

    async def find_jobs_by_skills(
        self,
        skills: List[str],
        match_all: bool = False,
        include_parents: bool = True,
        limit: int = 20,
    ) -> List[JobMatch]:
        """Find jobs matching the specified skills.

        Args:
            skills: List of skill names
            match_all: Whether to match all skills or any
            include_parents: Include jobs requiring parent skills
            limit: Maximum number of results

        Returns:
            List of job matches with scores
        """
        # Validate and normalize skill names first
        validated_skills = await self.validate_skills(skills)

        # Get canonical skill names
        canonical_skills = []
        for vs in validated_skills.validated_skills:
            canonical_skills.append(vs.canonical)

        # Add semantic matches
        for original, canonical in validated_skills.semantic_matches.items():
            if canonical not in canonical_skills:
                canonical_skills.append(canonical)

        if not canonical_skills:
            logger.warning("No valid skills found")
            return []

        # Query database
        results = await get_jobs_by_skills(
            skill_names=canonical_skills,
            match_all=match_all,
            include_parents=include_parents,
            limit=limit,
        )

        # Convert to JobMatch objects
        job_matches = []
        for row in results:
            job_data = row["job"]
            job = Job(
                id=job_data["id"],
                title=job_data["title"],
                description=job_data["description"],
                company=job_data.get("company"),
                location=job_data.get("location"),
                salary=job_data.get("salary"),
            )

            match_score = min(1.0, float(row["match_count"]) / len(canonical_skills))

            job_match = JobMatch(
                job=job,
                matched_skills=row["matched_skills"],
                match_score=match_score,
                total_required_skills=row.get("match_count", 0),
                coverage=float(row.get("coverage", 0.0)),
            )

            job_matches.append(job_match)

        return job_matches

    async def find_skills_by_job(
        self,
        job_title: str,
        include_children: bool = True,
    ) -> List[Skill]:
        """Find skills required by jobs with matching title.

        Uses LLM to filter relevant job titles before returning skills.

        Args:
            job_title: Job title to search for
            include_children: Include child skills in hierarchy

        Returns:
            List of skills with metadata
        """
        # Step 1: Get candidate job titles from full-text search
        logger.info(f"Searching for jobs matching '{job_title}'")
        candidate_jobs = await get_candidate_job_titles(job_title)

        if not candidate_jobs:
            logger.warning(f"No jobs found matching '{job_title}'")
            return []

        logger.info(f"Found {len(candidate_jobs)} candidate jobs: {candidate_jobs[:5]}...")

        # Step 2: Use LLM to filter relevant job titles
        logger.info(f"Filtering jobs with LLM...")
        relevant_jobs = await llm_client.filter_relevant_jobs(job_title, candidate_jobs)

        if not relevant_jobs:
            logger.warning(f"No relevant jobs after LLM filtering for '{job_title}'")
            return []

        logger.info(f"LLM filtered to {len(relevant_jobs)} relevant jobs: {relevant_jobs}")

        # Step 3: Get skills from the filtered job titles
        results = await get_skills_by_job_titles(relevant_jobs, include_children)

        # Convert to Skill objects
        skills = []
        for row in results:
            skill = Skill(
                canonical_name=row["canonical_name"],
                category=row["category"],
                aliases=row.get("aliases", []),
                embedding=None,  # Don't include embeddings in response
                parent_skills=[],  # Would need separate query
                child_skills=row.get("children", []),
            )
            skills.append(skill)

        return skills

    async def validate_skills(self, skill_names: List[str]) -> SkillValidationResponse:
        """Validate skills against database.

        This implements the three-step validation:
        1. Exact match
        2. Alias match
        3. Semantic match (vector similarity)

        Args:
            skill_names: List of skill names to validate

        Returns:
            SkillValidationResponse with validated, semantic, and unmatched skills
        """
        await self._load_skills_cache()

        validated_skills: List[ValidatedSkill] = []
        semantic_matches: Dict[str, str] = {}
        unmatched: List[str] = []

        for skill_name in skill_names:
            skill_lower = skill_name.lower()

            # Step 1: Check exact match (canonical name)
            if skill_name in self._skills_cache:
                validated_skills.append(
                    ValidatedSkill(
                        original=skill_name,
                        canonical=skill_name,
                        match_type="exact",
                        confidence=1.0,
                    )
                )
                continue

            # Step 2: Check alias match
            if skill_lower in self._alias_map:
                canonical = self._alias_map[skill_lower]
                validated_skills.append(
                    ValidatedSkill(
                        original=skill_name,
                        canonical=canonical,
                        match_type="alias",
                        confidence=1.0,
                    )
                )
                continue

            # Step 3: Semantic search fallback
            # Generate embedding and search vector database
            try:
                # Get all skills with embeddings
                skills_with_embeddings = [
                    s for s in self._skills_cache.values() if s.embedding
                ]

                if skills_with_embeddings:
                    # Use normalizer to find similar skills
                    from src.models import NormalizedSkill

                    normalized_skills_for_search = [
                        NormalizedSkill(
                            canonical_name=s.canonical_name,
                            original_name=s.canonical_name,
                            category=s.category,
                            aliases=s.aliases,
                            embedding=s.embedding,
                            cluster_id=None,
                        )
                        for s in skills_with_embeddings
                    ]

                    similar = skill_normalizer.find_similar_skills(
                        query_skill=skill_name,
                        normalized_skills=normalized_skills_for_search,
                        top_k=1,
                        threshold=0.85,
                    )

                    if similar:
                        best_match, similarity = similar[0]
                        semantic_matches[skill_name] = best_match.canonical_name
                        validated_skills.append(
                            ValidatedSkill(
                                original=skill_name,
                                canonical=best_match.canonical_name,
                                match_type="semantic",
                                confidence=similarity,
                            )
                        )
                        continue
            except Exception as e:
                logger.error(f"Semantic search failed for '{skill_name}': {e}")

            # No match found
            unmatched.append(skill_name)

        # Calculate coverage
        coverage = len(validated_skills) / len(skill_names) if skill_names else 0.0

        return SkillValidationResponse(
            validated_skills=validated_skills,
            semantic_matches=semantic_matches,
            unmatched=unmatched,
            coverage=coverage,
        )

    async def extract_validated_skills(self, text: str) -> SkillValidationResponse:
        """Extract skills from text using LLM and validate against database.

        Args:
            text: Text to extract skills from (e.g., resume, job description)

        Returns:
            SkillValidationResponse with validated skills
        """
        # Step 1: Extract skills using LLM
        extracted_skills: List[ExtractedSkill] = await llm_client.extract_skills(text)

        if not extracted_skills:
            return SkillValidationResponse(
                validated_skills=[],
                semantic_matches={},
                unmatched=[],
                coverage=0.0,
            )

        # Step 2: Validate extracted skills against database
        skill_names = [s.name for s in extracted_skills]
        validation_response = await self.validate_skills(skill_names)

        return validation_response

    async def search_skills(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        include_exact: bool = True,
        include_aliases: bool = True,
        include_semantic: bool = True,
    ) -> SearchSkillsResponse:
        """Search for skills by name with exact, alias, and semantic matching.

        Args:
            query: Skill name or pattern to search
            top_k: Maximum number of results
            min_similarity: Minimum similarity for semantic matches
            include_exact: Include exact matches
            include_aliases: Include alias matches
            include_semantic: Include semantic matches

        Returns:
            SearchSkillsResponse with matching skills
        """
        # Call database search function
        results = await db_search_skills(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            include_exact=include_exact,
            include_aliases=include_aliases,
            include_semantic=include_semantic,
        )

        # Convert to SkillSearchResult objects
        skill_results = []
        for row in results:
            skill_result = SkillSearchResult(
                canonical_name=row["canonical_name"],
                match_type=row["match_type"],
                similarity=row.get("similarity"),
                category=row["category"],
                aliases=row.get("aliases", []),
                parent_skills=row.get("parent_skills", []),
                child_skills=row.get("child_skills", []),
            )
            skill_results.append(skill_result)

        return SearchSkillsResponse(
            results=skill_results,
            total=len(skill_results),
            query=query,
        )

    async def search_jobs(
        self,
        query: str,
        top_k: int = 10,
        search_in_description: bool = False,
    ) -> SearchJobsResponse:
        """Search for jobs by title or keywords using full-text search.

        Args:
            query: Job title or keywords to search
            top_k: Maximum number of results
            search_in_description: Also search in job descriptions

        Returns:
            SearchJobsResponse with matching jobs
        """
        # Call database search function
        results = await search_jobs_fulltext(
            query=query,
            top_k=top_k,
            search_in_description=search_in_description,
        )

        # Convert to JobSearchResult objects
        job_results = []
        for row in results:
            job_data = row["job"]
            job = Job(
                id=job_data["id"],
                title=job_data["title"],
                description=job_data["description"],
                company=job_data.get("company"),
                location=job_data.get("location"),
                salary=job_data.get("salary"),
            )

            job_result = JobSearchResult(
                job=job,
                score=float(row["score"]),
            )
            job_results.append(job_result)

        return SearchJobsResponse(
            results=job_results,
            total=len(job_results),
            query=query,
        )


# Global query service instance
query_service = QueryService()
