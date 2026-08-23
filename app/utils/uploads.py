"""
Trek image upload handling. This is new attack surface (file handling is
explicitly called out in the spec's security-review checklist), so
validation ships in the same change that introduces the feature rather
than being bolted on afterwards:

  1. extension allowlist (config: UPLOAD_ALLOWED_EXTENSIONS)
  2. magic-byte sniff of the first few bytes — catches a renamed
     `payload.php.jpg` even though its *extension* looks fine, without
     pulling in an image-processing dependency just for this
  3. Flask's MAX_CONTENT_LENGTH caps request/body size before this code
     even runs
  4. secure_filename() + a random hex name for the file actually written
     to disk — the original filename is never trusted as a path
  5. stored under a per-trek subdirectory, never anywhere web-executable
"""
import os
import secrets

from werkzeug.utils import secure_filename

# (allowlisted extension -> expected leading bytes). JPEG has two common
# leading markers; WEBP's RIFF header additionally needs the "WEBP" tag at
# offset 8, checked separately below.
_MAGIC_BYTES = {
    "png": [b"\x89PNG\r\n\x1a\n"],
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "webp": [b"RIFF"],
}


class UploadRejected(ValueError):
    """Raised with a user-facing message when an upload fails validation."""


def _extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_image(file_storage, allowed_extensions):
    filename = file_storage.filename or ""
    if not filename:
        raise UploadRejected("No file selected.")

    ext = _extension(filename)
    if ext not in allowed_extensions:
        raise UploadRejected(f"Unsupported file type. Allowed: {', '.join(sorted(allowed_extensions))}.")

    header = file_storage.stream.read(16)
    file_storage.stream.seek(0)
    signatures = _MAGIC_BYTES.get(ext, [])
    if not any(header.startswith(sig) for sig in signatures):
        raise UploadRejected("File content doesn't match its extension.")
    if ext == "webp" and header[8:12] != b"WEBP":
        raise UploadRejected("File content doesn't match its extension.")

    return ext


def save_trek_image(file_storage, trek_id, upload_root, allowed_extensions):
    """Validates and saves an uploaded trek photo.

    Returns the path stored on TrekImage.file_path, relative to
    app/static/ (e.g. 'uploads/treks/12/ab12cd34.jpg') so templates can
    render it with `url_for('static', filename=image.file_path)`.
    """
    ext = validate_image(file_storage, allowed_extensions)

    trek_dir = os.path.join(upload_root, str(trek_id))
    os.makedirs(trek_dir, exist_ok=True)

    stored_name = f"{secrets.token_hex(8)}.{ext}"
    # secure_filename() is redundant given the fully random name, but kept
    # as a second guard in case the naming scheme ever changes.
    stored_name = secure_filename(stored_name)
    absolute_path = os.path.join(trek_dir, stored_name)
    file_storage.save(absolute_path)

    return f"uploads/treks/{trek_id}/{stored_name}"


def delete_trek_image_file(relative_path, static_root):
    absolute_path = os.path.join(static_root, relative_path)
    try:
        if os.path.commonpath([os.path.abspath(absolute_path), os.path.abspath(static_root)]) == os.path.abspath(
            static_root
        ) and os.path.isfile(absolute_path):
            os.remove(absolute_path)
    except (ValueError, OSError):
        pass  # best-effort cleanup — a missing/unreadable file shouldn't block the DB delete
