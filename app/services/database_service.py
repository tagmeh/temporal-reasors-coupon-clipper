from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.db import Base

from dotenv import dotenv_values

config = dotenv_values(".env")

ENV = config.get("ENV", "dev")

DATABASE_URL = {
    "dev": "sqlite:///coupons.db",
    "prod": "postgresql://user:password@localhost:5432/coupons",  # Not active yet.
}[ENV]

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)


def get_session():
    return SessionLocal()
