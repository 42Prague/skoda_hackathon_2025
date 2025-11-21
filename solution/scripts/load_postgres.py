#!/usr/bin/env python3
"""
Load synthetic data from CSV files into PostgreSQL database.
Creates tables and loads data with proper column mappings.
"""
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import json
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL"
)

SYNTHETIC_DATA_DIR = "synthetic_data"


def get_db_engine():
    """Get SQLAlchemy engine"""
    return create_engine(DATABASE_URL)


def _normalize_name(n: str) -> str:
    if n is None:
        return ""
    return " ".join(n.strip().lower().split())


def load_skills_from_json(path: str) -> List[Dict]:
    """Load skills from a JSON file and return as list of dicts."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    # ensure each item is a dict
    items = [i for i in data if isinstance(i, dict)]
    return items


def dedupe_skills_by_name(skills: List[Dict]) -> List[Dict]:
    """Deduplicate skills by normalized name, keeping the first occurrence."""
    seen = set()
    out = []
    for s in skills:
        name = s.get("name") or ""
        key = _normalize_name(name)
        if not key:
            # skip items without a name
            continue
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "skill_id": s.get("skill_id"),
            "skill_name": name.strip(),
            "category": s.get("category"),
            "description": s.get("description"),
        })
    return out



def insert_skills(engine, skills: List[Dict]):
    """Insert deduplicated skills into the DB. Skips rows that conflict on skill_id."""
    insert_sql = text("""
    INSERT INTO skill_list (skill_id, skill_name, category, description)
    VALUES (:skill_id, :skill_name, :category, :description)
    """)
    with engine.begin() as conn:
        for s in skills:
            params = {
                "skill_id": s.get("skill_id"),
                "skill_name": s.get("skill_name"),
                "category": s.get("category"),
                "description": s.get("description"),
            }
            conn.execute(insert_sql, params)


def main():
    if not DATABASE_URL:
        print("DATABASE_URL not set", file=sys.stderr)
        sys.exit(2)

    data_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "unique_skills.json")
    if not os.path.exists(data_path):
        print(f"Data file not found: {data_path}", file=sys.stderr)
        sys.exit(2)

    try:
        raw = load_skills_from_json(data_path)
        deduped = dedupe_skills_by_name(raw)
        engine = get_db_engine()
        insert_skills(engine, deduped)
        print(f"Inserted {len(deduped)} deduplicated skills (attempted).")
    except (IOError) as e:
        print(f"Failed to read/parse JSON: {e}", file=sys.stderr)
        sys.exit(3)
    except SQLAlchemyError as e:
        print(f"Database error: {e}", file=sys.stderr)
        sys.exit(4)


if __name__ == "__main__":
    main()


