#!/usr/bin/env python3
"""
Database migration: Add entity management system

Adds:
- entities table
- entity fields to ai_summaries table
- entity fields to insights table

Safe to run multiple times (checks if columns/tables exist first).
"""

import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import DB_PATH, engine
from app.models import Base

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def table_exists(cursor, table_name):
    """Check if a table exists."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def migrate():
    """Run the migration."""
    print(f"Migrating database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Create entities table if it doesn't exist
        if not table_exists(cursor, "entities"):
            print("Creating entities table...")
            cursor.execute("""
                CREATE TABLE entities (
                    id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    entity_identifier TEXT,
                    entity_metadata TEXT,
                    owner_id TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    FOREIGN KEY(owner_id) REFERENCES entities(id)
                )
            """)
            print("✓ Created entities table")
        else:
            print("✓ entities table already exists")

        # 2. Add entity fields to ai_summaries table
        ai_summaries_changes = [
            ("entity_id", "ALTER TABLE ai_summaries ADD COLUMN entity_id TEXT"),
            ("entity_confidence", "ALTER TABLE ai_summaries ADD COLUMN entity_confidence REAL"),
            ("suggested_entity_data", "ALTER TABLE ai_summaries ADD COLUMN suggested_entity_data TEXT"),
        ]

        for column, sql in ai_summaries_changes:
            if not column_exists(cursor, "ai_summaries", column):
                print(f"Adding {column} to ai_summaries...")
                cursor.execute(sql)
                print(f"✓ Added {column}")
            else:
                print(f"✓ {column} already exists in ai_summaries")

        # 3. Add entity fields to insights table
        insights_changes = [
            ("entity_id", "ALTER TABLE insights ADD COLUMN entity_id TEXT"),
            ("entity_name", "ALTER TABLE insights ADD COLUMN entity_name TEXT"),
            ("entity_type", "ALTER TABLE insights ADD COLUMN entity_type TEXT"),
        ]

        for column, sql in insights_changes:
            if not column_exists(cursor, "insights", column):
                print(f"Adding {column} to insights...")
                cursor.execute(sql)
                print(f"✓ Added {column}")
            else:
                print(f"✓ {column} already exists in insights")

        # 4. Create default "Family" entity if entities table is empty
        cursor.execute("SELECT COUNT(*) FROM entities")
        if cursor.fetchone()[0] == 0:
            print("Creating default 'Family' entity...")
            from datetime import datetime, timezone
            import uuid
            cursor.execute("""
                INSERT INTO entities (id, entity_type, entity_name, entity_identifier, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                "family",
                "Family",
                None,
                1,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            print("✓ Created default 'Family' entity")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
