from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    ALLOWED_ORIGINS: str

    ZANGABIL_DATABASE_URL: str
    AWATAD_DATABASE_URL: str
    AL_ARABA_DATABASE_URL: str
    AL_KOWA_DATABASE_URL: str

    GOOGLE_DRIVE_ROOT_FOLDER_ID: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REFRESH_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore"
    )


settings = Settings()