"""Generate generic job descriptions from job titles and skills."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import settings
from .llm_client import llm_client

logger = logging.getLogger(__name__)
console = Console()


class JobDescriptionGenerator:
    """Generates generic job descriptions using LLM."""

    def __init__(self):
        """Initialize the description generator."""
        self.cache_file = settings.data_dir / "generated_descriptions.json"
        self.cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Load cached descriptions from disk."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r") as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached job descriptions")
            except Exception as e:
                logger.warning(f"Failed to load description cache: {e}")

    def _save_cache(self) -> None:
        """Save description cache to disk."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
            logger.info(f"Saved {len(self.cache)} job descriptions to cache")
        except Exception as e:
            logger.warning(f"Failed to save description cache: {e}")

    async def generate_description(
        self, job_title: str, common_skills: List[str]
    ) -> str:
        """Generate a generic job description for a job title.

        Args:
            job_title: The job title (e.g., "Python Developer")
            common_skills: List of skills commonly required for this role

        Returns:
            Generic job description string
        """
        # Check cache first
        if job_title in self.cache:
            logger.debug(f"Using cached description for '{job_title}'")
            return self.cache[job_title]

        # Generate using LLM - include ALL skills for comprehensive description
        skills_str = ", ".join(common_skills)  # Include all skills

        prompt = f"""You are a professional job description writer. Create a generic, professional description for the job title: "{job_title}"

Common skills and technologies for this role include: {skills_str}

Write a 4-5 sentence generic description that:
1. Describes what professionals in this role typically do
2. Lists and mentions MANY of the common technologies, tools, and skills they use (include as many as naturally fit)
3. Describes typical responsibilities and work environment
4. Is generic and applies to most "{job_title}" positions, not one specific company

Important:
- Do NOT use phrases like "We are looking for" or "The ideal candidate"
- Write in third person about what these professionals do
- Include specific technology names and skills from the list provided
- Make it rich with examples of tools, frameworks, and technologies
- Keep it factual and professional
- Focus on the role itself, not hiring requirements

Return ONLY the description text, no additional formatting or explanation."""

        try:
            description = await llm_client.generate_job_description(
                job_title=job_title, skills=common_skills, prompt=prompt
            )

            # Cache the result
            self.cache[job_title] = description
            self._save_cache()

            logger.info(f"Generated description for '{job_title}'")
            return description

        except Exception as e:
            logger.error(f"Failed to generate description for '{job_title}': {e}")
            # Fallback to basic description
            fallback = f"{job_title}s work with various technologies including {skills_str}. They are responsible for developing, maintaining, and optimizing software systems."
            return fallback

    async def generate_descriptions_for_jobs(
        self, jobs_by_title: Dict[str, List[Dict]]
    ) -> Dict[str, str]:
        """Generate descriptions for multiple job titles.

        Args:
            jobs_by_title: Dict mapping job title to list of job data dicts
                          Each job dict should have 'skills' key with list of skill names

        Returns:
            Dict mapping job title to generic description
        """
        descriptions = {}
        total = len(jobs_by_title)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Generating descriptions for {total} job titles...", total=total
            )

            for job_title, jobs_data in jobs_by_title.items():
                # Aggregate skills from all jobs with this title
                skill_counts = defaultdict(int)
                for job_data in jobs_data:
                    for skill in job_data.get("skills", []):
                        skill_counts[skill] += 1

                # Sort by frequency and take most common
                common_skills = [
                    skill
                    for skill, _ in sorted(
                        skill_counts.items(), key=lambda x: x[1], reverse=True
                    )
                ]

                # Generate description
                description = await self.generate_description(job_title, common_skills)
                descriptions[job_title] = description

                progress.update(task, advance=1)

        console.print(
            f"\n[green]✓ Generated {len(descriptions)} job descriptions[/green]"
        )
        return descriptions


# Global instance
description_generator = JobDescriptionGenerator()
