from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


COMPANY_DATABASE_URLS = {
    "zangabil": settings.ZANGABIL_DATABASE_URL,
    "awatad": settings.AWATAD_DATABASE_URL,
    "al_araba": settings.AL_ARABA_DATABASE_URL,
    "al_kowa": settings.AL_KOWA_DATABASE_URL,
}


engines = {}
SessionLocals = {}


for company_code, db_url in COMPANY_DATABASE_URLS.items():
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
    )

    engines[company_code] = engine

    SessionLocals[company_code] = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )


def get_session_for_company(company_code: str):
    SessionLocal = SessionLocals.get(company_code)

    if SessionLocal is None:
        raise ValueError("Invalid company code")

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()