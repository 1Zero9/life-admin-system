#!/usr/bin/env python3

import os
from dotenv import load_dotenv
load_dotenv()

import base64
import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from app.db import SessionLocal, Base, engine
from app.models import Item
from app.extractors import extract_pdf_text

import boto3
from botocore.client import Config

from email import message_from_bytes
from email.policy import default as email_policy

# OCR imports
try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

# -----------------------------
# Configuration
# -----------------------------

LABEL_NAME = "LifeAdmin"

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

OAUTH_CLIENT_FILE = "secrets/google_oauth_client.json"
TOKEN_FILE = "secrets/gmail_token.json"

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET")

EMAIL_PREFIX = "emails"
ATTACHMENT_PREFIX = "attachments"

# -----------------------------
# R2 client
# -----------------------------

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)

# -----------------------------
# Gmail helpers
# -----------------------------

def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                OAUTH_CLIENT_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_label_id(service, label_name):
    results = service.users().labels().list(userId="me").execute()
    for label in results.get("labels", []):
        if label["name"] == label_name:
            return label["id"]
    return None


def extract_plain_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                return part.get_content()
    else:
        return msg.get_content()
    return ""


def extract_text_from_image(image_path):
    """Extract text from image using OCR with optional preprocessing."""
    if not PYTESSERACT_AVAILABLE:
        return None

    try:
        # Load image
        image = Image.open(image_path)

        # Optional preprocessing with OpenCV
        if CV2_AVAILABLE:
            # Convert PIL image to numpy array
            img_array = np.array(image)

            # Convert to grayscale
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array

            # Apply thresholding to improve OCR accuracy
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Convert back to PIL Image
            image = Image.fromarray(thresh)

        # Run OCR
        text = pytesseract.image_to_string(image, lang="eng")

        # Clean up text
        text = text.strip()

        return text if text else None

    except Exception as e:
        print(f"  Warning: OCR extraction failed: {e}")
        return None


# -----------------------------
# Ingestion logic
# -----------------------------

def build_object_key(prefix, filename):
    now = datetime.now(timezone.utc)
    ext = Path(filename).suffix or ".bin"
    return f"{prefix}/{now:%Y}/{now:%m}/{uuid.uuid4()}{ext}"


