"""
Taxonomy Versioning System
Tracks skill category clustering changes over time
"""
import os
import psycopg2
from typing import Dict, List, Any, Optional
import json
from datetime import datetime


def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    return psycopg2.connect(database_url)


def create_taxonomy_snapshot(
    category_mapping: Dict[str, List[str]],
    cluster_stats: Optional[Dict] = None,
    trigger_type: str = 'manual',
    created_by: str = 'system',
    change_summary: Optional[str] = None
) -> int:
    """
    Create a new taxonomy version snapshot

    Args:
        category_mapping: Dict of {category: [list of skills]}
        cluster_stats: Optional cluster metrics
        trigger_type: 'upload', 'manual', 'recompute', 'cluster_shift'
        created_by: User or system identifier
        change_summary: Human-readable description of changes

    Returns:
        version_number of created snapshot
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Get next version number
        cur.execute("SELECT COALESCE(MAX(version_number), 0) + 1 FROM taxonomy_versions")
        next_version = cur.fetchone()[0]

        # Insert new version
        cur.execute("""
            INSERT INTO taxonomy_versions (
                version_number, taxonomy_snapshot, cluster_stats,
                created_by, change_summary, trigger_type
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING version_id
        """, (
            next_version,
            json.dumps(category_mapping),
            json.dumps(cluster_stats) if cluster_stats else None,
            created_by,
            change_summary,
            trigger_type
        ))

        version_id = cur.fetchone()[0]
        conn.commit()

        return next_version

    except Exception as e:
        conn.rollback()
        raise Exception(f"Failed to create taxonomy snapshot: {e}")
    finally:
        cur.close()
        conn.close()


def get_latest_taxonomy() -> Dict[str, Any]:
    """
    Get the most recent taxonomy version

    Returns:
        {
            'version_number': int,
            'taxonomy': Dict[str, List[str]],
            'cluster_stats': Dict,
            'created_at': str,
            'change_summary': str
        }
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT version_number, taxonomy_snapshot, cluster_stats,
                   created_at, change_summary, created_by, trigger_type
            FROM taxonomy_versions
            ORDER BY version_number DESC
            LIMIT 1
        """)

        row = cur.fetchone()

        if not row:
            return {
                'version_number': 0,
                'taxonomy': {},
                'cluster_stats': {},
                'created_at': None,
                'change_summary': 'No taxonomy versions exist yet'
            }

        return {
            'version_number': row[0],
            'taxonomy': row[1],
            'cluster_stats': row[2] or {},
            'created_at': row[3].isoformat() if row[3] else None,
            'change_summary': row[4],
            'created_by': row[5],
            'trigger_type': row[6]
        }

    finally:
        cur.close()
        conn.close()


def get_taxonomy_version(version_number: int) -> Optional[Dict[str, Any]]:
    """Get a specific taxonomy version"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT version_number, taxonomy_snapshot, cluster_stats,
                   created_at, change_summary, created_by, trigger_type
            FROM taxonomy_versions
            WHERE version_number = %s
        """, (version_number,))

        row = cur.fetchone()

        if not row:
            return None

        return {
            'version_number': row[0],
            'taxonomy': row[1],
            'cluster_stats': row[2] or {},
            'created_at': row[3].isoformat() if row[3] else None,
            'change_summary': row[4],
            'created_by': row[5],
            'trigger_type': row[6]
        }

    finally:
        cur.close()
        conn.close()


def get_taxonomy_diff(version_from: int, version_to: int) -> Dict[str, Any]:
    """
    Calculate diff between two taxonomy versions

    Returns:
        {
            'version_from': int,
            'version_to': int,
            'added_categories': List[str],
            'removed_categories': List[str],
            'skills_added': Dict[category, List[skills]],
            'skills_removed': Dict[category, List[skills]],
            'skills_moved': List[{skill, from_category, to_category}],
            'summary': str
        }
    """
    v_from = get_taxonomy_version(version_from)
    v_to = get_taxonomy_version(version_to)

    if not v_from or not v_to:
        return {'error': 'One or both versions not found'}

    tax_from = v_from['taxonomy']
    tax_to = v_to['taxonomy']

    # Categories
    cats_from = set(tax_from.keys())
    cats_to = set(tax_to.keys())

    added_categories = list(cats_to - cats_from)
    removed_categories = list(cats_from - cats_to)

    # Skills
    skills_added = {}
    skills_removed = {}
    skills_moved = []

    # Create skill -> category mapping for both versions
    skill_to_cat_from = {}
    for cat, skills in tax_from.items():
        for skill in skills:
            skill_to_cat_from[skill] = cat

    skill_to_cat_to = {}
    for cat, skills in tax_to.items():
        for skill in skills:
            skill_to_cat_to[skill] = cat

    all_skills = set(skill_to_cat_from.keys()) | set(skill_to_cat_to.keys())

    for skill in all_skills:
        cat_from = skill_to_cat_from.get(skill)
        cat_to = skill_to_cat_to.get(skill)

        if cat_from and not cat_to:
            # Skill removed
            if cat_from not in skills_removed:
                skills_removed[cat_from] = []
            skills_removed[cat_from].append(skill)

        elif cat_to and not cat_from:
            # Skill added
            if cat_to not in skills_added:
                skills_added[cat_to] = []
            skills_added[cat_to].append(skill)

        elif cat_from != cat_to:
            # Skill moved between categories
            skills_moved.append({
                'skill': skill,
                'from_category': cat_from,
                'to_category': cat_to
            })

    # Generate summary
    total_changes = (
        len(added_categories) + len(removed_categories) +
        sum(len(s) for s in skills_added.values()) +
        sum(len(s) for s in skills_removed.values()) +
        len(skills_moved)
    )

    summary = f"{total_changes} total changes: "
    summary_parts = []
    if added_categories:
        summary_parts.append(f"{len(added_categories)} new categories")
    if removed_categories:
        summary_parts.append(f"{len(removed_categories)} removed categories")
    if skills_added:
        summary_parts.append(f"{sum(len(s) for s in skills_added.values())} skills added")
    if skills_removed:
        summary_parts.append(f"{sum(len(s) for s in skills_removed.values())} skills removed")
    if skills_moved:
        summary_parts.append(f"{len(skills_moved)} skills recategorized")

    summary += ", ".join(summary_parts) if summary_parts else "No changes"

    return {
        'version_from': version_from,
        'version_to': version_to,
        'added_categories': added_categories,
        'removed_categories': removed_categories,
        'skills_added': skills_added,
        'skills_removed': skills_removed,
        'skills_moved': skills_moved,
        'summary': summary
    }


def list_all_versions(limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all taxonomy versions (most recent first)

    Returns:
        List of {version_number, created_at, change_summary, trigger_type, created_by}
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT version_number, created_at, change_summary, trigger_type, created_by
            FROM taxonomy_versions
            ORDER BY version_number DESC
            LIMIT %s
        """, (limit,))

        versions = []
        for row in cur.fetchall():
            versions.append({
                'version_number': row[0],
                'created_at': row[1].isoformat() if row[1] else None,
                'change_summary': row[2],
                'trigger_type': row[3],
                'created_by': row[4]
            })

        return versions

    finally:
        cur.close()
        conn.close()
