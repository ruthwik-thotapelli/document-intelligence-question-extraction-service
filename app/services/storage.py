import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Magic bytes for supported file types
MAGIC_BYTES = {
    "application/pdf": [b"%PDF"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/jpg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG"],
}


def validate_file(file_bytes: bytes, content_type: str) -> None:
    """Validate file magic bytes to prevent malicious uploads."""
    magic_signatures = MAGIC_BYTES.get(content_type, [])
    for sig in magic_signatures:
        if file_bytes[: len(sig)] == sig:
            return
    raise ValueError(
        f"File content does not match declared content type '{content_type}'. "
        "File may be malformed or malicious."
    )


def save_upload(file_bytes: bytes, original_filename: str, user_id: int) -> str:
    """
    Save uploaded file bytes securely.
    - Uses UUID-based filenames to prevent path traversal.
    - Organises files per user in a subdirectory.
    Returns the relative file path string.
    """
    # Sanitize extension
    suffix = Path(original_filename).suffix.lower()
    if suffix not in {".pdf", ".jpg", ".jpeg", ".png"}:
        suffix = ".bin"

    unique_name = f"{uuid.uuid4().hex}{suffix}"
    user_dir = UPLOAD_DIR / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_dir / unique_name
    file_path.write_bytes(file_bytes)

    logger.info(f"Saved upload to {file_path} ({len(file_bytes)} bytes) for user {user_id}")
    return str(file_path)


def get_file_path(stored_path: str) -> Path:
    """Return the absolute path for a stored file, checking it still exists."""
    p = Path(stored_path)
    if not p.exists():
        raise FileNotFoundError(f"Stored file not found: {stored_path}")
    return p
