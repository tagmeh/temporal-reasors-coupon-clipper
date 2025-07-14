from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database_utils.schemas import Base


# Get the base directory of your app (always relative to this file)
BASE_DIR = Path(__file__).resolve().parent.parent  # app/

# Full path to database file
DB_PATH = BASE_DIR / "database" / "coupons.db"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
