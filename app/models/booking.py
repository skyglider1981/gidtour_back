# app/models/booking.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Text, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Booking(Base):
    """Модель бронирования тура/активности"""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    booking_type = Column(String(20), nullable=False)  # 'activity' или 'tour'
    
    # Связь с расписанием
    activity_schedule_id = Column(Integer, nullable=True)
    tour_schedule_id = Column(Integer, ForeignKey("tour_schedules.id"), nullable=True)
    
    # Данные бронирования
    participants_count = Column(Integer, nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default='RUB')
    status = Column(String(20), default='pending')  # pending, confirmed, paid, cancelled, completed
    
    # Контакты клиента (если без регистрации)
    customer_name = Column(String(255))
    customer_phone = Column(String(50))
    customer_email = Column(String(255))
    notes = Column(Text)
    
    # Даты
    created_at = Column(DateTime, server_default=func.now())
    confirmed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    customer = relationship("User", back_populates="bookings", foreign_keys=[customer_id])
    tour_schedule = relationship("TourSchedule", back_populates="bookings")
    booking_resources = relationship("BookingResource", back_populates="booking", cascade="all, delete-orphan")
    
    # === НОВОЕ: Связь с отзывом ===
    review = relationship("Review", back_populates="booking", uselist=False)
    
    __table_args__ = (
        CheckConstraint(
            "booking_type IN ('activity', 'tour')",
            name='bookings_booking_type_check'
        ),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'paid', 'cancelled', 'completed')",
            name='bookings_status_check'
        ),
    )


class BookingResource(Base):
    """Ресурсы, зарезервированные для бронирования"""
    __tablename__ = "booking_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    price_per_unit = Column(Numeric(10, 2), nullable=True)
    
    # Relationships
    booking = relationship("Booking", back_populates="booking_resources")
    resource = relationship("Resource")
