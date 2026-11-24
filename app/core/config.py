from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SUPERADMIN_LOGIN: str
    SUPERADMIN_PASSWORD: str
    SUPERADMIN_FULL_NAME: str = "Super Admin"
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173", "http://localhost:5174",
        "http://127.0.0.1:5173", "http://127.0.0.1:5174",
    ]

    # Refresh token httpOnly cookie'da. Lokal http'da Secure=False bo'lishi shart;
    # production (https) da COOKIE_SECURE=true qiling.
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


    UPLOAD_DIR: str = "uploads"
    MAX_IMAGE_MB: int = 5
    MAX_PDF_MB: int = 20


    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()