from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, UTC
from sqlalchemy.sql import func

Base = declarative_base()


class Account(Base):
    """Account information for authentication."""

    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
