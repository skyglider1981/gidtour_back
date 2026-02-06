from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    """Пользователи системы"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(String(20), nullable=False)  # business, customer
    full_name = Column(String(255))
    phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    business_profile = relationship("BusinessProfile", back_populates="user", uselist=False)
    customer_profile = relationship("CustomerProfile", back_populates="user", uselist=False)
    bookings = relationship("Booking", back_populates="customer")
    
    # === НОВОЕ: Связь с отзывами ===
    reviews = relationship("Review", foreign_keys="Review.user_id", back_populates="user")


class BusinessProfile(Base):
    """Профиль бизнеса"""
    __tablename__ = "business_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    business_name = Column(String(255), nullable=False)
    description = Column(Text)
    logo_url = Column(String(500))
    city = Column(String(100))
    address = Column(Text)
    tax_id = Column(String(100))  # ИНН
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="business_profile")
    activities = relationship("Activity", back_populates="business")
    tours = relationship("Tour", back_populates="business")
    locations = relationship("Location", back_populates="business")
    resources = relationship("Resource", back_populates="business")
    instructors = relationship("Instructor", back_populates="business")


class CustomerProfile(Base):
    """Профиль клиента"""
    __tablename__ = "customer_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    birth_date = Column(DateTime)
    city = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    user = relationship("User", back_populates="customer_profile")
