#!/usr/bin/env python3
"""
Apply taxonomy_versions schema migration
"""
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

def apply_migration():
    print("🔧 Applying taxonomy_versions schema migration...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create taxonomy_versions table
    print("📋 Creating taxonomy_versions table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS taxonomy_versions (
          version_id SERIAL PRIMARY KEY,
          version_number INTEGER NOT NULL UNIQUE,
          taxonomy_snapshot JSONB NOT NULL,
          cluster_stats JSONB,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by VARCHAR(100) DEFAULT 'system',
          change_summary TEXT,
          trigger_type VARCHAR(50)
        );
    """)

    # Create indexes
    print("📊 Creating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_version_number ON taxonomy_versions(version_number)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_taxonomy_created_at ON taxonomy_versions(created_at)")

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Migration applied successfully!")

if __name__ == "__main__":
    apply_migration()
