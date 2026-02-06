# app/models/review.py
"""
Модели для системы отзывов и рейтингов
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Date, Numeric, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Review(Base):
    """Отзывы о турах"""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связи
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Данные автора (для гостевых бронирований)
    author_name = Column(String(255))
    author_email = Column(String(255))
    
    # Рейтинг и текст
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(255))
    review_text = Column(Text)
    
    # Детальная оценка
    rating_guide = Column(Integer)           # Оценка гида
    rating_organization = Column(Integer)    # Организация
    rating_value = Column(Integer)           # Цена/качество
    rating_safety = Column(Integer)          # Безопасность
    
    # Плюсы/минусы
    pros = Column(Text)
    cons = Column(Text)
    
    # Фото от клиента
    photos = Column(ARRAY(Text))
    
    # Статусы
    is_verified = Column(Boolean, default=False)    # Подтверждённая покупка
    is_published = Column(Boolean, default=True)    # Опубликован
    is_anonymous = Column(Boolean, default=False)   # Анонимный
    
    # Ответ бизнеса
    business_reply = Column(Text)
    business_reply_at = Column(DateTime)
    business_reply_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    
    # Полезность
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)
    
    # Метаданные
    visit_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    booking = relationship("Booking", back_populates="review")
    tour = relationship("Tour", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id], back_populates="reviews")
    replier = relationship("User", foreign_keys=[business_reply_by])
    votes = relationship("ReviewVote", back_populates="review", cascade="all, delete-orphan")


class ReviewVote(Base):
    """Голоса за полезность отзывов"""
    __tablename__ = "review_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    session_id = Column(String(100))  # Для гостей
    vote_type = Column(String(10), nullable=False)  # 'helpful' или 'not_helpful'
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    review = relationship("Review", back_populates="votes")
    user = relationship("User")


class TourRatingStats(Base):
    """Агрегированная статистика рейтингов по турам"""
    __tablename__ = "tour_rating_stats"
    
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"), primary_key=True)
    
    # Общая статистика
    total_reviews = Column(Integer, default=0)
    average_rating = Column(Numeric(3, 2), default=0)
    
    # Распределение по звёздам
    rating_1_count = Column(Integer, default=0)
    rating_2_count = Column(Integer, default=0)
    rating_3_count = Column(Integer, default=0)
    rating_4_count = Column(Integer, default=0)
    rating_5_count = Column(Integer, default=0)
    
    # Детальные средние
    avg_rating_guide = Column(Numeric(3, 2))
    avg_rating_organization = Column(Numeric(3, 2))
    avg_rating_value = Column(Numeric(3, 2))
    avg_rating_safety = Column(Numeric(3, 2))
    
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    tour = relationship("Tour", back_populates="rating_stats")
