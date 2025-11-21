"""OpenRouter LLM client for skill extraction."""

import json
import logging
from typing import List, Optional, Dict, Any
import asyncio

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
import instructor

from config.settings import settings
from src.models import ExtractedSkill, SkillExtractionResponse

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with OpenRouter/GPT-4 for skill extraction."""

    def __init__(self):
        """Initialize the LLM client."""
        # Keep both wrapped and unwrapped clients
        self.base_client = AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        # Wrap with instructor for structured outputs
        self.client = instructor.from_openai(self.base_client)
        self.model = settings.openrouter_model
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries

    def _build_extraction_prompt(self, job_description: str) -> str:
        """Build the prompt for skill extraction."""
        return f"""You are a precise skill extraction system. Analyze the following job description and extract ALL mentioned skills.

Job Description:
{job_description}

Instructions:
1. Extract every skill mentioned, including:
   - Programming languages (Python, JavaScript, etc.)
   - Frameworks and libraries (React, Django, TensorFlow, etc.)
   - Tools and platforms (Git, Docker, AWS, etc.)
   - Methodologies (Agile, Scrum, TDD, etc.)
   - Domain knowledge (Machine Learning, Data Analysis, etc.)
   - Soft skills (Communication, Leadership, etc.)

2. For each skill, provide:
   - name: The skill name (use standard naming, e.g., "JavaScript" not "JS")
   - category: One of "technical", "domain", or "soft"
   - confidence: 0.0-1.0 (how confident you are this is a real skill requirement)
   - required: true if explicitly required, false if nice-to-have
   - level: One of "entry", "mid", "senior", "expert" or null if not specified

3. Use canonical names:
   - "React" not "ReactJS" or "React.js"
   - "Python" not "Python3" or "Py"
   - "Kubernetes" not "K8s" (unless "K8s" is explicitly written)

4. Return ONLY valid JSON in this exact format:
{{
  "skills": [
    {{
      "name": "Python",
      "category": "technical",
      "confidence": 0.95,
      "required": true,
      "level": "mid"
    }}
  ]
}}

Do not include any explanation or markdown formatting, only the JSON object."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((Exception,)),
    )
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM API with retry logic."""
        try:
            response: ChatCompletion = await self.base_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise skill extraction system that returns only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Low temperature for consistency
                max_tokens=100000,
                timeout=self.timeout,
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")

            return content.strip()

        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise

    def _parse_llm_response(self, response: str) -> SkillExtractionResponse:
        """Parse and validate LLM response."""
        try:
            # Remove markdown code blocks if present
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            # Parse JSON
            data = json.loads(response)

            # Validate and create Pydantic model
            extraction_response = SkillExtractionResponse.model_validate(data)

            return extraction_response

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response}")
            # Return empty response rather than failing
            return SkillExtractionResponse(skills=[])

        except Exception as e:
            logger.error(f"Failed to validate LLM response: {e}")
            return SkillExtractionResponse(skills=[])

    async def extract_skills(self, job_description: str) -> List[ExtractedSkill]:
        """Extract skills from a job description using structured output."""
        prompt = self._build_extraction_prompt(job_description)

        try:
            # Use instructor for guaranteed structured output
            extraction_response = await self.client.chat.completions.create(
                model=self.model,
                response_model=SkillExtractionResponse,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a precise skill extraction system that returns only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=100000,
                timeout=self.timeout,
                max_retries=2,
            )
            return extraction_response.skills

        except Exception as e:
            logger.error(f"Skill extraction failed: {e}")
            return []

    def _build_batch_extraction_prompt(self, job_descriptions: List[tuple[int, str]]) -> str:
        """Build prompt for extracting skills from multiple jobs in one request.

        Args:
            job_descriptions: List of (job_index, description) tuples

        Returns:
            Prompt string for batch extraction
        """
        jobs_text = "\n\n".join([
            f"JOB {idx}:\n{desc[:1000]}"  # Limit each description to 1000 chars
            for idx, desc in job_descriptions
        ])

        return f"""You are a precise skill extraction system. Analyze the following {len(job_descriptions)} job descriptions and extract ALL mentioned skills from EACH job.

{jobs_text}

Instructions:
1. Extract skills from EACH job separately
2. For each skill in each job, provide:
   - name: The skill name (use standard naming)
   - category: One of "technical", "domain", or "soft"
   - confidence: 0.0-1.0
   - required: true if explicitly required
   - level: One of "entry", "mid", "senior", "expert" or null

3. Return ONLY valid JSON in this exact format:
{{
  "jobs": [
    {{
      "job_index": 0,
      "skills": [
        {{
          "name": "Python",
          "category": "technical",
          "confidence": 0.95,
          "required": true,
          "level": "mid"
        }}
      ]
    }},
    {{
      "job_index": 1,
      "skills": [...]
    }}
  ]
}}

