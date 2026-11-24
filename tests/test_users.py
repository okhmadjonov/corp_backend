from conftest import auth_header


def test_super_admin_manages_users(client, admin):
    r = client.post("/admin/users", headers=admin,
                    json={"login": "op1", "password": "secret12", "full_name": "Operator"})
    assert r.status_code == 201 and r.json()["role"]["name"] == "operator"
    op = auth_header(client, "op1", "secret12")
    # operator katalogni boshqaradi, lekin foydalanuvchilarni emas
    assert client.get("/admin/clothes", headers=op).status_code == 200
    assert client.get("/admin/users", headers=op).status_code == 403


def test_last_super_admin_protected(client, admin):
    me = client.get("/auth/me", headers=admin).json()
    assert client.delete(f"/admin/users/{me['id']}", headers=admin).status_code == 400
    r = client.put(f"/admin/users/{me['id']}", headers=admin,
                   json={"full_name": "Xx", "role": "operator"})
    assert r.status_code == 400


def test_deleted_user_login_reusable(client, admin):
    u = client.post("/admin/users", headers=admin,
                    json={"login": "temp", "password": "secret12", "full_name": "Temp"}).json()
    assert client.delete(f"/admin/users/{u['id']}", headers=admin).status_code == 204
    assert client.post("/auth/login", json={"login": "temp", "password": "secret12"}).status_code == 401
    r = client.post("/auth/register",
                    json={"login": "temp", "password": "secret12", "full_name": "Yangi"})
    assert r.status_code == 201


def test_reset_password_ends_sessions(client, admin):
    t = client.post("/auth/register",
                    json={"login": "u1_user", "password": "secret12", "full_name": "Uu"}).json()
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {t['access_token']}"}).json()
    r = client.post(f"/admin/users/{me['id']}/reset-password", headers=admin,
                    json={"password": "yangi-parol"})
    assert r.status_code == 204
    assert client.post("/auth/refresh", json={"refresh_token": t["refresh_token"]}).status_code == 401
    assert client.post("/auth/login", json={"login": "u1_user", "password": "yangi-parol"}).status_code == 200


def test_user_search_escapes_wildcards(client, admin):
    assert client.get("/admin/users", headers=admin, params={"q": "%"}).json()["total"] == 0
