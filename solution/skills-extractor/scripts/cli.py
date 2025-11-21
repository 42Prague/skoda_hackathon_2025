"""CLI tool for the skills taxonomy pipeline."""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional
from collections import Counter

import typer
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from config.settings import settings
from src.database import (
    neo4j_client,
    create_jobs_bulk,
    create_skills_bulk,
    create_job_skill_relationships_bulk,
    create_skill_hierarchies_bulk,
)
from src.extraction import skill_extractor, ExtractionResult
from src.extraction.description_generator import description_generator
from src.normalization import skill_normalizer, hierarchy_builder
from src.models import Job, ExtractedSkill, NormalizedSkill, JobSkillRelationship, SkillLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(help="Skills Taxonomy CLI - LLM-based skill extraction and job matching")
console = Console()


@app.command()
def init_db():
    """Initialize Neo4j database schema (constraints and indexes)."""
    console.print("[bold cyan]Initializing Neo4j Database Schema[/bold cyan]\n")

    async def _init():
        await neo4j_client.connect()
        await neo4j_client.initialize_schema()
        await neo4j_client.close()

    asyncio.run(_init())
    console.print("\n[bold green]✓ Database schema initialized successfully![/bold green]")


@app.command()
def clear_db(
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    )
):
    """Clear all data from the database (use with caution!)."""
    if not confirm:
        confirmed = typer.confirm(
            "⚠️  This will delete ALL data from the database. Are you sure?"
        )
        if not confirmed:
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Abort()

    async def _clear():
        await neo4j_client.connect()
        await neo4j_client.clear_database()
        await neo4j_client.close()

    asyncio.run(_clear())
    console.print("[bold green]✓ Database cleared successfully![/bold green]")


@app.command()
def extract(
    dataset_path: Path = typer.Option(
        ...,
        "--dataset",
        "-d",
        help="Path to job descriptions CSV file",
        exists=True,
    ),
    batch_size: int = typer.Option(
        50,
        "--batch-size",
        "-b",
        help="Number of jobs to process per batch",
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of jobs to process (for testing)",
    ),
    checkpoint_name: str = typer.Option(
        "extraction_checkpoint",
        "--checkpoint",
        "-c",
        help="Checkpoint file name",
    ),
    no_resume: bool = typer.Option(
        False,
        "--no-resume",
        help="Don't resume from checkpoint",
    ),
):
    """Extract skills from job descriptions using LLM."""
    console.print("[bold cyan]Phase 1: Skill Extraction from Jobs[/bold cyan]\n")

    # Load dataset
    console.print(f"[cyan]Loading dataset from {dataset_path}...[/cyan]")
    df = pd.read_csv(dataset_path)

    if limit:
        df = df.head(limit)
        console.print(f"[yellow]Limited to {limit} jobs for testing[/yellow]")

    # Convert to Job objects
    jobs = []
    for idx, row in df.iterrows():
        job = Job(
            id=str(row.get("Job Id", idx)),
            title=str(row.get("Job Title", row.get("Role", "Unknown"))),
            description=str(row.get("Job Description", row.get("description", ""))),
            company=str(row.get("Company", row.get("company", None))) if "Company" in row or "company" in row else None,
            location=str(row.get("location", None)) if "location" in row else None,
            salary=None,
        )
        jobs.append(job)

    console.print(f"[green]✓ Loaded {len(jobs)} jobs[/green]\n")

    # Extract skills
    async def _extract():
        results = await skill_extractor.extract_from_jobs(
            jobs=jobs,
            batch_size=batch_size,
            checkpoint_name=checkpoint_name,
            resume=not no_resume,
        )

        # Save results
        output_file = settings.data_dir / f"{checkpoint_name}_results.json"
        with open(output_file, "w") as f:
            json.dump([{
                "job_id": r.job_id,
                "skills": r.skills,
                "success": r.success,
                "error": r.error,
            } for r in results], f, indent=2)

        console.print(f"\n[green]✓ Results saved to {output_file}[/green]")

        return results

    results = asyncio.run(_extract())

    console.print("\n[bold green]✓ Skill extraction complete![/bold green]")


