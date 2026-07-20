from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
import tempfile
from app.core.config import settings
from app.services.google_drive import upload_or_replace_file, get_or_create_folder
import os
import shutil

from app.core.database import get_db
from app.models.user import User
from app.core.dependencies import required_roles
from app.schemas.settings import SettingsOutput, SettingsUpdate
from app.services import settings as settings_service


router = APIRouter(prefix="/settings", tags=["Settings"])

COMPANY_FOLDER_NAMES = {
    "zangabil": "Zangabil",
    "awatad": "Awatad",
    "al_araba": "Al Araba",
    "al_kowa": "Al Kowa",
}


@router.get("/", response_model=SettingsOutput)
def get_settings(db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    return settings_service.get_settings(db)


@router.patch("/", response_model=SettingsOutput)
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):
    return settings_service.update_settings(db, data)


@router.post("/logo", response_model=SettingsOutput)
def upload_company_logo(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(required_roles(["COD"]))):

    allowed_types = [
        "image/png",
        "image/jpeg",
        "image/webp",
        "image/svg+xml"
    ]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PNG, JPG, WEBP, and SVG are allowed.",
        )

    company_code = db.info["company_code"]

    # create temporary file
    extension = os.path.splitext(file.filename)[1]

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=extension
    ) as temp_file:

        shutil.copyfileobj(file.file, temp_file)
        temp_path = temp_file.name


    try:
        # find or create company folder
        company_folder = get_or_create_folder(
            folder_name= COMPANY_FOLDER_NAMES[company_code],
            parent_folder_id=settings.GOOGLE_DRIVE_ROOT_FOLDER_ID,
        )

        # upload/replace logo
        uploaded_logo = upload_or_replace_file(
            file_path=temp_path,
            filename="company-logo" + extension,
            parent_folder_id=company_folder["id"],
            mime_type=file.content_type,
        )

        file_id = uploaded_logo["id"]
        logo_url = f"https://drive.google.com/uc?export=view&id={file_id}"

    finally:
        # remove temporary file
        os.remove(temp_path)


    return settings_service.update_company_logo(db, logo_url)