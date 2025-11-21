"""
Canonical Events Persistence Pipeline
Normalizes and stores events from various sources into canonical_events table
"""
import os
import psycopg2
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import json
import yaml


def get_db_connection():
    """Get PostgreSQL connection from environment"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please configure DATABASE_URL with your PostgreSQL connection string."
        )
    return psycopg2.connect(database_url)


def load_mappings() -> Dict:
    """Load canonical mappings from YAML"""
    mappings_path = os.path.join(
        os.path.dirname(__file__), '..', 'parsers', 'mappings.yaml'
    )
    with open(mappings_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def normalize_event(row: Dict, source_format: str, mappings: Dict) -> Optional[Dict]:
    """
    Normalize a single event row to canonical format

    Args:
        row: Raw data row (dict)
        source_format: Source format key from mappings.yaml
        mappings: Full mappings configuration

    Returns:
        Canonical event dict or None if validation fails
    """
    if source_format not in mappings['sources']:
        return None

    config = mappings['sources'][source_format]
    field_mappings = config.get('mappings', {})
    transforms = config.get('transforms', {})

    canonical = {}

    # Apply field mappings
    for canonical_field, source_field in field_mappings.items():
        if isinstance(source_field, list):
            # Combine multiple fields
            values = [str(row.get(f, '')).strip() for f in source_field if row.get(f)]
            if transforms.get(canonical_field, {}).get('combine_distinct'):
                sep = transforms[canonical_field].get('separator', ' | ')
                canonical[canonical_field] = sep.join(set(v for v in values if v))
            else:
                canonical[canonical_field] = values[0] if values else None
        elif source_field == 'NOW':
            # Use current date
            canonical[canonical_field] = date.today().isoformat()
        else:
            # Direct mapping
            canonical[canonical_field] = row.get(source_field)

    # Apply transforms
    for field, transform_rules in transforms.items():
        if field not in canonical or canonical[field] is None:
            # Handle missing values
            if 'default' in transform_rules:
                canonical[field] = transform_rules['default']
            elif 'if_missing' in transform_rules:
                # Generate value (e.g., EMP_{row_index})
                canonical[field] = transform_rules['if_missing']

        if field in canonical and canonical[field] is not None:
            value = canonical[field]

            # Parse dates
            if 'parse_date_formats' in transform_rules and value:
                for fmt in transform_rules['parse_date_formats']:
                    try:
                        parsed = datetime.strptime(str(value), fmt).date()
                        canonical[field] = parsed.isoformat()
                        break
                    except ValueError:
                        continue

            # Trim strings
            if transform_rules.get('trim') and isinstance(value, str):
                canonical[field] = value.strip()

    # Validation
    validation = config.get('validation', {})
    required_fields = validation.get('required', [])
    for req_field in required_fields:
        if not canonical.get(req_field):
            return None  # Skip invalid rows

    # Store raw source row for audit
    canonical['raw_source_row'] = json.dumps(row)

    return canonical


def persist_canonical_event(
    conn,
    canonical_event: Dict,
    source_event_id: Optional[int] = None
) -> int:
    """
    Persist a single canonical event to database

    Args:
        conn: Database connection
        canonical_event: Normalized event dict
        source_event_id: Optional link to skill_events table

    Returns:
        canonical_id of inserted event
    """
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO canonical_events (
                employee_id, hire_date, department, position,
                skill_name, category, event_type, event_date,
                source, confidence, raw_source_row, source_event_id
            ) VALUES (
                %(employee_id)s, %(hire_date)s, %(department)s, %(position)s,
                %(skill_name)s, %(category)s, %(event_type)s, %(event_date)s,
                %(source)s, %(confidence)s, %(raw_source_row)s, %(source_event_id)s
            )
            ON CONFLICT (employee_id, skill_name, event_date, source)
            DO UPDATE SET
                department = EXCLUDED.department,
                position = EXCLUDED.position,
                category = EXCLUDED.category,
                confidence = EXCLUDED.confidence,
                raw_source_row = EXCLUDED.raw_source_row,
                source_event_id = EXCLUDED.source_event_id
            RETURNING canonical_id
        """, {
            'employee_id': canonical_event.get('employee_id'),
            'hire_date': canonical_event.get('hire_date'),
            'department': canonical_event.get('department'),
            'position': canonical_event.get('position'),
            'skill_name': canonical_event.get('skill_name'),
            'category': canonical_event.get('category'),
            'event_type': canonical_event.get('event_type'),
            'event_date': canonical_event.get('event_date'),
            'source': canonical_event.get('source'),
            'confidence': canonical_event.get('confidence', 1.0),
            'raw_source_row': canonical_event.get('raw_source_row'),
            'source_event_id': source_event_id
        })

        canonical_id = cur.fetchone()[0]
        conn.commit()
        return canonical_id

    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Failed to persist canonical event: {e}")
        raise
    finally:
        cur.close()


