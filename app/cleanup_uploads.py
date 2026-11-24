"""Hech bir yozuvga biriktirilmagan (yetim) yuklangan fayllarni topadi.

Ishlatish:
    python -m app.cleanup_uploads            # faqat ro'yxatni ko'rsatadi
    python -m app.cleanup_uploads --delete   # haqiqatan o'chiradi

Yangi yuklangan, lekin hali formaga saqlanmagan fayllar o'chib ketmasligi uchun
MIN_AGE_HOURS dan yosh fayllarga tegilmaydi. Soft-delete qilingan yozuvlardagi
fayllar ham "ishlatilayotgan" hisoblanadi (yozuvni tiklash imkoni saqlanadi).
"""
import sys
import time

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.storage import PRIVATE_DIR, PUBLIC_DIR, THUMBS_DIR
# relationship'lar to'g'ri ulanishi uchun barcha modellar yuklanadi
from app.modules.auth import models as _auth  # noqa: F401
from app.modules.categories import models as _categories  # noqa: F401
from app.modules.clothes.models import ClothesImage
from app.modules.patterns.models import PatternFile

MIN_AGE_HOURS = 24


def _used_names() -> set[str]:
    with SessionLocal() as db:
        urls = list(db.scalars(select(ClothesImage.url)))
        urls += list(db.scalars(select(PatternFile.url)))
    return {u.rsplit("/", 1)[-1] for u in urls}


def main(delete: bool) -> None:
    used = _used_names()
    cutoff = time.time() - MIN_AGE_HOURS * 3600
    orphans = [
        p
        for d in (PUBLIC_DIR, PRIVATE_DIR)
        if d.exists()
        for p in d.iterdir()
        if p.is_file() and p.name not in used and p.stat().st_mtime < cutoff
    ]

    total = sum(p.stat().st_size for p in orphans)
    for p in orphans:
        print(p)
        if delete:
            p.unlink()
            (THUMBS_DIR / f"{p.stem}.webp").unlink(missing_ok=True)

    action = "o'chirildi" if delete else "topildi (o'chirish uchun --delete)"
    print(f"{len(orphans)} ta fayl, {total / 1024 / 1024:.1f} MB {action}")


if __name__ == "__main__":
    main(delete="--delete" in sys.argv)
