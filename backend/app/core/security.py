from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: UUID, company_code: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "company_code": company_code,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        user_id = payload.get("sub")
        company_code = payload.get("company_code")

        if user_id is None or company_code is None:
            return None

        return {
            "user_id": UUID(user_id),
            "company_code": company_code,
        }

    except JWTError:
        return None