import io
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.config import settings

BASE_DIR = Path(settings.UPLOAD_DIR)
PUBLIC_DIR = BASE_DIR / "public"    # rasmlar, /media orqali ochiq
THUMBS_DIR = PUBLIC_DIR / "thumbs"  # kichik nusxalar, /media/thumbs orqali
PRIVATE_DIR = BASE_DIR / "private"  # PDF, ochiq berilmaydi

THUMB_SIZE = (480, 640)  # karta 3:4 nisbatda ko'rsatiladi

# Faqat save_upload() yaratgan URL'lar qabul qilinadi
IMAGE_URL_RE = re.compile(r"^/media/[0-9a-f]{32}\.(jpg|png|webp)$")
PDF_URL_RE = re.compile(r"^private/[0-9a-f]{32}\.pdf$")

MAX_BYTES = {
    "image": settings.MAX_IMAGE_MB * 1024 * 1024,
    "pdf": settings.MAX_PDF_MB * 1024 * 1024,
}


def ensure_dirs() -> None:
    THUMBS_DIR.mkdir(parents=True, exist_ok=True)
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


def make_thumbnail(source: Path) -> Path:
    """Rasmning kichik WEBP nusxasini thumbs/ ga yozadi."""
    target = THUMBS_DIR / f"{source.stem}.webp"
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img)  # telefon rasmlari ag'darilib qolmasin
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA" if "A" in img.getbands() else "RGB")
        img.thumbnail(THUMB_SIZE)
        img.save(target, "WEBP", quality=80, method=4)
    return target


def thumb_url(url: str | None) -> str | None:
    """Rasm URL'idan thumbnail URL'ini beradi; thumbnail yo'q bo'lsa asl URL."""
    if not url or not IMAGE_URL_RE.match(url):
        return url
    stem = Path(url).stem
    if (THUMBS_DIR / f"{stem}.webp").exists():
        return f"/media/thumbs/{stem}.webp"
    return url


def private_path(url: str) -> Path:
    """private/<nom>.pdf URL'ini diskdagi yo'lga aylantiradi (path traversal'siz)."""
    if not PDF_URL_RE.match(url):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl topilmadi")
    path = PRIVATE_DIR / Path(url).name
    if not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fayl diskda topilmadi")
    return path


def _check_image(data: bytes) -> None:
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()  # buzilgan yoki soxta rasmni ushlaydi
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Rasm fayli buzilgan")


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
    if file_type == "pdf":
        (PRIVATE_DIR / name).write_bytes(data)
        return {"url": f"private/{name}", "thumb_url": None, "file_type": "pdf", "size": len(data)}

    _check_image(data)
    path = PUBLIC_DIR / name
    path.write_bytes(data)
    try:
        make_thumbnail(path)
    except (OSError, ValueError):
        path.unlink(missing_ok=True)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Rasmni qayta ishlab bo'lmadi")
    url = f"/media/{name}"
    return {"url": url, "thumb_url": thumb_url(url), "file_type": "image", "size": len(data)}
