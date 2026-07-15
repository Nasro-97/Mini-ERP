from sqlalchemy import select

from app.core.company_database import get_session_for_company
from app.core.security import hash_password
from app.models import User, Role


COMPANIES = [
    "zangabil",
    "awatad",
    "al_araba",
    "al_kowa",
]


COD_EMAIL = "cod@example.com"
COD_PASSWORD = "12345678"
COD_FULLNAME = "COD Admin"


def seed_cod_user(company_code: str):
    db_generator = get_session_for_company(company_code)
    db = next(db_generator)

    try:
        cod_role = db.execute(
            select(Role).where(Role.name == "COD")
        ).scalar_one_or_none()

        if cod_role is None:
            cod_role = Role(name="COD")
            db.add(cod_role)
            db.commit()
            db.refresh(cod_role)

        user = db.execute(
            select(User).where(User.email == COD_EMAIL)
        ).scalar_one_or_none()

        if user is None:
            user = User(
                username="cod_admin",
                fullname=COD_FULLNAME,
                email=COD_EMAIL,
                password_hash=hash_password(COD_PASSWORD),
                is_active=True,
            )

            user.roles.append(cod_role)

            db.add(user)
            db.commit()
            db.refresh(user)

            print(f"Created COD user for {company_code}")

        else:
            if cod_role not in user.roles:
                user.roles.append(cod_role)
                db.commit()

            print(f"COD user already exists for {company_code}")

    finally:
        db.close()


if __name__ == "__main__":
    for company_code in COMPANIES:
        seed_cod_user(company_code)