#!/usr/bin/env python3
"""
Database migration: Add display_title column to items table

Adds:
- display_title TEXT column to items table (nullable)

This allows custom/smart titles while preserving original_filename as source of truth.
Safe to run multiple times (checks if column exists first).
"""

import sqlite3
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import DB_PATH

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

def migrate():
    """Run the migration."""
    print(f"Migrating database: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Add display_title column to items table
        if not column_exists(cursor, "items", "display_title"):
            print("Adding display_title column to items table...")
            cursor.execute("ALTER TABLE items ADD COLUMN display_title TEXT")
            print("✓ Added display_title column")
        else:
            print("✓ display_title column already exists")

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
