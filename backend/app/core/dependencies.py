# Need dependencies for the login --> use the login token to auth and execute protected routes
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


bearer_scheme = HTTPBearer()

# get the loged in user token
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),db: Session = Depends(get_db)):

    token = credentials.credentials
    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid or expired token",)

    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

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
