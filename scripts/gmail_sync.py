#!/usr/bin/env python3
"""
Gmail sync script for automated ingestion.
Designed to be run by cron every 15 minutes.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
LOG_DIR = project_root / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "gmail_sync.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # Also print to console
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run Gmail ingestion with error handling."""
    logger.info("=" * 60)
    logger.info("Gmail sync started")

    try:
        # Import here to catch import errors
        from scripts.gmail_ingest import (
            get_gmail_service,
            get_label_id,
            email_already_ingested,
            ingest_message,
            LABEL_NAME,
        )
        from app.db import Base, engine

        # Ensure DB tables exist
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized")

        # Authenticate
        logger.info("Authenticating with Gmail API...")
        service = get_gmail_service()
        logger.info("✓ Authenticated")

        # Find label
        logger.info(f"Finding label '{LABEL_NAME}'...")
        label_id = get_label_id(service, LABEL_NAME)
        if not label_id:
            logger.warning(f"Label '{LABEL_NAME}' not found. Exiting.")
            return 0

        logger.info(f"✓ Found label ID: {label_id}")

        # Fetch messages (limited to 10 per run)
        logger.info(f"Fetching messages with label '{LABEL_NAME}'...")
        results = service.users().messages().list(
            userId="me",
            labelIds=[label_id],
            maxResults=10
        ).execute()

        messages = results.get("messages", [])
        logger.info(f"Found {len(messages)} message(s)")

        if not messages:
            logger.info("No messages to process")
            return 0

        # Ingest messages
        ingested_count = 0
        skipped_count = 0
        error_count = 0

        for msg in messages:
            msg_id = msg["id"]
            try:
                if email_already_ingested(msg_id):
                    logger.debug(f"Skipped {msg_id} (already ingested)")
                    skipped_count += 1
                else:
                    ingest_message(service, msg_id)
                    logger.info(f"✓ Ingested {msg_id}")
                    ingested_count += 1
            except Exception as e:
                logger.error(f"✗ Failed to ingest {msg_id}: {e}", exc_info=True)
                error_count += 1

        # Summary
        logger.info(f"Sync complete: {ingested_count} ingested, {skipped_count} skipped, {error_count} errors")
        return 0 if error_count == 0 else 1

    except Exception as e:
        logger.error(f"Gmail sync failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