@app.command()
def normalize(
    checkpoint_name: str = typer.Option(
        "extraction_checkpoint",
        "--checkpoint",
        "-c",
        help="Checkpoint file name from extraction phase",
    ),
    eps: float = typer.Option(
        0.15,
        "--eps",
        "-e",
        help="DBSCAN epsilon parameter",
    ),
):
    """Normalize extracted skills using embeddings and clustering."""
    console.print("[bold cyan]Phase 2: Skill Normalization[/bold cyan]\n")

    # Load extraction results
    checkpoint_file = settings.checkpoint_dir / f"{checkpoint_name}.json"
    if not checkpoint_file.exists():
        console.print(f"[red]Error: Checkpoint file not found: {checkpoint_file}[/red]")
        raise typer.Exit(1)

    with open(checkpoint_file, "r") as f:
        checkpoint_data = json.load(f)
        results = checkpoint_data["results"]

    # Convert to ExtractedSkill objects
    all_extracted_skills = []
    skill_counts = Counter()

    for result in results:
        if result["success"]:
            job_skills = [ExtractedSkill.model_validate(s) for s in result["skills"]]
            all_extracted_skills.append(job_skills)

            for skill in job_skills:
                skill_counts[skill.name] += 1

    console.print(f"[green]✓ Loaded {len(results)} extraction results[/green]\n")

    # Normalize skills
    normalized_skills = skill_normalizer.normalize_skills(
        all_extracted_skills=all_extracted_skills,
        skill_counts=skill_counts,
    )

    # Save normalized skills
    output_file = settings.data_dir / "normalized_skills.json"
    with open(output_file, "w") as f:
        json.dump(
            [s.model_dump() for s in normalized_skills],
            f,
            indent=2,
        )

    console.print(f"\n[green]✓ Normalized skills saved to {output_file}[/green]")
    console.print("\n[bold green]✓ Skill normalization complete![/bold green]")


@app.command()
def infer_hierarchy():
    """Infer hierarchical relationships between skills."""
    console.print("[bold cyan]Phase 3: Hierarchy Inference[/bold cyan]\n")

    # Load normalized skills
    normalized_file = settings.data_dir / "normalized_skills.json"
    if not normalized_file.exists():
        console.print(f"[red]Error: Normalized skills file not found: {normalized_file}[/red]")
        raise typer.Exit(1)

    with open(normalized_file, "r") as f:
        skills_data = json.load(f)
        normalized_skills = [NormalizedSkill.model_validate(s) for s in skills_data]

    console.print(f"[green]✓ Loaded {len(normalized_skills)} normalized skills[/green]\n")

    # Infer hierarchies
    hierarchies = hierarchy_builder.infer_hierarchies(normalized_skills)

    # Print hierarchy tree
    hierarchy_builder.print_hierarchy_tree(normalized_skills, hierarchies)

    # Save hierarchies
    output_file = settings.data_dir / "skill_hierarchies.json"
    with open(output_file, "w") as f:
        json.dump(
            [{"parent": p, "child": c} for p, c in hierarchies],
            f,
            indent=2,
        )

    console.print(f"\n[green]✓ Hierarchies saved to {output_file}[/green]")
    console.print("\n[bold green]✓ Hierarchy inference complete![/bold green]")


