"""Thumbnail'i yo'q eski rasmlar uchun kichik nusxa yaratadi.

Ishlatish:
    python -m app.make_thumbs
"""
from app.core.storage import IMAGE_URL_RE, PUBLIC_DIR, THUMBS_DIR, ensure_dirs, make_thumbnail


def main() -> None:
    ensure_dirs()
    made = failed = 0
    for path in sorted(PUBLIC_DIR.iterdir()):
        if not path.is_file() or not IMAGE_URL_RE.match(f"/media/{path.name}"):
            continue
        if (THUMBS_DIR / f"{path.stem}.webp").exists():
            continue
        try:
            make_thumbnail(path)
            made += 1
        except (OSError, ValueError) as e:
            failed += 1
            print(f"XATO {path.name}: {e}")
    print(f"{made} ta thumbnail yaratildi, {failed} ta xato")


if __name__ == "__main__":
    main()
