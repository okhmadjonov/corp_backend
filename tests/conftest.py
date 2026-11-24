"""Testlar alohida <db>_test bazasida ishlaydi; ish bazasiga tegmaydi.

Baza har sessiyada noldan Alembic migratsiyalari bilan quriladi (migratsiyalar ham
tekshiriladi), har testdan keyin jadvallar tozalanib, seed qayta yoziladi.
"""
import io
import shutil
import tempfile
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url

# --- boshqa app modullari import qilinishidan OLDIN sozlamani test bazasiga
# yo'naltiramiz (engine va storage import paytida sozlamani o'qiydi) ---
from app.core.config import settings

_base_url = make_url(settings.DATABASE_URL)
TEST_DB = f"{_base_url.database}_test"
settings.DATABASE_URL = _base_url.set(database=TEST_DB).render_as_string(hide_password=False)
settings.UPLOAD_DIR = tempfile.mkdtemp(prefix="corp_test_uploads_")

import psycopg  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.database import engine  # noqa: E402
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def _admin_conn():
    url = _base_url.set(drivername="postgresql", database="postgres")
    return psycopg.connect(url.render_as_string(hide_password=False), autocommit=True)


@pytest.fixture(scope="session", autouse=True)
def database():
    # himoya: hech qachon ish bazasini TRUNCATE qilmaslik uchun
    assert engine.url.database == TEST_DB and TEST_DB.endswith("_test"), engine.url
    with _admin_conn() as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')
        conn.execute(f'CREATE DATABASE "{TEST_DB}"')
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    yield
    engine.dispose()
    with _admin_conn() as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB}" WITH (FORCE)')
    shutil.rmtree(settings.UPLOAD_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_db(database):
    seed()
    yield
    with engine.begin() as conn:
        tables = conn.execute(
            text("select tablename from pg_tables where schemaname='public' "
                 "and tablename <> 'alembic_version'")
        ).scalars().all()
        conn.execute(text(f"TRUNCATE {', '.join(tables)} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    return TestClient(app)


def auth_header(client: TestClient, login: str, password: str) -> dict:
    r = client.post("/auth/login", json={"login": login, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def admin(client) -> dict:
    return auth_header(client, settings.SUPERADMIN_LOGIN, settings.SUPERADMIN_PASSWORD)


@pytest.fixture
def user(client) -> dict:
    r = client.post("/auth/register",
                    json={"login": "ali", "password": "secret12", "full_name": "Ali Valiyev"})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def image_bytes(fmt: str = "PNG", size=(1200, 1600)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buf, fmt)
    return buf.getvalue()


def upload(client, headers, data: bytes, name: str = "f.bin") -> dict:
    r = client.post("/admin/uploads", headers=headers, files={"file": (name, data)})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def make_clothes(client, admin):
    def _make(name="Palto", gender_id=1, season_id=1, **extra) -> dict:
        body = {"name": name, "gender_id": gender_id, "season_id": season_id, **extra}
        r = client.post("/admin/clothes", headers=admin, json=body)
        assert r.status_code == 201, r.text
        return r.json()
    return _make


@pytest.fixture
def make_pattern(client, admin):
    def _make(name="Ko'ylak andozasi", price="50000", **extra) -> dict:
        body = {"name": name, "price": price, "gender_id": 1, "season_id": 1, **extra}
        r = client.post("/admin/patterns", headers=admin, json=body)
        assert r.status_code == 201, r.text
        return r.json()
    return _make