@app.command()
def generate_descriptions(
    checkpoint_name: str = typer.Option(
        "extraction_checkpoint",
        "--checkpoint",
        "-c",
        help="Checkpoint file name from extraction phase",
    ),
):
    """Generate generic job descriptions from extraction results."""
    console.print("[bold cyan]Phase 3.5: Generic Job Description Generation[/bold cyan]\n")

    # Load extraction results
    checkpoint_file = settings.checkpoint_dir / f"{checkpoint_name}.json"
    if not checkpoint_file.exists():
        console.print(f"[red]Error: Checkpoint file not found: {checkpoint_file}[/red]")
        raise typer.Exit(1)

    with open(checkpoint_file, "r") as f:
        checkpoint_data = json.load(f)

    # Group jobs by title and aggregate skills
    jobs_by_title = {}
    for result in checkpoint_data["results"]:
        if result["success"]:
            job_title = result.get("job_title", "Unknown")
            skill_names = [s["name"] for s in result["skills"]]

            if job_title not in jobs_by_title:
                jobs_by_title[job_title] = []

            jobs_by_title[job_title].append({"skills": skill_names})

    console.print(f"[green]✓ Found {len(jobs_by_title)} unique job titles[/green]\n")

    # Generate descriptions
    async def _generate():
        descriptions = await description_generator.generate_descriptions_for_jobs(
            jobs_by_title
        )
        return descriptions

    descriptions = asyncio.run(_generate())

    # Display sample
    console.print("\n[bold]Sample Generated Descriptions:[/bold]\n")
    for idx, (title, desc) in enumerate(list(descriptions.items())[:3]):
        console.print(f"[cyan]Title:[/cyan] {title}")
        console.print(f"[dim]{desc}[/dim]\n")

    console.print(f"\n[bold green]✓ Generated descriptions for {len(descriptions)} job titles![/bold green]")


@app.command()
def load_db(
    checkpoint_name: str = typer.Option(
        "extraction_checkpoint",
        "--checkpoint",
        "-c",
        help="Checkpoint file name from extraction phase",
    ),
):
    """Load all data into Neo4j database from prepared JSON files."""
    console.print("[bold cyan]Phase 4: Loading Data into Neo4j[/bold cyan]\n")

    async def _load():
        await neo4j_client.connect()

        # Load generic job descriptions
        descriptions_file = settings.data_dir / "generated_descriptions.json"
        descriptions = {}
        if descriptions_file.exists():
            with open(descriptions_file, "r") as f:
                descriptions = json.load(f)
            console.print(f"[green]✓ Loaded {len(descriptions)} generic job descriptions[/green]")
        else:
            console.print("[yellow]Warning: No generated descriptions found, using fallback descriptions[/yellow]")

        # Load extraction checkpoint to get job data
        console.print("[cyan]Loading jobs from checkpoint...[/cyan]")
        checkpoint_file = settings.checkpoint_dir / f"{checkpoint_name}.json"
        with open(checkpoint_file, "r") as f:
            checkpoint_data = json.load(f)
            extraction_results = checkpoint_data["results"]

        # Create Job objects from checkpoint
        jobs = []
        for result in extraction_results:
            if result["success"]:
                job_id = result["job_id"]
                job_title = result["job_title"]

                # Use generic description if available, otherwise use a generic fallback
                if job_title in descriptions:
                    description = descriptions[job_title]
                else:
                    # Fallback to generic description
                    description = f"{job_title}s are professionals who work in this role. Skills and responsibilities vary by position."

                job = Job(
                    id=job_id,
                    title=job_title,
                    description=description,
                    company=None,  # Not available in checkpoint
                    location=None,  # Not available in checkpoint
                    salary=None,
                )
                jobs.append(job)

        await create_jobs_bulk(jobs)
        console.print(f"[green]✓ Loaded {len(jobs)} jobs[/green]")

        # Load normalized skills
        console.print("[cyan]Loading skills...[/cyan]")
        normalized_file = settings.data_dir / "normalized_skills.json"
        with open(normalized_file, "r") as f:
            skills_data = json.load(f)
            normalized_skills = [NormalizedSkill.model_validate(s) for s in skills_data]

        await create_skills_bulk(normalized_skills)
        console.print(f"[green]✓ Loaded {len(normalized_skills)} skills[/green]")

        # Load job-skill relationships
        console.print("[cyan]Loading job-skill relationships...[/cyan]")

        # Build skill name -> canonical mapping
        skill_map = {s.canonical_name.lower(): s.canonical_name for s in normalized_skills}
        for skill in normalized_skills:
            for alias in skill.aliases:
                skill_map[alias.lower()] = skill.canonical_name

        relationships = []
        for result in extraction_results:
            if result["success"]:
                for skill_data in result["skills"]:
                    skill = ExtractedSkill.model_validate(skill_data)
                    canonical_name = skill_map.get(skill.name.lower(), skill.name)

                    rel = JobSkillRelationship(
                        job_id=result["job_id"],
                        skill_name=canonical_name,
                        confidence=skill.confidence,
                        required=skill.required,
                        level=skill.level if isinstance(skill.level, (SkillLevel, type(None))) else None,
                    )
                    relationships.append(rel)

        await create_job_skill_relationships_bulk(relationships)
        console.print(f"[green]✓ Loaded {len(relationships)} relationships[/green]")

        # Load hierarchies
        console.print("[cyan]Loading skill hierarchies...[/cyan]")
        hierarchy_file = settings.data_dir / "skill_hierarchies.json"
        with open(hierarchy_file, "r") as f:
            hierarchy_data = json.load(f)
            hierarchies = [(h["parent"], h["child"]) for h in hierarchy_data]

        await create_skill_hierarchies_bulk(hierarchies)
        console.print(f"[green]✓ Loaded {len(hierarchies)} hierarchy relationships[/green]")

        await neo4j_client.close()

    asyncio.run(_load())
    console.print("\n[bold green]✓ Database loading complete![/bold green]")
    console.print("\n[cyan]Access Neo4j Browser at: http://localhost:7474[/cyan]")
    console.print("[cyan]Username: neo4j, Password: skillspassword[/cyan]")


