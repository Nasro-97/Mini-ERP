from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import os
import shutil
from uuid import uuid4

from app.core.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user, required_roles
from app.schemas.settings import SettingsOutput, SettingsUpdate
from app.services import settings as settings_service


router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("/", response_model=SettingsOutput)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    return settings_service.get_settings(db)


@router.patch("/", response_model=SettingsOutput)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    return settings_service.update_settings(db, data)


@router.post("/logo", response_model=SettingsOutput)
def upload_company_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    allowed_types = ["image/png", "image/jpeg", "image/webp", "image/svg+xml"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PNG, JPG, WEBP, and SVG are allowed.",
        )

    upload_dir = "uploads/company"
    os.makedirs(upload_dir, exist_ok=True)

    extension = os.path.splitext(file.filename)[1]
    filename = f"company-logo-{uuid4()}{extension}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    logo_url = f"/{file_path}"

    return settings_service.update_company_logo(db, logo_url)