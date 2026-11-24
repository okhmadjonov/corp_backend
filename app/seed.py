from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_password

# Barcha modellar import qilinadi, relationship'lar to'g'ri ulanishi uchun
from app.modules.auth.models import Role, User
from app.modules.categories.models import Gender, Season
from app.modules.clothes import models as _clothes  # noqa: F401
from app.modules.patterns import models as _patterns  # noqa: F401

ROLES = {
    "super_admin": "Barcha huquqlarga ega",
    "operator": "Katalogni boshqaradi",
    "user": "Oddiy foydalanuvchi",
}
GENDERS = ["Ayollar", "Erkaklar", "Bolalar"]
SEASONS = ["Kuz", "Qish", "Bahor", "Yoz"]


def seed() -> None:
    with SessionLocal() as db:
        for name, description in ROLES.items():
            if not db.scalar(select(Role).where(Role.name == name)):
                db.add(Role(name=name, description=description))

        for name in GENDERS:
            if not db.scalar(select(Gender).where(Gender.name == name)):
                db.add(Gender(name=name))

        for name in SEASONS:
            if not db.scalar(select(Season).where(Season.name == name)):
                db.add(Season(name=name))

        db.flush()

        super_admin_role = db.scalar(select(Role).where(Role.name == "super_admin"))
        if not db.scalar(select(User).where(User.login == settings.SUPERADMIN_LOGIN)):
            db.add(
                User(
                    login=settings.SUPERADMIN_LOGIN,
                    password_hash=hash_password(settings.SUPERADMIN_PASSWORD),
                    full_name=settings.SUPERADMIN_FULL_NAME,
                    role_id=super_admin_role.id,
                )
            )

        db.commit()
    print("Seed tugadi.")


if __name__ == "__main__":
    seed()