@app.command()
def stats():
    """Display database statistics."""
    async def _stats():
        await neo4j_client.connect()
        stats = await neo4j_client.get_stats()
        await neo4j_client.close()

        # Create statistics table
        table = Table(title="Skills Taxonomy Database Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Total Jobs", str(stats["total_jobs"]))
        table.add_row("Total Skills", str(stats["total_skills"]))
        table.add_row("Job-Skill Relationships", str(stats["total_relationships"]))
        table.add_row("Hierarchical Relationships", str(stats["total_hierarchical"]))
        table.add_row("Avg Skills per Job", f"{stats['avg_skills_per_job']:.2f}")

        console.print()
        console.print(table)

        # Skill categories
        if stats["skill_categories"]:
            console.print("\n[bold cyan]Skills by Category:[/bold cyan]")
            for category, count in stats["skill_categories"].items():
                console.print(f"  • {category}: {count}")

    asyncio.run(_stats())


@app.command()
def serve(
    host: str = typer.Option(
        "0.0.0.0",
        "--host",
        "-h",
        help="Host to bind to",
    ),
    port: int = typer.Option(
        8000,
        "--port",
        "-p",
        help="Port to bind to",
    ),
    reload: bool = typer.Option(
        False,
        "--reload",
        "-r",
        help="Enable auto-reload",
    ),
):
    """Start the FastAPI server."""
    import uvicorn

    console.print(f"[bold cyan]Starting Skills Taxonomy API on {host}:{port}[/bold cyan]\n")
    console.print(f"[cyan]API docs: http://{host}:{port}/docs[/cyan]")
    console.print(f"[cyan]Neo4j Browser: http://localhost:7474[/cyan]\n")

    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command()
