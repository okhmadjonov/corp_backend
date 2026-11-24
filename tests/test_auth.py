from datetime import datetime, timedelta, timezone

from sqlalchemy import update

from app.core.database import SessionLocal
from app.core.security import hash_token
from app.modules.auth.models import RefreshToken


def test_register_login_me(client):
    r = client.post("/auth/register",
                    json={"login": "vali", "password": "secret12", "full_name": "Vali"})
    assert r.status_code == 201
    token = r.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).json()
    assert me["login"] == "vali" and me["role"]["name"] == "user"


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


def _refresh(client, token):
    return client.post("/auth/refresh", json={"refresh_token": token})


def test_refresh_rotation(client):
    tokens = client.post("/auth/register",
                         json={"login": "r1_user", "password": "secret12", "full_name": "Rr"}).json()
    r = _refresh(client, tokens["refresh_token"])
    assert r.status_code == 200
    assert r.json()["refresh_token"] != tokens["refresh_token"]
    # eski token endi ishlamaydi
    assert _refresh(client, tokens["refresh_token"]).status_code == 401


def test_refresh_reuse_after_grace_revokes_all(client):
    old = client.post("/auth/register",
                      json={"login": "r2_user", "password": "secret12", "full_name": "Rr"}).json()
    new = _refresh(client, old["refresh_token"]).json()

    # eski tokenni 1 daqiqa oldin bekor qilingandek ko'rsatamiz (grace o'tgan)
    with SessionLocal() as db:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(old["refresh_token"]))
            .values(revoked_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        )
        db.commit()

    assert _refresh(client, old["refresh_token"]).status_code == 401  # o'g'irlik belgisi
    assert _refresh(client, new["refresh_token"]).status_code == 401  # hamma sessiya yopildi


def test_refresh_reuse_within_grace_keeps_session(client):
    old = client.post("/auth/register",
                      json={"login": "r3_user", "password": "secret12", "full_name": "Rr"}).json()
    new = _refresh(client, old["refresh_token"]).json()
    assert _refresh(client, old["refresh_token"]).status_code == 401  # ikkinchi tab
    assert _refresh(client, new["refresh_token"]).status_code == 200  # sessiya tirik


def test_logout_revokes_refresh(client):
    t = client.post("/auth/register",
                    json={"login": "r4_user", "password": "secret12", "full_name": "Rr"}).json()
    assert client.post("/auth/logout", json={"refresh_token": t["refresh_token"]}).status_code == 204
    assert _refresh(client, t["refresh_token"]).status_code == 401
