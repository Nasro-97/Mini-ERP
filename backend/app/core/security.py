from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()

# Hashing the password using pwd_context
def hash_password(password: str) -> str:
    return password_hash.hash(password)

#verifying the password using pwd_context
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)

# Create the token and saving it using the user_id + expiry date as payload and adding SECRET_KEY and ALGORITHM to encode the token to JWT
def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return token

# Decoding the token using the SECRET_KEY and ALGORITHM to get the payload and then getting the user_id from the payload and returning it.
def decode_access_token(token: str) -> UUID | None:

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return UUID(user_id)

    except JWTError:
        return None