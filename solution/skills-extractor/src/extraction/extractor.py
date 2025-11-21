"""Job skill extraction with batch processing and checkpointing."""

import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import asyncio

from rich.progress import Progress, TaskID, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console

from config.settings import settings
from src.models import Job, ExtractedSkill
from .llm_client import llm_client

logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ExtractionResult:
    """Result of skill extraction for a single job."""
    job_id: str
    job_title: str
    skills: List[Dict[str, Any]]  # ExtractedSkill as dict
    success: bool
    error: Optional[str] = None


class SkillExtractor:
    """Handles batch skill extraction from job descriptions."""

    def __init__(self):
        """Initialize the skill extractor."""
        self.cache_dir = settings.cache_dir / "extractions"
        self.checkpoint_dir = settings.checkpoint_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Deduplication cache: hash -> skills
        self.dedup_cache: Dict[str, List[ExtractedSkill]] = {}

    def _hash_description(self, description: str) -> str:
        """Generate hash for job description deduplication."""
        return hashlib.md5(description.encode()).hexdigest()

    def _load_cache(self) -> None:
        """Load extraction cache from disk."""
        cache_file = self.cache_dir / "dedup_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    # Convert dict back to ExtractedSkill objects
                    for desc_hash, skills_data in cache_data.items():
                        self.dedup_cache[desc_hash] = [
                            ExtractedSkill.model_validate(s) for s in skills_data
                        ]
                logger.info(f"Loaded {len(self.dedup_cache)} cached extractions")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")

    def _save_cache(self) -> None:
        """Save extraction cache to disk."""
        cache_file = self.cache_dir / "dedup_cache.json"
        try:
            # Convert ExtractedSkill objects to dicts
            cache_data = {
                desc_hash: [s.model_dump() for s in skills]
                for desc_hash, skills in self.dedup_cache.items()
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f)
            logger.info(f"Saved {len(self.dedup_cache)} extractions to cache")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _save_checkpoint(
        self, results: List[ExtractionResult], checkpoint_name: str
    ) -> None:
        """Save extraction checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        try:
            checkpoint_data = {
                "results": [asdict(r) for r in results],
                "count": len(results),
            }
            with open(checkpoint_file, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            logger.info(f"Saved checkpoint: {checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def _load_checkpoint(self, checkpoint_name: str) -> Optional[List[ExtractionResult]]:
        """Load extraction checkpoint."""
        checkpoint_file = self.checkpoint_dir / f"{checkpoint_name}.json"
        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, "r") as f:
                checkpoint_data = json.load(f)
                results = [
                    ExtractionResult(**r) for r in checkpoint_data["results"]
                ]
            logger.info(f"Loaded checkpoint with {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    async def extract_from_job(self, job: Job) -> ExtractionResult:
        """Extract skills from a single job."""
        # Check deduplication cache
        desc_hash = self._hash_description(job.description)

        if desc_hash in self.dedup_cache:
            logger.debug(f"Cache hit for job {job.id}")
            skills = self.dedup_cache[desc_hash]
            return ExtractionResult(
                job_id=job.id,
                job_title=job.title,
                skills=[s.model_dump() for s in skills],
                success=True,
            )

        # Extract skills using LLM
        try:
            skills = await llm_client.extract_skills(job.description)

            # Cache the result
            self.dedup_cache[desc_hash] = skills

            return ExtractionResult(
                job_id=job.id,
                job_title=job.title,
                skills=[s.model_dump() for s in skills],
                success=True,
            )

        except Exception as e:
            logger.error(f"Extraction failed for job {job.id}: {e}")
            return ExtractionResult(
                job_id=job.id,
                job_title=job.title,
                skills=[],
                success=False,
                error=str(e),
            )

    async def extract_from_jobs(
        self,
        jobs: List[Job],
        batch_size: Optional[int] = None,
        checkpoint_name: str = "extraction_checkpoint",
        resume: bool = True,
    ) -> List[ExtractionResult]:
        """Extract skills from multiple jobs with progress tracking.

        Args:
            jobs: List of jobs to process
            batch_size: Number of jobs per batch (defaults to settings)
            checkpoint_name: Name for checkpoint files
            resume: Whether to resume from checkpoint if it exists

        Returns:
            List of extraction results
        """
        batch_size = batch_size or settings.llm_batch_size

        # Load cache
        self._load_cache()

        # Check for existing checkpoint
        if resume:
            checkpoint_results = self._load_checkpoint(checkpoint_name)
            if checkpoint_results:
                console.print(
                    f"[yellow]Resuming from checkpoint with {len(checkpoint_results)} results[/yellow]"
                )
                # Filter out already processed jobs
                processed_ids = {r.job_id for r in checkpoint_results}
                jobs = [j for j in jobs if j.id not in processed_ids]
                if not jobs:
                    console.print("[green]All jobs already processed![/green]")
                    return checkpoint_results
            else:
                checkpoint_results = []
        else:
            checkpoint_results = []

        all_results = checkpoint_results.copy()

        # Process in batches with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            console=console,
        ) as progress:

            main_task = progress.add_task(
                f"[cyan]Extracting skills from {len(jobs)} jobs...",
                total=len(jobs),
            )

            for i in range(0, len(jobs), batch_size):
                batch = jobs[i : i + batch_size]
                batch_num = i // batch_size + 1
                total_batches = (len(jobs) + batch_size - 1) // batch_size

                progress.update(
                    main_task,
                    description=f"[cyan]Processing batch {batch_num}/{total_batches} ({len(batch)} jobs, ~{(len(batch) + 19) // 20} LLM calls)...",
                )

                # Check cache for each job in batch
                batch_jobs_to_process = []
                batch_job_indices = []
                batch_results_cached = [None] * len(batch)

                for idx, job in enumerate(batch):
                    desc_hash = self._hash_description(job.description)
                    if desc_hash in self.dedup_cache:
                        logger.debug(f"Cache hit for job {job.id}")
                        skills = self.dedup_cache[desc_hash]
                        batch_results_cached[idx] = ExtractionResult(
                            job_id=job.id,
                            job_title=job.title,
                            skills=[s.model_dump() for s in skills],
                            success=True,
                        )
                    else:
                        batch_jobs_to_process.append(job)
                        batch_job_indices.append(idx)

                # Process uncached jobs with true batching (multiple jobs in 1 LLM call)
                if batch_jobs_to_process:
                    descriptions = [job.description for job in batch_jobs_to_process]
                    try:
                        # TRUE BATCHING: Send 10 jobs per LLM request (parallel processing with OpenRouter)
                        skills_lists = await llm_client.extract_skills_true_batch(
                            descriptions, batch_size=10
                        )

                        # Cache and create results
                        for job, skills in zip(batch_jobs_to_process, skills_lists):
                            desc_hash = self._hash_description(job.description)
                            self.dedup_cache[desc_hash] = skills

                            result = ExtractionResult(
                                job_id=job.id,
                                job_title=job.title,
                                skills=[s.model_dump() for s in skills],
                                success=True,
                            )

                            # Find the original index and update
                            for i, idx in enumerate(batch_job_indices):
                                if batch_jobs_to_process[i].id == job.id:
                                    batch_results_cached[idx] = result
                                    break

                    except Exception as e:
                        logger.error(f"Batch extraction failed: {e}")
                        logger.info(f"Falling back to individual extraction for {len(batch_jobs_to_process)} jobs")

                        # FALLBACK: Process failed batch jobs individually
                        for i, job in enumerate(batch_jobs_to_process):
                            try:
                                skills = await llm_client.extract_skills(job.description)
                                desc_hash = self._hash_description(job.description)
                                self.dedup_cache[desc_hash] = skills

                                result = ExtractionResult(
                                    job_id=job.id,
                                    job_title=job.title,
                                    skills=[s.model_dump() for s in skills],
                                    success=True,
                                )
                                batch_results_cached[batch_job_indices[i]] = result
                            except Exception as individual_error:
                                logger.error(f"Individual extraction failed for job {job.id}: {individual_error}")
                                batch_results_cached[batch_job_indices[i]] = ExtractionResult(
                                    job_id=job.id,
                                    job_title=job.title,
                                    skills=[],
                                    success=False,
                                    error=str(individual_error),
                                )

                # Update progress for all jobs in batch
                progress.advance(main_task, advance=len(batch))

                all_results.extend(batch_results_cached)

                # Save checkpoint after each batch
                self._save_checkpoint(all_results, checkpoint_name)

                # Small delay to avoid rate limiting
                if i + batch_size < len(jobs):
                    await asyncio.sleep(1)

        # Save final cache
        self._save_cache()

        # Statistics
        successful = sum(1 for r in all_results if r.success)
        failed = len(all_results) - successful
        total_skills = sum(len(r.skills) for r in all_results if r.success)
        avg_skills = total_skills / successful if successful > 0 else 0

        console.print("\n[bold green]Extraction Complete![/bold green]")
        console.print(f"  ✓ Successful: {successful}")
        console.print(f"  ✗ Failed: {failed}")
        console.print(f"  📊 Total skills extracted: {total_skills}")
        console.print(f"  📈 Average skills per job: {avg_skills:.1f}")

        return all_results


# Global extractor instance
skill_extractor = SkillExtractor()
