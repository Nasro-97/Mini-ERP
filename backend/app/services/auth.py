from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.services.user import get_user_by_email
from app.core.company_database import get_session_for_company


def login_user(company_code: str, email: EmailStr, password: str):
    try:
        db_generator = get_session_for_company(company_code)
        db: Session = next(db_generator)
    except ValueError:
        return None

    try:
        user = get_user_by_email(db, email)

        if user is None:
            return None

        if not user.is_active:
            return None

        if not verify_password(password, user.password_hash):
            return None

        token = create_access_token(user.id, company_code)

        return token

    finally:
        db.close()