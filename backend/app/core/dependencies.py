# Need dependencies for the login --> use the login token to auth and execute protected routes
from fastapi.security import HTTPBearer
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

bearer_scheme = HTTPBearer()

# get the logged-in user token
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload["user_id"]
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user

# checking the user-role before granting access to specific action
def required_roles(allowed_roles: list[str]):
    def role_checker(current_user=Depends(get_current_user)):

        user_roles = [role.name for role in current_user.roles]

        # Check if the user has at least one allowed role
        has_permission = any(role in allowed_roles for role in user_roles)

        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return current_user

    return role_checker