def prepare(
    dataset_path: Path = typer.Option(
        ...,
        "--dataset",
        "-d",
        help="Path to job descriptions CSV file",
        exists=True,
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of jobs to process (for testing)",
    ),
    batch_size: int = typer.Option(
        15,
        "--batch-size",
        "-b",
        help="Number of jobs to process per batch",
    ),
    skip_extract: bool = typer.Option(
        False,
        "--skip-extract",
        help="Skip extraction phase (use existing checkpoint)",
    ),
):
    """Prepare data without Neo4j: extract → normalize → infer → generate."""
    console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]")
    console.print("[bold cyan]  Data Preparation (No Neo4j Required)  [/bold cyan]")
    console.print("[bold cyan]═══════════════════════════════════════════[/bold cyan]\n")

    checkpoint_name = "extraction_checkpoint"

    # Phase 1: Extract
    if not skip_extract:
        console.print("[bold]Phase 1: Extract Skills[/bold]")
        extract(
            dataset_path=dataset_path,
            batch_size=batch_size,
            limit=limit,
            checkpoint_name=checkpoint_name,
            no_resume=False,
        )
        console.print()

    # Phase 2: Normalize
    console.print("[bold]Phase 2: Normalize Skills[/bold]")
    normalize(checkpoint_name=checkpoint_name)
    console.print()

    # Phase 3: Infer Hierarchy
    console.print("[bold]Phase 3: Infer Hierarchies[/bold]")
    infer_hierarchy()
    console.print()

    # Phase 3.5: Generate Descriptions
    console.print("[bold]Phase 3.5: Generate Job Descriptions[/bold]")
    generate_descriptions(checkpoint_name=checkpoint_name)
    console.print()

    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]  ✓ Data Preparation Complete!           [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    console.print("[cyan]Data files created:[/cyan]")
    console.print(f"  • data/checkpoints/{checkpoint_name}.json")
    console.print("  • data/normalized_skills.json")
    console.print("  • data/skill_hierarchies.json")
    console.print("  • data/generated_descriptions.json")
    console.print()
    console.print("[cyan]Next steps:[/cyan]")
    console.print("  1. Start services: docker-compose up -d")
    console.print("  2. Data will be auto-loaded into Neo4j on startup")
    console.print("  3. Access Neo4j Browser: http://localhost:7474")
    console.print("  4. Access API docs: http://localhost:8000/docs")


@app.command()
def pipeline(
    dataset_path: Path = typer.Option(
        ...,
        "--dataset",
        "-d",
        help="Path to job descriptions CSV file",
        exists=True,
    ),
    limit: Optional[int] = typer.Option(
        None,
        "--limit",
        "-l",
        help="Maximum number of jobs to process (for testing)",
    ),
    skip_extract: bool = typer.Option(
        False,
        "--skip-extract",
        help="Skip extraction phase (use existing checkpoint)",
    ),
):
    """Run the complete pipeline: extract → normalize → infer → load (requires Neo4j)."""
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]  Skills Taxonomy Pipeline - Full Run   [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════[/bold magenta]\n")

    checkpoint_name = "pipeline_checkpoint"

    # Phase 0: Initialize database
    console.print("[bold]Phase 0: Initialize Database[/bold]")
    init_db()
    console.print()

    # Phase 1: Extract
    if not skip_extract:
        console.print("[bold]Phase 1: Extract Skills[/bold]")
        extract(
            dataset_path=dataset_path,
            batch_size=50,
            limit=limit,
            checkpoint_name=checkpoint_name,
            no_resume=False,
        )
        console.print()

    # Phase 2: Normalize
    console.print("[bold]Phase 2: Normalize Skills[/bold]")
    normalize(checkpoint_name=checkpoint_name)
    console.print()

    # Phase 3: Infer Hierarchy
    console.print("[bold]Phase 3: Infer Hierarchies[/bold]")
    infer_hierarchy()
    console.print()

    # Phase 3.5: Generate Descriptions
    console.print("[bold]Phase 3.5: Generate Job Descriptions[/bold]")
    generate_descriptions(checkpoint_name=checkpoint_name)
    console.print()

    # Phase 4: Load into database
    console.print("[bold]Phase 4: Load into Database[/bold]")
    load_db(dataset_path=dataset_path, checkpoint_name=checkpoint_name)
    console.print()

    # Phase 5: Show stats
    console.print("[bold]Phase 5: Database Statistics[/bold]")
    stats()
    console.print()

    console.print("[bold green]═══════════════════════════════════════════[/bold green]")
    console.print("[bold green]  ✓ Pipeline Complete!                   [/bold green]")
    console.print("[bold green]═══════════════════════════════════════════[/bold green]\n")

    console.print("[cyan]Next steps:[/cyan]")
    console.print("  1. Start API server: python scripts/cli.py serve")
    console.print("  2. Access API docs: http://localhost:8000/docs")
    console.print("  3. Access Neo4j Browser: http://localhost:7474")


if __name__ == "__main__":
    app()
