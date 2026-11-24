"""Auth: access token javobda (frontend uni faqat xotirada saqlaydi),
refresh token esa httpOnly cookie'da (JavaScript o'qiy olmaydi).

Admin panel va sayt bitta domen (localhost) da turgani uchun cookie'lar portga
qarab ajralmaydi — shu sabab har ilova `X-App` sarlavhasini yuboradi va o'z
nomli cookie'sini oladi: admin -> corp_admin_rt, sayt -> corp_site_rt.
"""
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

App = Literal["admin", "site"]
COOKIE_PATH = "/auth"  # cookie faqat /auth/* so'rovlariga yuboriladi


def check_origin(request: Request) -> None:
    """CSRF himoyasi: brauzer boshqa saytdan yuborgan so'rovni rad etadi.
    Origin bo'lmasa (curl, testlar) — brauzer emas, cookie ham o'g'irlanmagan."""
    origin = request.headers.get("origin")
    if origin and origin not in settings.CORS_ORIGINS:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Ruxsat etilmagan manba")


def get_app(x_app: str | None = Header(default=None)) -> App:
    return "admin" if x_app == "admin" else "site"


def cookie_name(app: App) -> str:
    return f"corp_{app}_rt"


def _cookie_args() -> dict:
    return {
        "path": COOKIE_PATH,
        "httponly": True,
        "secure": settings.COOKIE_SECURE,
        "samesite": settings.COOKIE_SAMESITE,
    }


def _set_refresh(response: Response, app: App, raw: str) -> None:
    response.set_cookie(
        cookie_name(app), raw,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        **_cookie_args(),
    )


def _clear_refresh(response: Response, app: App) -> None:
    response.delete_cookie(cookie_name(app), **_cookie_args())


def _client(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    return request.headers.get("user-agent"), ip


router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(check_origin)])


def _start_session(
    db: Session, user: User, request: Request, response: Response, app: App
) -> TokenResponse:
    access, raw = service.issue_tokens(db, user, *_client(request))
    _set_refresh(response, app, raw)
    return access


@router.post("/login", response_model=TokenResponse)
def login(
    data: LoginRequest, request: Request, response: Response,
    app: App = Depends(get_app), db: Session = Depends(get_db),
):
    user = service.authenticate(db, data.login, data.password)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Login yoki parol noto'g'ri")
    if app == "admin" and user.role.name not in service.ADMIN_ROLES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Sizda admin panelga kirish huquqi yo'q")
    return _start_session(db, user, request, response, app)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest, request: Request, response: Response,
    app: App = Depends(get_app), db: Session = Depends(get_db),
):
    user = service.register_user(db, data)
    if not user:
        raise HTTPException(status.HTTP_409_CONFLICT, "Bu login band")
    return _start_session(db, user, request, response, app)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request, response: Response,
    app: App = Depends(get_app), db: Session = Depends(get_db),
):
    raw = request.cookies.get(cookie_name(app))
    issued = service.refresh_tokens(db, raw, *_client(request)) if raw else None
    if not issued:
        # yaroqsiz cookie brauzerda qolib ketmasin
        resp = JSONResponse({"detail": "Sessiya tugagan"}, status.HTTP_401_UNAUTHORIZED)
        _clear_refresh(resp, app)
        return resp
    access, new_raw = issued
    if new_raw:  # grace holatida yangi cookie berilmaydi (brauzerda allaqachon bor)
        _set_refresh(response, app, new_raw)
    return access


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request, response: Response,
    app: App = Depends(get_app), db: Session = Depends(get_db),
):
    raw = request.cookies.get(cookie_name(app))
    if raw:
        service.revoke_token(db, raw)
    _clear_refresh(response, app)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
