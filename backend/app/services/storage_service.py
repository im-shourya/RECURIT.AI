"""
RECRUIT.AI — Object Storage Service
Uploads candidate submission files to S3 (or any S3-compatible endpoint such
as MinIO) and hands out short-lived presigned URLs for reading them back.

Uploaded files are treated as untrusted:
  - the client's filename is never used to build the object key
  - only an allowlisted set of extensions is accepted
  - the size limit is enforced while streaming, not from the Content-Length
    header, which a client controls
  - objects are private; reads go through short-lived presigned URLs
"""

import uuid
from typing import BinaryIO, Optional

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings

settings = get_settings()


# ── Upload policy ──────────────────────────────────────────────
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

# Extension -> the content type we store the object with. We set the type from
# this table rather than trusting the client's Content-Type header.
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".txt": "text/plain",
    ".md": "text/markdown",
}

PRESIGNED_URL_TTL_SECONDS = 300  # 5 minutes

# Interview recordings are captured by the browser's MediaRecorder, which
# produces webm almost everywhere and mp4 on Safari. Kept separate from the
# submission allowlist: a candidate should not be able to post a .docx as a
# "recording", and a recording is written by our own player, not chosen from
# a file picker.
RECORDING_EXTENSIONS: dict[str, str] = {
    ".webm": "video/webm",
    ".mp4": "video/mp4",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
}

MAX_RECORDING_BYTES = 200 * 1024 * 1024  # 200 MB

# Organisation logos. Images only, and a tight cap: this renders in an avatar
# and at the top of the public apply page, so a multi-megabyte original would
# be paid for by every candidate who opens the form.
LOGO_EXTENSIONS: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
}

MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 MB

# Every prefix this service owns. Used to refuse signing or deleting anything
# it did not write — a legacy row holding a plain URL must not be turned into
# a delete against an arbitrary path.
MANAGED_PREFIXES = ("submissions/", "recordings/", "logos/")


class StorageError(RuntimeError):
    """Raised when the storage backend is unusable or rejects a request."""


class UploadTooLarge(ValueError):
    """Raised when a stream exceeds MAX_UPLOAD_BYTES."""


class UnsupportedFileType(ValueError):
    """Raised when a filename's extension is not allowlisted."""


