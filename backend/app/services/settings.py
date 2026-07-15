from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.settings import Settings
from app.schemas.settings import SettingsUpdate


def get_settings(db: Session) -> Settings:
    settings = db.execute(select(Settings)).scalar_one_or_none()

    if not settings:
        settings = Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


def update_settings(db: Session, data: SettingsUpdate) -> Settings:
    settings = get_settings(db)

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(settings, field, value)

    db.commit()
    db.refresh(settings)

    return settings


def update_company_logo(db: Session, logo_url: str) -> Settings:
    settings = get_settings(db)

    settings.company_logo_url = logo_url

    db.commit()
    db.refresh(settings)

    return settings