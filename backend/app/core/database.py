from sqlalchemy.orm import sessionmaker, DeclarativeBase
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.core.company_database import get_session_for_company


class Base(DeclarativeBase):
    pass


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


def get_company_code_from_token(token: str = Depends(oauth2_scheme)) -> str:
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    company_code = payload.get("company_code")

    if not company_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing company code in token",
        )

    return company_code


def get_db(company_code: str = Depends(get_company_code_from_token)):
    db_generator = get_session_for_company(company_code)
    db = next(db_generator)

    try:
        yield db
    finally:
        db.close()