Return results for ALL {len(job_descriptions)} jobs in the same order."""

    async def extract_skills_true_batch(
        self, job_descriptions: List[str], batch_size: int = 10
    ) -> List[List[ExtractedSkill]]:
        """Extract skills from multiple jobs with concurrent batched LLM requests.

        This splits jobs into groups (batch_size per group) and runs multiple
        groups in parallel using asyncio, significantly improving throughput.

        Args:
            job_descriptions: List of job description strings
            batch_size: Number of jobs to send per LLM request (default: 10)

        Returns:
            List of skill lists, one per job description
        """
        # Split into batches
        batches = []
        for i in range(0, len(job_descriptions), batch_size):
            batch = job_descriptions[i:i+batch_size]
            batches.append((i, batch))

        # Process batches concurrently with semaphore limit
        semaphore = asyncio.Semaphore(settings.llm_max_concurrent)

        async def process_batch(start_idx: int, batch: List[str]) -> tuple[int, List[List[ExtractedSkill]]]:
            """Process a single batch of jobs."""
            async with semaphore:
                indexed_batch = list(enumerate(batch))

                try:
                    prompt = self._build_batch_extraction_prompt(indexed_batch)
                    response = await self._call_llm(prompt)

                    # Parse response
                    response = response.strip()
                    if response.startswith("```json"):
                        response = response[7:]
                    if response.startswith("```"):
                        response = response[3:]
                    if response.endswith("```"):
                        response = response[:-3]
                    response = response.strip()

                    data = json.loads(response)

                    # Extract skills for each job
                    job_results = data.get("jobs", [])

                    # Initialize results for this batch
                    batch_results = [[] for _ in range(len(batch))]

                    # Map results by job_index
                    for job_result in job_results:
                        job_idx = job_result.get("job_index", -1)
                        if 0 <= job_idx < len(batch):
                            skills_data = job_result.get("skills", [])
                            skills = []
                            for skill_data in skills_data:
                                try:
                                    skill = ExtractedSkill.model_validate(skill_data)
                                    skills.append(skill)
                                except Exception as e:
                                    logger.warning(f"Invalid skill in batch: {e}")
                            batch_results[job_idx] = skills

                    return (start_idx, batch_results)

                except Exception as e:
                    logger.error(f"Batch extraction failed for batch starting at {start_idx}: {e}")
                    # Return empty lists for failed batch
                    return (start_idx, [[] for _ in range(len(batch))])

        # Run all batches concurrently
        tasks = [process_batch(start_idx, batch) for start_idx, batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Reconstruct results in original order
        all_results = [None] * len(job_descriptions)
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch task failed: {result}")
                continue
            start_idx, batch_results = result
            for i, skills in enumerate(batch_results):
                all_results[start_idx + i] = skills

        # Fill any None values with empty lists (shouldn't happen but safety)
        all_results = [r if r is not None else [] for r in all_results]

        return all_results

    async def extract_skills_batch(
        self, job_descriptions: List[str]
    ) -> List[List[ExtractedSkill]]:
        """Extract skills from multiple job descriptions concurrently."""
        # Create tasks for all extractions
        tasks = [self.extract_skills(desc) for desc in job_descriptions]

        # Execute with controlled concurrency
        semaphore = asyncio.Semaphore(settings.llm_max_concurrent)

        async def bounded_task(task):
            async with semaphore:
                return await task

        # Run all tasks with concurrency limit
        results = await asyncio.gather(
            *[bounded_task(task) for task in tasks],
            return_exceptions=True,
        )

        # Convert exceptions to empty lists
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch extraction error: {result}")
                processed_results.append([])
            else:
                processed_results.append(result)

        return processed_results

    async def generate_job_description(
        self, job_title: str, skills: List[str], prompt: str
    ) -> str:
        """Generate a generic job description using LLM.

        Args:
            job_title: The job title to generate description for
            skills: List of common skills for this role
            prompt: The full prompt to send to LLM

        Returns:
            Generated job description string
        """
        try:
            response = await self._call_llm(prompt)
            # Clean up the response
            description = response.strip()

            # Remove any markdown formatting
            if description.startswith("```"):
                lines = description.split("\n")
                description = "\n".join(
                    line for line in lines if not line.startswith("```")
                ).strip()

            return description

        except Exception as e:
            logger.error(f"Job description generation failed for '{job_title}': {e}")
            # Return a basic fallback
            skills_str = ", ".join(skills[:10])
            return f"{job_title}s work with technologies such as {skills_str}. They develop, maintain, and optimize software systems and applications."

    async def filter_relevant_jobs(
        self, target_job_title: str, candidate_jobs: List[str]
    ) -> List[str]:
        """Filter candidate job titles to only those relevant to the target job.

        Args:
            target_job_title: The job title to search for (e.g., "ML Engineer")
            candidate_jobs: List of candidate job titles from full-text search

        Returns:
            List of relevant job titles filtered by LLM
        """
        if not candidate_jobs:
            return []

        # Build the filtering prompt
        jobs_list = "\n".join([f"- {job}" for job in candidate_jobs])

        prompt = f"""You are a job title relevance filter. Given a target job title and a list of candidate job titles, return ONLY the job titles that are truly relevant to the target.

Target Job Title: {target_job_title}

Candidate Job Titles:
{jobs_list}

Instructions:
1. Return ONLY job titles that would have similar skills/responsibilities to "{target_job_title}"
2. Remove job titles that are completely unrelated (different domain/field)
3. Include variations and related roles (e.g., for "ML Engineer": include "Machine Learning Engineer", "Data Scientist", "AI Engineer")
4. Exclude loosely related titles (e.g., for "ML Engineer": exclude "Mechanical Engineer", "Electrical Engineer")

Return your response as a JSON array of strings:
{{"relevant_jobs": ["Job Title 1", "Job Title 2", ...]}}

If no jobs are relevant, return: {{"relevant_jobs": []}}"""

        try:
            response = await self._call_llm(prompt)

            # Parse response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)
            relevant_jobs = data.get("relevant_jobs", [])

            # Validate that returned jobs are in the original list
            valid_jobs = [job for job in relevant_jobs if job in candidate_jobs]

            logger.info(f"LLM filtered {len(candidate_jobs)} jobs to {len(valid_jobs)} relevant jobs for '{target_job_title}'")

            return valid_jobs

        except Exception as e:
            logger.error(f"Job filtering failed: {e}")
            # Fallback: return all candidates
            return candidate_jobs


# Global LLM client instance
llm_client = LLMClient()
