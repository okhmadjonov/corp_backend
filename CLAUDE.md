# Corp loyihasi

Onlayn kiyim do'koni: tayyor kiyimlar va kiyim patternlari (lekalo/chizma). Buyurtma va to'lov yo'q, faqat ko'rsatish (katalog).

## Tuzilma
- corp_backend: FastAPI + PostgreSQL + Alembic, sync SQLAlchemy 2.0 (psycopg), pip + requirements.txt
- corp_admin: Vite + React + TypeScript + React Router + React Query + axios (port 5174)
- corp_front: xuddi shu stack (port 5173)
- UI kutubxonasi yo'q. Faqat SCSS Modules: `import styles from "./X.module.scss"`, `className={styles.main}`
- SCSS: `@use '@/styles/variables' as *;`, `@` alias = src

## Backend arxitekturasi
app/core/{config,database,base,security,crud,utils,storage}.py
app/modules/<modul>/{models,schemas,service,router}.py
Modullar: auth, categories (Gender, Season, Tag), clothes, patterns, favorites, uploads, catalog (public), users

## Qoidalar
- Barcha jadvallar BaseModel'dan: id, created_at, updated_at, is_deleted, deleted_at, created_by/updated_by/deleted_by (FK users.id, use_alter=True)
- Soft delete hamma joyda; ro'yxatlarda doim is_deleted=false filtri
- Rollar: super_admin, operator, user. Ro'yxatdan o'tish: faqat login + parol, rol `user`
- Mehmon faqat ro'yxatlarni ko'radi; detail sahifa uchun login kerak (views_count atomik oshadi)
- Rasmlar /media orqali ochiq; PDF fayllar private (serve qilinmaydi)
- Auth: access token 15 daq + refresh token (DB'da hash, rotation)
- Migratsiya: `alembic revision --autogenerate -m "..."`, keyin `alembic upgrade head`
- Seed: `python -m app.seed`
- Yetim fayllarni tozalash: `python -m app.cleanup_uploads` (ko'rish), `--delete` (o'chirish)
- Qidiruv (ILIKE) doim `like_pattern(q)` + `escape="\\"` orqali; ro'yxatlar `app.core.schemas.Page` qaytaradi

## Muloqot
- Javoblar o'zbek tilida, qadamma-qadam, qisqa
- Foydalanuvchi: Windows, Git Bash, VS Code uslubi

## Ma'lum kamchiliklar (hal qilinmoqda)
1. ~~UNIQUE ustunlar o'chirilgan qatorlarda band turadi~~ — HAL QILINDI: `unique_alive()` (app/core/base.py) partial unique index. Yangi modelda `unique=True` emas, `__table_args__ = (unique_alive("jadval", "ustun"),)` ishlating; "band" tekshiruvlarida ham `is_deleted=false` filtri bo'lsin
2. Ishlatilayotgan jins/fasl/tegni o'chirib bo'ladi -> 409 bilan bloklash
3. Rasm thumbnail'lari yo'q (ro'yxat sekinlashadi) -> Pillow bilan kichik nusxa
4. Admin'da private PDF'ni ko'rish yo'q
5. Testlar va README yo'q
Deploy hozircha kerak emas.