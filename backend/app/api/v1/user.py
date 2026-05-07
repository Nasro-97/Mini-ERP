from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services import user as user_service
from app.models import User

router = APIRouter(prefix="/users", tags=["Users"])

#Creating the user route
@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(user_data: UserCreate ,db: Session = Depends(get_db)):
    existing_email = user_service.get_user_by_email(db, user_data.email)
    existing_username = user_service.get_user_by_username(db, user_data.username)

    #Checking if the username or email already exists
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with this email already exists")
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="User with this username already exists")

    return user_service.create_user(db, user_data)

#get users route
@router.get("/", response_model=list[UserOut], status_code=status.HTTP_200_OK)
def get_users(db: Session = Depends(get_db)):
    return user_service.get_users(db)

# current user from the token
@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

#getting users by id route
@router.get("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_user_by_id(user_id: UUID, db: Session = Depends(get_db)):
    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# Update user information route
@router.patch("/{user_id}", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_user( user_id:UUID, user_data: UserUpdate, db: Session = Depends(get_db)):
    user = user_service.update_user(db, user_data, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

# deactivate_user route
@router.patch("/{user_id}/deactivate", response_model=UserOut, status_code=status.HTTP_200_OK)
def deactivate_user( user_id:UUID, db: Session = Depends(get_db)):
    user = user_service.deactivate_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user

@router.patch("/{user_id}/activate", response_model=UserOut, status_code=status.HTTP_200_OK)
def activate_user( user_id:UUID, db: Session = Depends(get_db)):
    user = user_service.activate_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


