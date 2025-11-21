"""Typer CLI entrypoint."""

from __future__ import annotations

import logging
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from . import __version__
from .booster import suggest_boosters
from .diagnostics import generate_questions
from .pipeline import ingest
from .profiles import mock_profile
from .recommendation import recommend
from .vector_store import VectorStore

app = typer.Typer(help="S³ — Skoda Smart Stream CLI")
console = Console()
logging.basicConfig(level=logging.INFO)


@app.callback()
def main() -> None:
    """Base callback for Typer CLI."""


@app.command()
def version() -> None:
    """Print version."""
    console.print(f"S³ version {__version__}")


@app.command()
def run_ingest() -> None:
    """Chunk and embed all data."""
    ingest()
    console.print("[green]Ingestion complete[/green]")


def _load_store() -> VectorStore:
    store = VectorStore()
    store.load()
    return store


@app.command()
def demo(user_id: str = typer.Argument("anna")) -> None:
    """Show recommendations, diagnostics, and boosters for a persona."""
    profile = mock_profile(user_id)
    store = _load_store()
    recs = recommend(profile, store)
    questions = generate_questions(profile)
    boosters = suggest_boosters(profile)

    _render_recs(recs)
    _render_questions(questions)
    _render_boosters(boosters)


def _render_recs(recs) -> None:
    table = Table(title="Recommended Micro-Modules", box=box.ROUNDED)
    table.add_column("Chunk ID")
    table.add_column("Reason")
    table.add_column("Score", justify="right")
    for rec in recs:
        table.add_row(rec.chunk_id, rec.reason, f"{rec.score:.2f}")
    console.print(table)


def _render_questions(questions) -> None:
    table = Table(title="Micro-Questions", box=box.SIMPLE_HEAD)
    table.add_column("Skill")
    table.add_column("Prompt")
    table.add_column("Remediation")
    for q in questions:
        table.add_row(q.skill, q.question, q.remediation)
    console.print(table)


def _render_boosters(boosters) -> None:
    table = Table(title="Productivity Boosters")
    table.add_column("Skill")
    table.add_column("Title")
    table.add_column("Description")
    for booster in boosters:
        table.add_row(booster.skill, booster.title, booster.description)
    console.print(table)


if __name__ == "__main__":
    app()

