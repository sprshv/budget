import httpx
from app.config import settings

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_receipt_file(content_type: str, size: int) -> None:
    if content_type not in ALLOWED_TYPES:
        raise ValueError(f"File type {content_type} not allowed. Use JPEG, PNG, WebP, or GIF.")
    if size > MAX_SIZE_BYTES:
        raise ValueError(f"File size {size} bytes exceeds 10 MB limit.")


async def upload_receipt_to_supabase(
    file_bytes: bytes,
    content_type: str,
    storage_path: str,
) -> str:
    """Upload file to Supabase Storage and return public URL."""
    bucket = "receipts"
    upload_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{storage_path}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            upload_url,
            content=file_bytes,
            headers={
                "apikey": settings.SUPABASE_SECRET_KEY,
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(f"Supabase upload failed: {response.text}")

    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{storage_path}"
    return public_url