def persist_canonical_events_batch(
    parsed_data: Dict,
    source_format: str
) -> Dict:
    """
    Persist batch of canonical events from parsed data

    Args:
        parsed_data: Output from parser (with 'rows' key)
        source_format: Format identifier (e.g., 'format3_lms')

    Returns:
        Dict with persistence statistics
    """
    conn = get_db_connection()
    mappings = load_mappings()

    rows = parsed_data.get('rows', [])
    stats = {
        'total_rows': len(rows),
        'canonical_events_created': 0,
        'skipped_invalid': 0,
        'errors': []
    }

    for i, row in enumerate(rows):
        try:
            # Normalize to canonical format
            canonical_event = normalize_event(row, source_format, mappings)

            if canonical_event is None:
                stats['skipped_invalid'] += 1
                continue

            # Persist to database
            canonical_id = persist_canonical_event(conn, canonical_event)
            stats['canonical_events_created'] += 1

        except Exception as e:
            stats['errors'].append(f"Row {i}: {str(e)}")

    conn.close()

    return stats


def migrate_existing_skill_events():
    """
    One-time migration: Convert existing skill_events to canonical_events
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch all skill_events
    cur.execute("""
        SELECT
            se.event_id,
            se.employee_id,
            e.hire_date,
            e.department,
            e.position,
            s.skill_name,
            s.skill_category,
            se.event_type,
            se.event_date,
            se.source,
            se.proficiency_level
        FROM skill_events se
        JOIN skills s ON se.skill_id = s.skill_id
        LEFT JOIN employees e ON se.employee_id = e.employee_id
        ORDER BY se.event_id
    """)

    migrated = 0
    skipped = 0

    for row in cur.fetchall():
        event_id, emp_id, hire_date, dept, pos, skill_name, category, event_type, event_date, source, prof = row

        canonical_event = {
            'employee_id': emp_id,
            'hire_date': hire_date.isoformat() if hire_date else None,
            'department': dept,
            'position': pos,
            'skill_name': skill_name,
            'category': category,
            'event_type': event_type or 'acquired',
            'event_date': event_date.isoformat(),
            'source': source or 'LEGACY',
            'confidence': 0.95,
            'raw_source_row': json.dumps({
                'migrated_from': 'skill_events',
                'proficiency_level': prof
            })
        }

        try:
            persist_canonical_event(conn, canonical_event, source_event_id=event_id)
            migrated += 1
        except Exception as e:
            print(f"[WARN] Skip event {event_id}: {e}")
            skipped += 1

    cur.close()
    conn.close()

    print(f"✅ Migration complete: {migrated} migrated, {skipped} skipped")
    return {'migrated': migrated, 'skipped': skipped}


if __name__ == "__main__":
    # Run migration
    print("🔄 Starting canonical_events migration...")
    result = migrate_existing_skill_events()
    print(f"📊 Result: {result}")
