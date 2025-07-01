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

    redeemed_coupons = relationship("RedeemedCoupon", back_populates="user")


class RedeemedCoupon(Base):
    """Contains a relationship of coupons that have been redeemed and by which user."""

    __tablename__ = "redeemed_coupons"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("accounts.id"), index=True)
    coupon_id = Column(Integer, ForeignKey("coupons.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    coupon = relationship("DBCoupon", back_populates="redeemed_by")
    user = relationship("Account", back_populates="redeemed_coupons")


class DBCoupon(Base):
    """Coupon object"""

    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    coupon_id = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String)
    brand = Column(String)
    price = Column(Float)
    price_off = Column(Float)
    start_date = Column(Date, default=datetime.now(UTC))
    finish_date = Column(Date, default=datetime.now(UTC))
    clip_start_date = Column(Date, default=datetime.now(UTC))
    clip_end_date = Column(Date, default=datetime.now(UTC))

    redeemed_by = relationship("RedeemedCoupon", back_populates="coupon")
