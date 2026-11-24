# corp_backend

Onlayn kiyim katalogining API'si: tayyor kiyimlar va kiyim patternlari (andozalar).
Buyurtma va to'lov yo'q — faqat katalog.

Bog'liq loyihalar (alohida repolar):
- [corp_admin](https://github.com/okhmadjonov/corp_admin) — admin panel (port 5174)
- [corp_front](https://github.com/okhmadjonov/corp_front) — sayt (port 5173)

## Texnologiyalar
FastAPI · PostgreSQL · SQLAlchemy 2 (sync, psycopg) · Alembic · Pillow · pytest

## Ishga tushirish

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash
pip install -r requirements-dev.txt

cp .env.example .env                 # DATABASE_URL, SECRET_KEY, SUPERADMIN_* ni to'ldiring
alembic upgrade head
python -m app.seed                   # rollar, jinslar, fasllar, super admin
uvicorn app.main:app --reload        # http://127.0.0.1:8000/docs
```

## Testlar

```bash
pytest
```

Testlar `<baza>_test` nomli **alohida** bazani o'zi yaratadi va oxirida o'chiradi.
Ish bazangizga tegmaydi. PostgreSQL foydalanuvchisida `CREATE DATABASE` huquqi bo'lishi kerak.

## Foydali buyruqlar

| Buyruq | Vazifasi |
|---|---|
| `alembic revision --autogenerate -m "..."` | Model o'zgarganda migratsiya yaratish |
| `alembic check` | Modellar va migratsiyalar mosligini tekshirish |
| `python -m app.make_thumbs` | Eski rasmlarga thumbnail yaratish |
| `python -m app.cleanup_uploads [--delete]` | Hech qayerda ishlatilmagan fayllarni topish/o'chirish |

## Tuzilma

```
app/core/      config, database, base (BaseModel, unique_alive), crud, security, storage
app/modules/   auth · users · categories · clothes · patterns · catalog · favorites · uploads
tests/         pytest (alohida test bazasida)
```

## Asosiy qoidalar
- **Soft delete**: hech narsa bazadan o'chirilmaydi, `is_deleted = true` bo'ladi.
  Kiyim o'chirilsa — variant va rasmlari ham; pattern o'chirilsa — fayllari ham.
- **Unique faqat tirik qatorlarda** (`unique_alive()`, partial index): o'chirilgan
  yozuvning login/slug/SKU/nomini qayta ishlatish mumkin.
- **Ishlatilayotgan** jins/fasl/tegni o'chirib bo'lmaydi — `409`.
- **Rollar**: `super_admin` (hammasi), `operator` (katalog), `user` (sayt).
  Ro'yxatdan o'tgan har kim `user` bo'ladi.
- **Mehmon** ro'yxatlarni ko'radi; batafsil sahifa uchun login kerak.
- **Fayllar**: rasmlar `/media` orqali ochiq (+ `/media/thumbs/` da 480px WEBP nusxa);
  PDF'lar yopiq, faqat admin `GET /admin/patterns/{id}/files/{file_id}/content` orqali ko'radi.
- **Auth**: access token 15 daqiqa; refresh token 7 kun, bazada hash, har ishlatilganda
  almashtiriladi. Bekor qilingan token qayta kelsa (30 s dan keyin) — barcha sessiyalar yopiladi.
- **API javob formati** o'zgarsa, `corp_admin` va `corp_front` ham shu ishda moslashtiriladi.
