from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALLOWED_ORIGINS: str

    ZANGABIL_DATABASE_URL: str
    AWATAD_DATABASE_URL: str
    AL_ARABA_DATABASE_URL:str
    AL_KOWA_DATABASE_URL: str

    class Config:
        env_file = ".env"

settings = Settings()

