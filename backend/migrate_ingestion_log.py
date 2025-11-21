#!/usr/bin/env python3
"""
Apply ingestion_log schema migration
"""
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

def apply_migration():
    print("🔧 Applying ingestion_log schema migration...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create ingestion_log table
    print("📋 Creating ingestion_log table...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_log (
          ingestion_id SERIAL PRIMARY KEY,
          filename VARCHAR(500),
          format_detected VARCHAR(100),
          rows_processed INTEGER,
          upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          status VARCHAR(50),
          anomaly_report TEXT,
          error_message TEXT
        );
    """)

    # Create indexes
    print("📊 Creating indexes...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_upload_date ON ingestion_log(upload_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_status ON ingestion_log(status)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_format ON ingestion_log(format_detected)")

    conn.commit()
    cur.close()
    conn.close()

    print("✅ Migration applied successfully!")

if __name__ == "__main__":
    apply_migration()
