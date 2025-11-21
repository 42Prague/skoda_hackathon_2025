#!/usr/bin/env python3
"""
Apply canonical_events schema migration
"""
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

def apply_migration():
    print("🔧 Applying canonical_events schema migration...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create canonical_events table
    print("📋 Creating canonical_events table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS canonical_events (
          canonical_id SERIAL PRIMARY KEY,
          employee_id VARCHAR(50) NOT NULL,
          hire_date DATE,
          department VARCHAR(100),
          position VARCHAR(100),
          skill_name VARCHAR(200) NOT NULL,
          category VARCHAR(100),
          event_type VARCHAR(50) NOT NULL,
          event_date DATE NOT NULL,
          source VARCHAR(100) NOT NULL,
          confidence DECIMAL(3,2) DEFAULT 1.0,
          raw_source_row JSONB,
          source_event_id INTEGER REFERENCES skill_events(event_id),
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(employee_id, skill_name, event_date, source)
        );
    """)

    # Create indexes
    print("📊 Creating indexes...")
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_canonical_employee ON canonical_events(employee_id)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_skill_name ON canonical_events(skill_name)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_event_date ON canonical_events(event_date)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_source ON canonical_events(source)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_category ON canonical_events(category)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_employee_date ON canonical_events(employee_id, event_date)",
        "CREATE INDEX IF NOT EXISTS idx_canonical_skill_date ON canonical_events(skill_name, event_date)"
    ]

    for idx_sql in indexes:
        cur.execute(idx_sql)

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Migration applied successfully!")

if __name__ == "__main__":
    apply_migration()
