from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import login_user


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(login_data: LoginRequest):
    token = login_user(
        company_code=login_data.company_code,
        email=login_data.email,
        password=login_data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid company, email, or password",
        )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
    )