def ingest_message(service, message_id):
    print(f"Fetching message {message_id}...")
    msg_data = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    raw_data = service.users().messages().get(
        userId="me", id=message_id, format="raw"
    ).execute()

    raw_bytes = base64.urlsafe_b64decode(raw_data["raw"].encode("utf-8"))
    email_msg = message_from_bytes(raw_bytes, policy=email_policy)

    subject = email_msg.get("subject", "(no subject)")
    sender = email_msg.get("from", "")
    date = email_msg.get("date", "")

    print(f"Subject: {subject}")
    print(f"From: {sender}")
    print(f"Date: {date}")

    body_text = extract_plain_text(email_msg)
    extracted_text = f"EMAIL:\nSubject: {subject}\nFrom: {sender}\nDate: {date}\n{body_text}"

    email_key = build_object_key(EMAIL_PREFIX, "email.eml")
    print(f"Uploading to R2: {email_key}")

    s3.put_object(
        Bucket=R2_BUCKET,
        Key=email_key,
        Body=raw_bytes,
        ContentType="message/rfc822",
    )

    db = SessionLocal()
    try:
        email_item = Item(
            original_filename=f"{subject}.eml".replace(" ", "_"),
            content_type="message/rfc822",
            bucket=R2_BUCKET,
            object_key=email_key,
            size_bytes=len(raw_bytes),
            extracted_text=extracted_text,
            parent_id=None,
            source_type="email",
            source_id=message_id,
        )
        db.add(email_item)
        db.commit()
        db.refresh(email_item)
    finally:
        db.close()

    # -----------------------------
    # Attachments
    # -----------------------------

    payload = msg_data.get("payload", {})
    parts = payload.get("parts", [])

    def walk_parts(parts):
        for part in parts:
            yield part
            if "parts" in part:
                yield from walk_parts(part["parts"])

    for part in walk_parts(parts):
        filename = part.get("filename")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if not filename:
            continue

        print(f"Ingesting attachment: {filename}")

        if attachment_id:
            attachment = service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=attachment_id,
            ).execute()
            data = base64.urlsafe_b64decode(attachment["data"])
        else:
            data = base64.urlsafe_b64decode(body.get("data", ""))

        # Check if attachment already exists (idempotency)
        source_id_value = attachment_id or part.get("partId")
        db_check = SessionLocal()
        try:
            existing = db_check.query(Item).filter(
                Item.source_type == "attachment",
                Item.source_id == source_id_value,
                Item.parent_id == email_item.id
            ).first()
            if existing:
                print(f"  Skipping {filename} (already ingested)")
                continue
        finally:
            db_check.close()

        attachment_key = build_object_key(ATTACHMENT_PREFIX, filename)

        s3.put_object(
            Bucket=R2_BUCKET,
            Key=attachment_key,
            Body=data,
            ContentType=part.get("mimeType"),
        )

        # Extract text from PDF attachments
        extracted_text = None
        mime_type = part.get("mimeType", "")
        is_pdf = mime_type == "application/pdf" or filename.lower().endswith(".pdf")
        is_image = (
            mime_type in ("image/png", "image/jpeg", "image/jpg")
            or filename.lower().endswith((".jpg", ".jpeg", ".png"))
        )

        # Guardrails
        file_size_bytes = len(data)
        size_threshold = 10 * 1024 * 1024  # 10 MB

        if is_pdf:
            tmp_file = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp.write(data)
                    tmp_file = tmp.name

                text = extract_pdf_text(tmp_file)
                if text:
                    # Add quality marker prefix
                    extracted_text = f"PDF:\n{text}"
                    char_count = len(text)
                    print(f"  Extracted {char_count} characters from PDF attachment {filename}")
            except Exception as e:
                print(f"  Warning: PDF extraction failed for {filename}: {e}")
            finally:
                if tmp_file and os.path.exists(tmp_file):
                    os.unlink(tmp_file)

        elif is_image and PYTESSERACT_AVAILABLE:
            # OCR guardrails
            if file_size_bytes > size_threshold:
                print(f"  Skipping OCR for {filename} (size {file_size_bytes / 1024 / 1024:.1f} MB exceeds {size_threshold / 1024 / 1024:.0f} MB limit)")
            else:
                tmp_file = None
                try:
                    # Determine file extension
                    ext = Path(filename).suffix.lower() or ".png"

                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
                        tmp.write(data)
                        tmp_file = tmp.name

                    text = extract_text_from_image(tmp_file)
                    if text:
                        # Add quality marker prefix
                        extracted_text = f"OCR:\n{text}"
                        char_count = len(text)
                        print(f"  OCR extracted {char_count} characters from {filename}")
                except Exception as e:
                    print(f"  Warning: OCR extraction failed for {filename}: {e}")
                finally:
                    if tmp_file and os.path.exists(tmp_file):
                        os.unlink(tmp_file)

        db = SessionLocal()
        try:
            attachment_item = Item(
                original_filename=filename,
                content_type=part.get("mimeType"),
                bucket=R2_BUCKET,
                object_key=attachment_key,
                size_bytes=len(data),
                extracted_text=extracted_text,
                parent_id=email_item.id,
                source_type="attachment",
                source_id=attachment_id or part.get("partId"),
            )
            db.add(attachment_item)
            db.commit()
        finally:
            db.close()

    return email_item


def email_already_ingested(message_id):
    """Check if email already exists in database."""
    db = SessionLocal()
    try:
        existing = db.query(Item).filter(
            Item.source_type == "email",
            Item.source_id == message_id
        ).first()
        return existing is not None
    finally:
        db.close()


# -----------------------------
# Main
# -----------------------------

def main():
    print("Life Admin System - Gmail Ingestion")
    print("=" * 50)

    # Ensure DB tables exist
    Base.metadata.create_all(bind=engine)

    print("\nAuthenticating with Gmail API...")
    service = get_gmail_service()
    print("✓ Authenticated")

    print(f"\nFinding label '{LABEL_NAME}'...")
    label_id = get_label_id(service, LABEL_NAME)
    if not label_id:
        print("Label not found.")
        return

    print(f"✓ Found label ID: {label_id}")

    print(f"\nFetching latest 10 messages with label '{LABEL_NAME}'...")
    results = service.users().messages().list(
        userId="me", labelIds=[label_id], maxResults=10
    ).execute()

    messages = results.get("messages", [])
    print(f"Found {len(messages)} message(s)")

    if not messages:
        return

    print(f"\nIngesting messages...")
    for msg in messages:
        msg_id = msg["id"]
        if email_already_ingested(msg_id):
            print(f"  ↓ Skipped {msg_id} (already ingested)")
        else:
            ingest_message(service, msg_id)
            print(f"  ✓ Ingested {msg_id}")


if __name__ == "__main__":
    main()
