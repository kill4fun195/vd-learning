import re
import uuid
from pathlib import Path
from urllib.parse import urlparse

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, UploadFile, status

from app.core.config import get_settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
PRESIGNED_URL_EXPIRES_SECONDS = 60 * 60  # 1 hour


def _get_s3_client():
    settings = get_settings()
    kwargs: dict = {
        "aws_access_key_id": settings.aws_access_key_id,
        "aws_secret_access_key": settings.aws_secret_access_key,
        "region_name": settings.aws_region,
        "config": Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    }
    if settings.s3_endpoint_url:
        kwargs["endpoint_url"] = settings.s3_endpoint_url
    else:
        # Regional endpoint so presigned URLs open correctly in the browser
        kwargs["endpoint_url"] = f"https://s3.{settings.aws_region}.amazonaws.com"
    return boto3.client("s3", **kwargs)


def _extract_object_key(stored: str) -> str:
    """Accept either a raw S3 key or a previously stored full URL."""
    if not stored.startswith("http://") and not stored.startswith("https://"):
        return stored.lstrip("/")

    settings = get_settings()
    path = urlparse(stored).path.lstrip("/")
    bucket_prefix = f"{settings.s3_bucket_name}/"
    if path.startswith(bucket_prefix):
        return path[len(bucket_prefix) :]

    # Virtual-hosted–style: /avatars/...
    if path.startswith("avatars/"):
        return path

    # Fallback: strip leading bucket-like segment if present
    match = re.match(r"^[^/]+/(avatars/.+)$", path)
    if match:
        return match.group(1)
    return path


def build_presigned_avatar_url(stored: str | None) -> str | None:
    """Turn a stored key/URL into a browser-openable temporary URL."""
    if not stored:
        return None

    settings = get_settings()
    if not settings.s3_bucket_name:
        return stored

    key = _extract_object_key(stored)
    try:
        client = _get_s3_client()
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.s3_bucket_name, "Key": key},
            ExpiresIn=PRESIGNED_URL_EXPIRES_SECONDS,
        )
    except (BotoCoreError, ClientError):
        return stored

    # When using MinIO / custom endpoint, rewrite host for browser access if needed
    public_base = settings.s3_public_endpoint_url
    if public_base and settings.s3_endpoint_url and settings.s3_endpoint_url in url:
        url = url.replace(settings.s3_endpoint_url.rstrip("/"), public_base.rstrip("/"), 1)
    return url


async def upload_avatar(file: UploadFile, user_id: int) -> str:
    """Upload avatar to S3 and return the object key (stored in DB)."""
    settings = get_settings()
    if not settings.s3_bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="S3 bucket is not configured",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")
    if len(content) > MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large (max 5MB)")

    extension = Path(file.filename or "avatar.jpg").suffix.lower() or ".jpg"
    key = f"avatars/{user_id}/{uuid.uuid4().hex}{extension}"

    try:
        client = _get_s3_client()
        client.put_object(
            Bucket=settings.s3_bucket_name,
            Key=key,
            Body=content,
            ContentType=file.content_type,
        )
    except (BotoCoreError, ClientError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to upload avatar to S3: {exc}",
        ) from exc

    return key
