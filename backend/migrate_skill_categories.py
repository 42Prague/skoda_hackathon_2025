#!/usr/bin/env python3
"""
Migrate skill categories from CSV to PostgreSQL database
Updates skills table with correct category assignments
"""
import os
import psycopg2
import pandas as pd

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required")

# Skill category mapping from CSV
SKILL_CATEGORIES = {
    # Legacy Engineering
    'CAD': 'legacy_engineering',
    'Mechanical Design': 'legacy_engineering',
    'CNC Programming': 'legacy_engineering',
    'CATIA': 'legacy_engineering',
    'AutoCAD': 'legacy_engineering',
    'Quality Control': 'legacy_engineering',

    # Software & Cloud
    'Python': 'software_cloud',
    'JavaScript': 'software_cloud',
    'React': 'software_cloud',
    'AWS': 'software_cloud',
    'Azure': 'software_cloud',
    'Docker': 'software_cloud',
    'Kubernetes': 'software_cloud',
    'CI/CD': 'software_cloud',
    'Microservices': 'software_cloud',

    # E-Mobility
    'Battery Systems': 'e_mobility',
    'Electric Powertrain': 'e_mobility',
    'Charging Infrastructure': 'e_mobility',
    'Energy Management': 'e_mobility',
    'Thermal Management': 'e_mobility',

    # AI & Emerging Tech
    'Machine Learning': 'ai_emerging',
    'TensorFlow': 'ai_emerging',
    'PyTorch': 'ai_emerging',
    'LLM Integration': 'ai_emerging',
    'Computer Vision': 'ai_emerging',
    'NLP': 'ai_emerging'
}

def apply_migration():
    print("🔧 Migrating skill categories...")

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    try:
        # Update each skill with its category
        updated_count = 0
        missing_count = 0

        for skill_name, category in SKILL_CATEGORIES.items():
            cur.execute("""
                UPDATE skills
                SET skill_category = %s
                WHERE skill_name = %s
            """, (category, skill_name))

            if cur.rowcount > 0:
                print(f"  ✓ Updated '{skill_name}' → {category}")
                updated_count += 1
            else:
                print(f"  ⚠️  Skill '{skill_name}' not found in database")
                missing_count += 1

        # Check skills without categories
        cur.execute("""
            SELECT skill_name
            FROM skills
            WHERE skill_category IS NULL OR skill_category = 'General'
            ORDER BY skill_name
        """)

        uncategorized = cur.fetchall()

        if uncategorized:
            print(f"\n⚠️  {len(uncategorized)} skills remain uncategorized:")
            for (skill,) in uncategorized[:10]:  # Show first 10
                print(f"     - {skill}")
            if len(uncategorized) > 10:
                print(f"     ... and {len(uncategorized) - 10} more")

        conn.commit()

        print(f"\n✅ Migration complete!")
        print(f"   Updated: {updated_count} skills")
        print(f"   Missing: {missing_count} skills")
        print(f"   Uncategorized: {len(uncategorized)} skills")

    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise

    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    apply_migration()
