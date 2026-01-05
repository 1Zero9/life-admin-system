#!/usr/bin/env python3
"""
Database backup script.
Creates SQLite backup and uploads to R2 with timestamp.
Keeps last 30 daily backups.
"""

import os
import sys
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import boto3
from botocore.client import Config

# Set up logging
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "backup.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = project_root / "data"
DB_FILE = DATA_DIR / "life_admin.sqlite3"
BACKUP_DIR = project_root / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")
R2_BACKUP_PREFIX = "backups"

# Keep last 30 backups in R2
MAX_BACKUPS_TO_KEEP = 30


def create_backup():
    """Create local backup of database."""
    if not DB_FILE.exists():
        logger.error(f"Database not found: {DB_FILE}")
        return None

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"life_admin_{timestamp}.sqlite3"
    backup_path = BACKUP_DIR / backup_filename

    logger.info(f"Creating backup: {backup_filename}")

    try:
        # Use SQLite backup API via sqlite3 module
        import sqlite3

        # Connect to source and destination
        source_conn = sqlite3.connect(str(DB_FILE))
        backup_conn = sqlite3.connect(str(backup_path))

        # Perform backup
        with backup_conn:
            source_conn.backup(backup_conn)

        source_conn.close()
        backup_conn.close()

        file_size = backup_path.stat().st_size
        logger.info(f"✓ Backup created: {backup_filename} ({file_size:,} bytes)")
        return backup_path

    except Exception as e:
        logger.error(f"Failed to create backup: {e}", exc_info=True)
        return None


def upload_to_r2(backup_path):
    """Upload backup to R2."""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET]):
        logger.warning("R2 not configured. Skipping upload.")
        return False

    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

        object_key = f"{R2_BACKUP_PREFIX}/{backup_path.name}"

        logger.info(f"Uploading to R2: {object_key}")
        s3_client.upload_file(str(backup_path), R2_BUCKET, object_key)
        logger.info(f"✓ Uploaded to R2: {object_key}")

        return True

    except Exception as e:
        logger.error(f"Failed to upload to R2: {e}", exc_info=True)
        return False


def cleanup_old_backups():
    """Remove old backups from R2 (keep last 30)."""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET]):
        return

    try:
        s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

        # List all backups
        response = s3_client.list_objects_v2(
            Bucket=R2_BUCKET,
            Prefix=f"{R2_BACKUP_PREFIX}/",
        )

        objects = response.get("Contents", [])
        if not objects:
            return

        # Sort by last modified (oldest first)
        objects.sort(key=lambda x: x["LastModified"])

        # Delete oldest if we have more than MAX_BACKUPS_TO_KEEP
        to_delete = len(objects) - MAX_BACKUPS_TO_KEEP
        if to_delete > 0:
            logger.info(f"Cleaning up {to_delete} old backup(s)")
            for obj in objects[:to_delete]:
                key = obj["Key"]
                s3_client.delete_object(Bucket=R2_BUCKET, Key=key)
                logger.info(f"Deleted old backup: {key}")

    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}", exc_info=True)


def cleanup_local_backups():
    """Remove local backups older than 7 days."""
    try:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)

        deleted_count = 0
        for backup_file in BACKUP_DIR.glob("life_admin_*.sqlite3"):
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                backup_file.unlink()
                logger.info(f"Deleted local backup: {backup_file.name}")
                deleted_count += 1

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} local backup(s)")

    except Exception as e:
        logger.error(f"Failed to cleanup local backups: {e}", exc_info=True)


def main():
    """Run backup process."""
    logger.info("=" * 60)
    logger.info("Database backup started")

    # Create backup
    backup_path = create_backup()
    if not backup_path:
        logger.error("Backup failed")
        return 1

    # Upload to R2
    upload_success = upload_to_r2(backup_path)

    # Cleanup
    if upload_success:
        cleanup_old_backups()
    cleanup_local_backups()

    logger.info("Backup complete")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
