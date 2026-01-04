"""
UI helper functions for the Vault interface.
Handles title normalization and date formatting.
"""

from datetime import datetime, timezone
from pathlib import Path
import re


def normalize_title(filename: str, source_type: str, created_at: datetime) -> str:
    """
    Convert a filename into a human-readable title.

    Rules:
    - Email subjects: strip .eml extension, replace underscores with spaces
    - Email attachments: strip extension only
    - Uploaded files: strip extension, replace underscores/hyphens with spaces
    - Images (IMG_xxxx pattern): "Image · [date]"
    """

    if not filename:
        return "Untitled"

    # For emails, strip .eml and clean up the subject
    if source_type == "email":
        title = Path(filename).stem  # removes .eml
        title = title.replace('_', ' ')
        # Clean up multiple spaces
        title = re.sub(r'\s+', ' ', title).strip()
        return title if title else "Email"

    # For attachments and uploads, process the filename
    stem = Path(filename).stem  # filename without extension

    # Check for generic camera filenames (IMG_1234, DSC_5678, etc.)
    if re.match(r'^(IMG|DSC|PHOTO|IMAGE)_?\d+$', stem, re.IGNORECASE):
        date_str = format_date_short(created_at)
        return f"Image · {date_str}"

    # For attachments, just remove extension (keep original formatting)
    if source_type == "attachment":
        return stem

    # For uploads, make more readable by replacing separators
    title = stem
    title = title.replace('_', ' ')
    title = title.replace('-', ' ')

    # Clean up multiple spaces
    title = re.sub(r'\s+', ' ', title).strip()

    return title if title else "Untitled"


def format_date_short(dt: datetime) -> str:
    """
    Format date for use in titles like "Image · 3 January"
    Returns: "3 January" format
    """
    return dt.strftime("%-d %B").lstrip("0")


def format_date_display(dt: datetime) -> str:
    """
    Format date for display in the item list.

    Rules:
    - Today: "Today, 14:32"
    - Yesterday: "Yesterday, 09:15"
    - This week: "Tuesday, 11:20"
    - This year: "15 March"
    - Older: "12 July 2024"
    """

    if not dt:
        return ""

    # Ensure we're working with UTC-aware datetime
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)

    # Calculate days difference
    dt_date = dt.date()
    now_date = now.date()
    days_diff = (now_date - dt_date).days

    time_str = dt.strftime("%H:%M")

    # Today
    if days_diff == 0:
        return f"Today, {time_str}"

    # Yesterday
    if days_diff == 1:
        return f"Yesterday, {time_str}"

    # This week (2-6 days ago)
    if days_diff < 7:
        day_name = dt.strftime("%A")
        return f"{day_name}, {time_str}"

    # This year
    if dt.year == now.year:
        return dt.strftime("%-d %B").lstrip("0")

    # Older
    return dt.strftime("%-d %B %Y").lstrip("0")


def format_source_type(source_type: str) -> str:
    """
    Format source_type for display.

    Returns:
    - "email" -> "Email"
    - "attachment" -> "Attachment"
    - "upload" -> "Upload"
    - None/empty -> "Upload" (default)
    """
    if not source_type:
        return "Upload"

    return source_type.capitalize()


def get_file_type(filename: str, content_type: str = None) -> str:
    """
    Determine file type from filename and content type.
    Returns a simple category for icon display.

    Categories:
    - email
    - pdf
    - image
    - word
    - excel
    - audio
    - video
    - archive
    - document (fallback)
    """
    if not filename:
        return "document"

    # Check content type first
    if content_type:
        if "pdf" in content_type.lower():
            return "pdf"
        if content_type.startswith("image/"):
            return "image"
        if "word" in content_type.lower() or "msword" in content_type.lower():
            return "word"
        if "excel" in content_type.lower() or "spreadsheet" in content_type.lower():
            return "excel"
        if content_type.startswith("audio/"):
            return "audio"
        if content_type.startswith("video/"):
            return "video"

    # Check file extension
    ext = Path(filename).suffix.lower()

    if ext in ['.eml', '.msg']:
        return "email"
    elif ext == '.pdf':
        return "pdf"
    elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic']:
        return "image"
    elif ext in ['.doc', '.docx']:
        return "word"
    elif ext in ['.xls', '.xlsx', '.csv']:
        return "excel"
    elif ext in ['.mp3', '.wav', '.m4a', '.aac', '.flac']:
        return "audio"
    elif ext in ['.mp4', '.mov', '.avi', '.mkv', '.webm']:
        return "video"
    elif ext in ['.zip', '.tar', '.gz', '.rar', '.7z']:
        return "archive"
    else:
        return "document"


def get_file_icon_color(file_type: str) -> str:
    """
    Get the color for a file type icon.
    Returns hex color code.
    """
    colors = {
        "email": "#5B9BD5",  # blue
        "pdf": "#D94A4A",    # red
        "image": "#70AD47",  # green
        "word": "#2B579A",   # dark blue
        "excel": "#217346",  # dark green
        "audio": "#8E44AD",  # purple
        "video": "#E67E22",  # orange
        "archive": "#95A5A6", # grey
        "document": "#7F8C8D", # dark grey
    }
    return colors.get(file_type, "#7F8C8D")
