import os
import re
import uuid
import logging
import easyocr
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from models import OCRRecord, FlowManager

# ------------------------------------------------------------------
# CONFIG & LOGGER
# ------------------------------------------------------------------

logger = logging.getLogger("FlowManagerApp")
reader = easyocr.Reader(["en"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE_MB = 1

UPLOAD_DIR = "uploads"
# ------------------------------------------------------------------
# VALIDATION FUNCTIONS
# ------------------------------------------------------------------


def validate_file_type(file: UploadFile):
    """Validate allowed file extension."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )


def validate_file_size(file: UploadFile):
    """Validate file size in MB."""
    file.file.seek(0, os.SEEK_END)
    size_mb = file.file.tell() / (1024 * 1024)
    file.file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.2f} MB). Max size: {MAX_FILE_SIZE_MB} MB",
        )


# ------------------------------------------------------------------
# TASK FUNCTIONS
# ------------------------------------------------------------------
def upload_task(file: UploadFile) -> str:
    """Validate and save uploaded file."""
    validate_file_type(file)
    validate_file_size(file)

    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    logger.info(f"✅ File uploaded successfully: {file_path}")
    return file_path


def ocr_task(file_path: str) -> str:
    """Perform OCR on saved image."""
    results = reader.readtext(file_path)
    text = " ".join([res[1] for res in results])
    if not text.strip():
        raise ValueError("No text detected during OCR.")
    logger.info(f"OCR results: {results}")
    return text


def extract_task(text: str):
    """Extract Name and DOB from OCR text."""
    name_match = re.search(r"\bName\b[:\s]*([A-Za-z\s]+)", text, re.IGNORECASE)
    _MONTH = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|January|February|March|April|June|July|August|September|October|November|December)"
    DOB_LABELS = r"(?:DoB|DOB|Date\s*of\s*Birth)"
    DOB_VALUE = rf"([0-3]?\d(?:[\/\-][01]?\d[\/\-]\d{{2,4}}|\s+{_MONTH}\s+\d{{2,4}}))"
    clean = re.sub(r"[ \t]+", " ", text).strip()

    dob_match = re.search(
        rf"\b{DOB_LABELS}\b[:\s]*{DOB_VALUE}", clean, flags=re.IGNORECASE
    )

    name = name_match.group(1).strip() if name_match else "Unknown"
    dob = dob_match.group(1) if dob_match else "Unknown"

    if name == "Unknown" or dob == "Unknown":
        raise ValueError("Failed to extract valid Name or DOB.")
    logger.info(f"Extracted details — Name: {name}, DOB: {dob}")
    return name, dob


def save_task(db: Session, flow: FlowManager, name: str, dob: str, file_path: str):
    """Save OCR results to database."""
    try:
        record = OCRRecord(name=name, dob=dob, image_name=os.path.basename(file_path))
        db.add(record)
        db.commit()
        db.refresh(record)

        flow.related_record_id = record.id
        db.commit()
        logger.info(f"✅ Record saved to database with ID {record.id}")
        return record
    except Exception as e:
        db.rollback()
        raise ValueError(f"Database save failed: {e}")