def is_configured() -> bool:
    """
    True when enough S3 settings are present to attempt an upload.

    Uploads are opt-in: a developer running without AWS credentials gets a
    clear 503 from the router rather than a confusing boto error.
    """
    return bool(
        settings.S3_BUCKET_NAME
        and (
            (settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
            or settings.S3_ENDPOINT_URL
        )
    )


def _client():
    kwargs = {
        "region_name": settings.S3_REGION,
        "config": Config(signature_version="s3v4", retries={"max_attempts": 3}),
    }
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    if settings.S3_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.S3_ENDPOINT_URL
    return boto3.client("s3", **kwargs)


def extension_of(filename: str) -> str:
    """
    Return the allowlisted extension for a client-supplied filename.

    Only the final suffix is considered, lowercased. Anything not in the
    allowlist raises, so `resume.pdf.exe` and `../../etc/passwd` are both
    rejected here rather than reaching the key builder.
    """
    name = (filename or "").strip().lower()
    dot = name.rfind(".")
    ext = name[dot:] if dot != -1 else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(
            f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return ext


def build_key(applicant_id, extension: str) -> str:
    """
    Build the object key from server-controlled values only.

    The applicant id is a UUID and the extension is allowlisted, so no part of
    the key comes from client input and the key cannot traverse the bucket.
    """
    return f"submissions/{applicant_id}/{uuid.uuid4().hex}{extension}"


def upload_submission_file(applicant_id, filename: str, stream: BinaryIO) -> str:
    """
    Stream an upload into object storage and return the stored object key.

    The size cap is enforced chunk by chunk while reading, so an oversized or
    lying client is cut off rather than buffered whole into memory.
    """
    if not is_configured():
        raise StorageError("Object storage is not configured")

    extension = extension_of(filename)
    key = build_key(applicant_id, extension)

    body = bytearray()
    while True:
        chunk = stream.read(64 * 1024)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_UPLOAD_BYTES:
            raise UploadTooLarge(
                f"File exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit"
            )

    if not body:
        raise ValueError("Uploaded file is empty")

    try:
        _client().put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=bytes(body),
            ContentType=ALLOWED_EXTENSIONS[extension],
            # Private by default. Reads are served via presigned URLs so the
            # bucket never needs public access.
            ACL="private",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Upload failed: {exc}") from exc

    return key


def upload_recording(interview_id, filename: str, stream: BinaryIO) -> str:
    """
    Store an interview recording and return its object key.

    Same guarantees as a submission upload — allowlisted extension, key built
    only from server-side values, private object — with a larger cap and a
    video/audio allowlist.
    """
    if not is_configured():
        raise StorageError("Object storage is not configured")

    name = (filename or "").strip().lower()
    dot = name.rfind(".")
    extension = name[dot:] if dot != -1 else ""
    if extension not in RECORDING_EXTENSIONS:
        raise UnsupportedFileType(
            f"Unsupported recording format. Allowed: {', '.join(sorted(RECORDING_EXTENSIONS))}"
        )

    key = f"recordings/{interview_id}/{uuid.uuid4().hex}{extension}"

    body = bytearray()
    while True:
        chunk = stream.read(256 * 1024)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_RECORDING_BYTES:
            raise UploadTooLarge(
                f"Recording exceeds the {MAX_RECORDING_BYTES // (1024 * 1024)}MB limit"
            )

    if not body:
        raise ValueError("Recording is empty")

    try:
        _client().put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=bytes(body),
            ContentType=RECORDING_EXTENSIONS[extension],
            ACL="private",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Recording upload failed: {exc}") from exc

    return key


def upload_org_logo(org_id, filename: str, stream: BinaryIO) -> str:
    """
    Store an organisation logo and return its object key.

    Same guarantees as the other uploads — allowlisted extension, key built
    only from server-side values, private object — with an image allowlist and
    a much tighter cap.

    SVG is accepted because logos are commonly supplied that way, and it is
    stored with an explicit `image/svg+xml` content type. Note that an SVG is
    a document and can carry script, so it must never be rendered same-origin;
    it is only ever served from the storage host through a presigned URL and
    referenced as an <img> src, which does not execute embedded script.
    """
    if not is_configured():
        raise StorageError("Object storage is not configured")

    name = (filename or "").strip().lower()
    dot = name.rfind(".")
    extension = name[dot:] if dot != -1 else ""
    if extension not in LOGO_EXTENSIONS:
        raise UnsupportedFileType(
            f"Unsupported image format. Allowed: {', '.join(sorted(LOGO_EXTENSIONS))}"
        )

    key = f"logos/{org_id}/{uuid.uuid4().hex}{extension}"

    body = bytearray()
    while True:
        chunk = stream.read(64 * 1024)
        if not chunk:
            break
        body.extend(chunk)
        if len(body) > MAX_LOGO_BYTES:
            raise UploadTooLarge(
                f"Logo exceeds the {MAX_LOGO_BYTES // (1024 * 1024)}MB limit"
            )

    if not body:
        raise ValueError("Uploaded image is empty")

    try:
        _client().put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
            Body=bytes(body),
            ContentType=LOGO_EXTENSIONS[extension],
            ACL="private",
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Logo upload failed: {exc}") from exc

    return key


def resolve_logo_url(stored: str) -> str:
    """
    Turn a stored logo value into something a browser can render.

    `logo_url` holds either an object key we wrote, or a plain URL an
    organisation supplied directly — both are legitimate, and the field
    predates uploads. A key is signed; anything else is returned unchanged.

    Never raises: a logo that cannot be resolved should leave a blank avatar,
    not fail the profile or the public apply page it appears on.
    """
    if not stored:
        return ""
    if not stored.startswith(MANAGED_PREFIXES):
        return stored
    try:
        return presigned_get_url(stored) or ""
    except StorageError:
        return ""


def delete_object(key: str) -> bool:
    """
    Remove a stored object.

    Used when erasing a candidate: leaving their recording or submission in
    the bucket would make the deletion only partial. Refuses anything that is
    not one of our own keys, so a legacy row holding a plain URL cannot be
    turned into a delete against an arbitrary path.
    """
    if not key or not key.startswith(MANAGED_PREFIXES):
        return False
    if not is_configured():
        raise StorageError("Object storage is not configured")

    try:
        _client().delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        return True
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Delete failed: {exc}") from exc


def presigned_get_url(key: str, expires_in: int = PRESIGNED_URL_TTL_SECONDS) -> Optional[str]:
    """
    Return a short-lived read URL for a stored object.

    Returns None when storage is not configured or the value is not one of our
    keys — for example a legacy row where `file_url` holds a plain URL the
    client supplied before uploads existed.
    """
    if not key or not is_configured() or not key.startswith(MANAGED_PREFIXES):
        return None

    try:
        return _client().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )
    except (BotoCoreError, ClientError) as exc:
        raise StorageError(f"Could not sign URL: {exc}") from exc
