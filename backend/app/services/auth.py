from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.services.user import get_user_by_email


def login_user(db:Session, email: EmailStr, password: str):
    user = get_user_by_email(db ,email)

    # User does not exist
    if user is None:
        return None

    # User is deactivated
    if not user.is_active:
        return None

    # Password is wrong
    if not verify_password(password, user.password_hash):
        return None

    token = create_access_token(user.id)
    return token