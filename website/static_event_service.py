
import json
import os
import shutil
import logging
import secrets
from datetime import datetime

from django.conf import settings
from django.utils.text import get_valid_filename, slugify

from .models import EventImage

# ── Paths ──────────────────────────────────────────────────────────────────────
EVENTS_ROOT = os.path.join(settings.BASE_DIR, "static", "images", "events")
STATIC_URL_PREFIX = "/static/images/events"   # used to build URLs in templates
EVENT_DB_URL_PREFIX = "/events/image"
logger = logging.getLogger(__name__)


def _ensure_dirs():
    os.makedirs(EVENTS_ROOT, exist_ok=True)


def _meta_path(folder):
    return os.path.join(EVENTS_ROOT, folder, "meta.json")


def _read_meta(folder):
    path = _meta_path(folder)

    if not os.path.exists(path):
        return {}

    if not os.path.isfile(path):
        logger.warning("Event metadata path is not a regular file.")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to read event metadata.")
        return {}


def _write_meta(folder, meta: dict):
    path = _meta_path(folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

def update_event_meta(folder, title_en, title_hi, thumbnail=None):
    """
    Update titles + optional thumbnail safely
    """

    folder_path = os.path.join(EVENTS_ROOT, folder)

    if not os.path.exists(folder_path):
        raise Exception(f"Event folder '{folder}' does not exist.")

    meta_path = _meta_path(folder)

    meta = {}

    # Read existing meta safely
    if os.path.exists(meta_path) and os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            logger.exception("Failed reading existing event metadata.")

    # Update titles
    if title_en:
        meta["title_en"] = title_en.strip()
    if title_hi:
        meta["title_hi"] = (title_hi or title_en).strip()

    # Thumbnail support
    if thumbnail:
        db_exists = EventImage.objects.filter(folder=folder, stored_name=thumbnail).exists()
        if thumbnail in os.listdir(folder_path) or db_exists:
            meta["thumbnail"] = thumbnail
        else:
            logger.warning("Requested event thumbnail was not found in the event folder.")

    # Save
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception("Failed writing event metadata.")
        raise Exception("Could not update event metadata.")
def _format_title(slug):
    return slug.replace("-", " ").title()


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def _event_image_url(folder, stored_name):
    return f"{EVENT_DB_URL_PREFIX}/{folder}/{stored_name}/"


def _safe_folder_name(event_date, event_name):
    slug = slugify(event_name or "", allow_unicode=False) or "event"
    return f"{event_date}_{slug}"


def _validate_image(file):
    ext = os.path.splitext(file.name)[1].lower()
    content_type = getattr(file, "content_type", "")

    if file.size > MAX_IMAGE_SIZE:
        raise Exception(f"{file.name} exceeds 5MB limit.")
    if ext not in IMAGE_EXTS:
        raise Exception(f"{file.name} is not an allowed image type.")
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise Exception(f"{file.name} has an unsupported content type.")

    return ext, content_type


def _store_event_image(folder, file):
    ext, content_type = _validate_image(file)
    original_name = get_valid_filename(os.path.basename(file.name))
    stored_name = f"{secrets.token_urlsafe(18)}{ext}"
    data = b"".join(file.chunks())

    EventImage.objects.create(
        folder=folder,
        stored_name=stored_name,
        original_name=original_name,
        content_type=content_type,
        size=len(data),
        data=data,
    )


def get_all_events():
    """
    Scan EVENTS_ROOT, read each folder's meta.json, return sorted event list.
    """
    _ensure_dirs()
    events = []

    for folder_name in os.listdir(EVENTS_ROOT):
        folder_path = os.path.join(EVENTS_ROOT, folder_name)

        if not os.path.isdir(folder_path):
            continue

        # Collect legacy static images and database-backed uploads.
        legacy_image_files = [
            fname for fname in os.listdir(folder_path)
            if os.path.splitext(fname)[1].lower() in IMAGE_EXTS
        ]
        db_images = list(EventImage.objects.filter(folder=folder_name))

        # Sort by creation time (upload order)
        legacy_image_files.sort(
            key=lambda x: os.path.getctime(os.path.join(folder_path, x))
        )

        legacy_images = [
            f"{STATIC_URL_PREFIX}/{folder_name}/{fname}"
            for fname in legacy_image_files
        ]
        db_image_urls = [
            _event_image_url(folder_name, image.stored_name)
            for image in db_images
        ]
        images = legacy_images + db_image_urls

        if not images:
            continue   # skip empty folders

        # Parse date + slug from folder name
        try:
            if "_" in folder_name and folder_name[:4].isdigit():
                date_str, slug = folder_name.split("_", 1)
                event_date = datetime.strptime(date_str, "%Y-%m-%d")
                display_date = event_date.strftime("%d %B %Y")
                sort_date = event_date
            else:
                slug = folder_name
                display_date = "Unknown Date"
                sort_date = datetime(1900, 1, 1)
        except Exception:
            slug = folder_name
            display_date = "Unknown Date"
            sort_date = datetime(1900, 1, 1)

        meta = _read_meta(folder_name)
        title_en = meta.get("title_en") or _format_title(slug)
        title_hi = meta.get("title_hi") or title_en
        thumbnail_file = meta.get("thumbnail")

        db_names = {image.stored_name for image in db_images}
        if thumbnail_file and thumbnail_file in legacy_image_files:
            thumbnail = f"{STATIC_URL_PREFIX}/{folder_name}/{thumbnail_file}"
        elif thumbnail_file and thumbnail_file in db_names:
            thumbnail = _event_image_url(folder_name, thumbnail_file)
        else:
            thumbnail = images[0] if images else None

        events.append({
            "folder":    folder_name,
            "title":     title_en,
            "title_hi":  title_hi,
            "date":      display_date,
            "thumbnail": thumbnail,
            "images":    images,
            "sort_date": sort_date,
        })

    events.sort(key=lambda x: x["sort_date"], reverse=True)
    return events


def upload_event(event_date, event_name, event_name_hi, files):
    """
    Create a new event folder and save uploaded images in the database.
    Returns the folder name.
    """
    _ensure_dirs()

    folder_name = _safe_folder_name(event_date, event_name)
    folder_path = os.path.join(EVENTS_ROOT, folder_name)
    os.makedirs(folder_path, exist_ok=True)

    # Write meta
    _write_meta(folder_name, {
        "title_en": event_name.strip(),
        "title_hi": (event_name_hi or event_name).strip(),
    })

    # Save uploaded images as database records with unpredictable names.
    for file in files:
        _store_event_image(folder_name, file)

    return folder_name


def upload_images_to_existing_event(folder, files):
    """
    Add more images to an existing event folder.
    """
    folder_path = os.path.join(EVENTS_ROOT, folder)
    if not os.path.exists(folder_path):
        raise Exception(f"Event folder '{folder}' does not exist.")

    for file in files:
        _store_event_image(folder, file)


def delete_event(folder):
    """
    Delete an entire event folder (images + meta.json).
    """
    folder_path = os.path.join(EVENTS_ROOT, folder)
    EventImage.objects.filter(folder=folder).delete()
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
