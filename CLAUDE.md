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
- Rasmlar /media orqali ochiq (+ /media/thumbs/ WEBP nusxa, `thumb_url`); PDF private, faqat admin `.../files/{id}/content` orqali
- Rasm/fayl `url` faqat /admin/uploads bergan formatda qabul qilinadi (`IMAGE_URL_RE`, `PDF_URL_RE`)
- Auth: access token 15 daq + refresh token (DB'da hash, rotation)
- Migratsiya: `alembic revision --autogenerate -m "..."`, keyin `alembic upgrade head`
- Seed: `python -m app.seed`
- Yetim fayllarni tozalash: `python -m app.cleanup_uploads` (ko'rish), `--delete` (o'chirish)
- Unique: `unique=True` emas, `__table_args__ = (unique_alive("jadval", "ustun"),)`; "band" tekshiruvida `is_deleted=false`
- Ota-yozuv o'chirilsa bolalari ham: `soft_delete_children()`; ishlatilayotgan kategoriya o'chirilmaydi (409)
- Testlar: `pytest` (alohida `<db>_test` bazada); yangi funksiyaga test yozilsin
- Qidiruv (ILIKE) doim `like_pattern(q)` + `escape="\\"` orqali; ro'yxatlar `app.core.schemas.Page` qaytaradi

## Muloqot
- Javoblar o'zbek tilida, qadamma-qadam, qisqa
- Foydalanuvchi: Windows, Git Bash, VS Code uslubi

## Bog'liq loyihalar
corp_backend, corp_admin, corp_front — 3 alohida git repo, lekin bitta tizim.
API javob/so'rov formati o'zgarsa, admin va front ham shu ishda moslashtiriladi; har biri o'z repo'siga commit/push.
`client.ts`, `tokenStorage.ts`, `errors.ts` ikkala frontda nusxa — birini tuzatsangiz, ikkinchisini ham.

## Ma'lum kamchiliklar
Hozircha yo'q (partial unique, 409 bloklash, thumbnail, admin PDF, testlar/README — hal qilingan).
Deploy hozircha kerak emas.
