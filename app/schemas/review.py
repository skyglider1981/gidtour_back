# app/schemas/review.py
"""
Pydantic схемы для системы отзывов
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date


# === СОЗДАНИЕ ОТЗЫВА ===

class ReviewCreate(BaseModel):
    """Создание отзыва"""
    tour_id: int
    booking_id: Optional[int] = None  # Если есть бронирование
    
    # Рейтинг
    rating: int = Field(..., ge=1, le=5, description="Общая оценка от 1 до 5")
    
    # Текст
    title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    
    # Детальные оценки (опционально)
    rating_guide: Optional[int] = Field(None, ge=1, le=5)
    rating_organization: Optional[int] = Field(None, ge=1, le=5)
    rating_value: Optional[int] = Field(None, ge=1, le=5)
    rating_safety: Optional[int] = Field(None, ge=1, le=5)
    
    # Фото
    photos: Optional[List[str]] = []
    
    # Опции
    is_anonymous: bool = False
    visit_date: Optional[date] = None
    
    # Для гостей (если нет user_id)
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class ReviewUpdate(BaseModel):
    """Обновление отзыва (только автором)"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    review_text: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    rating_guide: Optional[int] = Field(None, ge=1, le=5)
    rating_organization: Optional[int] = Field(None, ge=1, le=5)
    rating_value: Optional[int] = Field(None, ge=1, le=5)
    rating_safety: Optional[int] = Field(None, ge=1, le=5)
    photos: Optional[List[str]] = None


# === ОТВЕТ БИЗНЕСА ===

class BusinessReplyCreate(BaseModel):
    """Ответ бизнеса на отзыв"""
    reply_text: str = Field(..., min_length=10, max_length=2000)


# === ГОЛОСОВАНИЕ ===

class ReviewVoteCreate(BaseModel):
    """Голос за полезность"""
    vote_type: str = Field(..., pattern="^(helpful|not_helpful)$")
    session_id: Optional[str] = None  # Для гостей


# === ОТВЕТЫ API ===

class ReviewAuthor(BaseModel):
    """Информация об авторе отзыва"""
    id: Optional[int] = None
    name: str
    is_verified: bool = False
    reviews_count: int = 0
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    """Полный ответ отзыва"""
    id: int
    tour_id: int
    booking_id: Optional[int] = None
    
    # Автор
    author: ReviewAuthor
    is_anonymous: bool
    is_verified: bool
    
    # Рейтинг
    rating: int
    rating_guide: Optional[int] = None
    rating_organization: Optional[int] = None
    rating_value: Optional[int] = None
    rating_safety: Optional[int] = None
    
    # Текст
    title: Optional[str] = None
    review_text: Optional[str] = None
    pros: Optional[str] = None
    cons: Optional[str] = None
    
    # Фото
    photos: List[str] = []
    
    # Полезность
    helpful_count: int = 0
    not_helpful_count: int = 0
    user_vote: Optional[str] = None  # Голос текущего пользователя
    
    # Ответ бизнеса
    business_reply: Optional[str] = None
    business_reply_at: Optional[datetime] = None
    
    # Даты
    visit_date: Optional[date] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewListResponse(BaseModel):
    """Список отзывов с пагинацией"""
    items: List[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int


# === СТАТИСТИКА РЕЙТИНГА ===

class RatingDistribution(BaseModel):
    """Распределение оценок"""
    rating_1: int = 0
    rating_2: int = 0
    rating_3: int = 0
    rating_4: int = 0
    rating_5: int = 0


class DetailedRatings(BaseModel):
    """Детальные средние оценки"""
    guide: Optional[float] = None
    organization: Optional[float] = None
    value: Optional[float] = None
    safety: Optional[float] = None


class TourRatingStatsResponse(BaseModel):
    """Статистика рейтинга тура"""
    tour_id: int
    total_reviews: int
    average_rating: float
    distribution: RatingDistribution
    detailed: DetailedRatings
    
    class Config:
        from_attributes = True


# === ФИЛЬТРЫ ===

class ReviewFilters(BaseModel):
    """Фильтры для списка отзывов"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    with_photos: Optional[bool] = None
    with_text: Optional[bool] = None
    verified_only: Optional[bool] = None
    sort_by: str = Field("newest", pattern="^(newest|oldest|rating_high|rating_low|helpful)$")
