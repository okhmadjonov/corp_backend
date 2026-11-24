import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

BASE_DIR = Path(settings.UPLOAD_DIR)
PUBLIC_DIR = BASE_DIR / "public"    # rasmlar, /media orqali ochiq
PRIVATE_DIR = BASE_DIR / "private"  # PDF, ochiq berilmaydi

MAX_BYTES = {
    "image": settings.MAX_IMAGE_MB * 1024 * 1024,
    "pdf": settings.MAX_PDF_MB * 1024 * 1024,
}


def ensure_dirs() -> None:
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)


def _detect(data: bytes) -> tuple[str, str] | None:
    """Fayl turini nomiga emas, ichidagi baytlarga qarab aniqlaydi."""
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image"
    if data.startswith(b"%PDF-"):
        return "pdf", "pdf"
    return None


async def save_upload(file: UploadFile) -> dict:
    data = await file.read(max(MAX_BYTES.values()) + 1)

    detected = _detect(data)
    if not detected:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Faqat JPG, PNG, WEBP yoki PDF yuklash mumkin"
        )
    ext, file_type = detected

    if len(data) > MAX_BYTES[file_type]:
        limit_mb = MAX_BYTES[file_type] // (1024 * 1024)
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, f"Fayl {limit_mb} MB dan katta"
        )

    name = f"{uuid.uuid4().hex}.{ext}"
    if file_type == "image":
        (PUBLIC_DIR / name).write_bytes(data)
        url = f"/media/{name}"
    else:
        (PRIVATE_DIR / name).write_bytes(data)
        url = f"private/{name}"

    return {"url": url, "file_type": file_type, "size": len(data)}