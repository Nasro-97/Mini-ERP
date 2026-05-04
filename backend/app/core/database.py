from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , DeclarativeBase
from config import Settings

engine = create_engine(Settings.DATABASE_URL)

class Base(DeclarativeBase):
    pass

def get_db():
    db = sessionmaker()
    try:
        yield db
    finally:
        db.close()
