import mimetypes

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.storage import PUBLIC_DIR, ensure_dirs
from app.modules.uploads.router import router as uploads_router
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.clothes.router import router as clothes_router
from app.modules.patterns.router import router as patterns_router
from app.modules.catalog.router import router as catalog_router
from app.modules.favorites.router import router as favorites_router
from app.modules.users.router import router as users_router

# Windows reestrida .webp bo'lmasligi mumkin -> application/octet-stream qaytib qoladi
mimetypes.add_type("image/webp", ".webp")

app = FastAPI(title="Corp Backend")

ensure_dirs()
app.mount("/media", StaticFiles(directory=PUBLIC_DIR), name="media")
app.include_router(uploads_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(categories_router)
app.include_router(clothes_router)
app.include_router(patterns_router)
app.include_router(catalog_router)
app.include_router(favorites_router)
app.include_router(users_router)

@app.get("/health")
def health():
    return {"status": "ok"}