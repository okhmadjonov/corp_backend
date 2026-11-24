from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_token
from app.modules.auth.models import RefreshToken

SITE = "corp_site_rt"
ADMIN = "corp_admin_rt"


def _register(client, login="vali_user"):
    r = client.post("/auth/register",
                    json={"login": login, "password": "secret12", "full_name": "Vali"})
    assert r.status_code == 201, r.text
    return r


def _refresh(client, raw: str | None = None, app: str = "site"):
    """raw berilsa, cookie qo'lda qo'yiladi (eski tokenni qayta yuborish uchun)."""
    name = ADMIN if app == "admin" else SITE
    if raw is not None:
        client.cookies.clear()  # aks holda jar'da bir nomli ikki cookie qoladi
        client.cookies.set(name, raw, path="/auth")
    return client.post("/auth/refresh", headers={"X-App": app})


def test_register_sets_httponly_cookie_not_body(client):
    r = _register(client)
    assert "refresh_token" not in r.json()
    cookie = r.headers["set-cookie"].lower()
    assert cookie.startswith(f"{SITE}=")
    assert "httponly" in cookie and "path=/auth" in cookie and "samesite=lax" in cookie
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {r.json()['access_token']}"})
    assert me.json()["role"]["name"] == "user"


def test_register_duplicate_login_409(client, user):
    r = client.post("/auth/register",
                    json={"login": "ali", "password": "secret12", "full_name": "Boshqa"})
    assert r.status_code == 409


def test_password_over_72_bytes_rejected(client):
    r = client.post("/auth/register",
                    json={"login": "uzun", "password": "ў" * 40, "full_name": "Uzun"})
    assert r.status_code == 422
    assert "72" in r.json()["detail"][0]["msg"]


def test_wrong_password_401(client, user):
    r = client.post("/auth/login", json={"login": "ali", "password": "xato-parol"})
    assert r.status_code == 401


def test_no_token_rejected(client):
    assert client.get("/auth/me").status_code in (401, 403)


def test_refresh_uses_cookie_and_rotates(client):
    _register(client)
    old = client.cookies[SITE]
    r = _refresh(client)
    assert r.status_code == 200 and r.json()["access_token"]
    assert client.cookies[SITE] != old  # rotation: yangi cookie


def test_refresh_without_cookie_401(client):
    assert _refresh(client).status_code == 401


def test_parallel_refresh_within_grace_keeps_session(client):
    """Ikki tab / StrictMode: ikkalasi eski cookie bilan keladi."""
    _register(client)
    old = client.cookies[SITE]
    assert _refresh(client).status_code == 200
    new = client.cookies[SITE]
    second = _refresh(client, old)  # ikkinchi so'rov eski cookie bilan
    assert second.status_code == 200 and second.json()["access_token"]
    assert "set-cookie" not in second.headers  # yangi cookie berilmaydi
    assert _refresh(client, new).status_code == 200  # sessiya tirik


def test_reuse_after_grace_revokes_all(client):
    _register(client)
    old = client.cookies[SITE]
    _refresh(client)
    new = client.cookies[SITE]
    with SessionLocal() as db:  # rotation 1 daqiqa oldin bo'lgandek
        past = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.execute(update(RefreshToken)
                   .where(RefreshToken.token_hash == hash_token(old))
                   .values(revoked_at=past, rotated_at=past))
        db.commit()
    assert _refresh(client, old).status_code == 401  # o'g'irlik belgisi
    assert _refresh(client, new).status_code == 401  # hamma sessiya yopildi


def test_logout_revokes_and_clears_cookie(client):
    _register(client)
    raw = client.cookies[SITE]
    r = client.post("/auth/logout")
    assert r.status_code == 204
    assert SITE not in client.cookies  # brauzer cookie'ni o'chiradi
    # logout qilingan token grace ichida ham qayta ishlamaydi
    assert _refresh(client, raw).status_code == 401


def test_admin_and_site_cookies_are_separate(client):
    r = client.post("/auth/login", headers={"X-App": "admin"},
                    json={"login": settings.SUPERADMIN_LOGIN, "password": settings.SUPERADMIN_PASSWORD})
    assert r.status_code == 200
    assert ADMIN in client.cookies and SITE not in client.cookies
    assert _refresh(client, app="site").status_code == 401  # sayt admin sessiyasini ko'rmaydi
    assert _refresh(client, app="admin").status_code == 200


def test_regular_user_cannot_login_to_admin(client, user):
    client.cookies.clear()
    r = client.post("/auth/login", headers={"X-App": "admin"},
                    json={"login": "ali", "password": "secret12"})
    assert r.status_code == 403
    assert ADMIN not in client.cookies


def test_foreign_origin_blocked(client, user):
    r = client.post("/auth/refresh", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    ok = client.post("/auth/refresh", headers={"Origin": "http://localhost:3000"})
    assert ok.status_code == 200


def test_cors_allows_credentials_for_frontends(client):
    r = client.options("/auth/refresh", headers={
        "Origin": "http://localhost:5000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "x-app",
    })
    assert r.headers["access-control-allow-origin"] == "http://localhost:5000"
    assert r.headers["access-control-allow-credentials"] == "true"
