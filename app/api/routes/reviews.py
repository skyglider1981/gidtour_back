# app/api/routes/reviews.py
"""
API для системы отзывов и рейтингов
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import Optional, List
from datetime import datetime

from app.core.database import get_db
from app.api.deps import get_current_user_optional, get_current_user, get_current_business_user
from app.models.user import User
from app.models.tour import Tour
from app.models.booking import Booking
from app.models.review import Review, ReviewVote, TourRatingStats
from app.schemas.review import (
    ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse,
    BusinessReplyCreate, ReviewVoteCreate, TourRatingStatsResponse,
    ReviewAuthor, RatingDistribution, DetailedRatings
)

router = APIRouter(tags=["Отзывы"])


# =====================================================
# ПУБЛИЧНЫЕ ЭНДПОИНТЫ (без авторизации)
# =====================================================

@router.get("/public/tours/{tour_id}/reviews", response_model=ReviewListResponse)
async def get_tour_reviews(
    tour_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    rating: Optional[int] = Query(None, ge=1, le=5),
    with_photos: Optional[bool] = None,
    with_text: Optional[bool] = None,
    verified_only: Optional[bool] = None,
    sort_by: str = Query("newest", pattern="^(newest|oldest|rating_high|rating_low|helpful)$"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Получить отзывы о туре (публичный)"""
    
    # Проверяем существование тура
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Базовый запрос
    query = db.query(Review).filter(
        Review.tour_id == tour_id,
        Review.is_published == True
    )
    
    # Фильтры
    if rating:
        query = query.filter(Review.rating == rating)
    if with_photos:
        query = query.filter(Review.photos != None, func.array_length(Review.photos, 1) > 0)
    if with_text:
        query = query.filter(Review.review_text != None, Review.review_text != '')
    if verified_only:
        query = query.filter(Review.is_verified == True)
    
    # Сортировка
    if sort_by == "newest":
        query = query.order_by(desc(Review.created_at))
    elif sort_by == "oldest":
        query = query.order_by(asc(Review.created_at))
    elif sort_by == "rating_high":
        query = query.order_by(desc(Review.rating), desc(Review.created_at))
    elif sort_by == "rating_low":
        query = query.order_by(asc(Review.rating), desc(Review.created_at))
    elif sort_by == "helpful":
        query = query.order_by(desc(Review.helpful_count), desc(Review.created_at))
    
    # Подсчёт общего количества
    total = query.count()
    
    # Пагинация
    offset = (page - 1) * per_page
    reviews = query.offset(offset).limit(per_page).all()
    
    # Формируем ответ
    items = []
    for review in reviews:
        # Определяем голос текущего пользователя
        user_vote = None
        if current_user:
            vote = db.query(ReviewVote).filter(
                ReviewVote.review_id == review.id,
                ReviewVote.user_id == current_user.id
            ).first()
            if vote:
                user_vote = vote.vote_type
        
        # Формируем автора
        author_name = "Анонимный пользователь" if review.is_anonymous else (
            review.author_name or (review.user.full_name if review.user else "Гость")
        )
        
        items.append(ReviewResponse(
            id=review.id,
            tour_id=review.tour_id,
            booking_id=review.booking_id,
            author=ReviewAuthor(
                id=review.user_id if not review.is_anonymous else None,
                name=author_name,
                is_verified=review.is_verified,
                reviews_count=db.query(Review).filter(Review.user_id == review.user_id).count() if review.user_id else 0
            ),
            is_anonymous=review.is_anonymous,
            is_verified=review.is_verified,
            rating=review.rating,
            rating_guide=review.rating_guide,
            rating_organization=review.rating_organization,
            rating_value=review.rating_value,
            rating_safety=review.rating_safety,
            title=review.title,
            review_text=review.review_text,
            pros=review.pros,
            cons=review.cons,
            photos=review.photos or [],
            helpful_count=review.helpful_count,
            not_helpful_count=review.not_helpful_count,
            user_vote=user_vote,
            business_reply=review.business_reply,
            business_reply_at=review.business_reply_at,
            visit_date=review.visit_date,
            created_at=review.created_at
        ))
    
    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.get("/public/tours/{tour_id}/rating", response_model=TourRatingStatsResponse)
async def get_tour_rating_stats(
    tour_id: int,
    db: Session = Depends(get_db)
):
    """Получить статистику рейтинга тура"""
    
    # Пробуем получить из кэш-таблицы
    stats = db.query(TourRatingStats).filter(TourRatingStats.tour_id == tour_id).first()
    
    if stats:
        return TourRatingStatsResponse(
            tour_id=tour_id,
            total_reviews=stats.total_reviews,
            average_rating=float(stats.average_rating) if stats.average_rating else 0,
            distribution=RatingDistribution(
                rating_1=stats.rating_1_count,
                rating_2=stats.rating_2_count,
                rating_3=stats.rating_3_count,
                rating_4=stats.rating_4_count,
                rating_5=stats.rating_5_count
            ),
            detailed=DetailedRatings(
                guide=float(stats.avg_rating_guide) if stats.avg_rating_guide else None,
                organization=float(stats.avg_rating_organization) if stats.avg_rating_organization else None,
                value=float(stats.avg_rating_value) if stats.avg_rating_value else None,
                safety=float(stats.avg_rating_safety) if stats.avg_rating_safety else None
            )
        )
    
    # Если нет в кэше — возвращаем пустую статистику
    return TourRatingStatsResponse(
        tour_id=tour_id,
        total_reviews=0,
        average_rating=0,
        distribution=RatingDistribution(),
        detailed=DetailedRatings()
    )


# =====================================================
# СОЗДАНИЕ ОТЗЫВА (требует авторизации или гостевые данные)
# =====================================================

@router.post("/public/reviews", response_model=ReviewResponse)
async def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Создать отзыв о туре"""
    
    # Проверяем тур
    tour = db.query(Tour).filter(Tour.id == data.tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Проверяем бронирование (если указано)
    booking = None
    is_verified = False
    if data.booking_id:
        booking = db.query(Booking).filter(
            Booking.id == data.booking_id,
            Booking.status == 'completed'
        ).first()
        if not booking:
            raise HTTPException(status_code=400, detail="Бронирование не найдено или не завершено")
        
        # Проверяем что бронирование относится к этому туру
        if booking.tour_schedule and booking.tour_schedule.tour_id != data.tour_id:
            raise HTTPException(status_code=400, detail="Бронирование не относится к этому туру")
        
        # Проверяем что отзыв ещё не оставлен
        existing = db.query(Review).filter(Review.booking_id == data.booking_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Отзыв на это бронирование уже существует")
        
        is_verified = True
    
    # Для гостей требуем имя
    if not current_user and not data.author_name:
        raise HTTPException(status_code=400, detail="Укажите ваше имя")
    
    # Создаём отзыв
    review = Review(
        booking_id=data.booking_id,
        tour_id=data.tour_id,
        user_id=current_user.id if current_user else None,
        author_name=data.author_name or (current_user.full_name if current_user else None),
        author_email=data.author_email or (current_user.email if current_user else None),
        rating=data.rating,
        title=data.title,
        review_text=data.review_text,
        pros=data.pros,
        cons=data.cons,
        rating_guide=data.rating_guide,
        rating_organization=data.rating_organization,
        rating_value=data.rating_value,
        rating_safety=data.rating_safety,
        photos=data.photos or [],
        is_verified=is_verified,
        is_anonymous=data.is_anonymous,
        visit_date=data.visit_date
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    # Формируем ответ
    author_name = "Анонимный пользователь" if review.is_anonymous else (
        review.author_name or "Гость"
    )
    
    return ReviewResponse(
        id=review.id,
        tour_id=review.tour_id,
        booking_id=review.booking_id,
        author=ReviewAuthor(
            id=review.user_id if not review.is_anonymous else None,
            name=author_name,
            is_verified=review.is_verified,
            reviews_count=1
        ),
        is_anonymous=review.is_anonymous,
        is_verified=review.is_verified,
        rating=review.rating,
        rating_guide=review.rating_guide,
        rating_organization=review.rating_organization,
        rating_value=review.rating_value,
        rating_safety=review.rating_safety,
        title=review.title,
        review_text=review.review_text,
        pros=review.pros,
        cons=review.cons,
        photos=review.photos or [],
        helpful_count=0,
        not_helpful_count=0,
        user_vote=None,
        business_reply=None,
        business_reply_at=None,
        visit_date=review.visit_date,
        created_at=review.created_at
    )


# =====================================================
# ГОЛОСОВАНИЕ ЗА ПОЛЕЗНОСТЬ
# =====================================================

@router.post("/public/reviews/{review_id}/vote")
async def vote_review(
    review_id: int,
    data: ReviewVoteCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Проголосовать за полезность отзыва"""
    
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    # Проверяем не голосовал ли уже
    existing_vote = None
    if current_user:
        existing_vote = db.query(ReviewVote).filter(
            ReviewVote.review_id == review_id,
            ReviewVote.user_id == current_user.id
        ).first()
    elif data.session_id:
        existing_vote = db.query(ReviewVote).filter(
            ReviewVote.review_id == review_id,
            ReviewVote.session_id == data.session_id
        ).first()
    
    if existing_vote:
        # Обновляем голос
        existing_vote.vote_type = data.vote_type
        db.commit()
        return {"message": "Голос обновлён", "vote_type": data.vote_type}
    
    # Создаём новый голос
    vote = ReviewVote(
        review_id=review_id,
        user_id=current_user.id if current_user else None,
        session_id=data.session_id if not current_user else None,
        vote_type=data.vote_type
    )
    db.add(vote)
    db.commit()
    
    return {"message": "Голос учтён", "vote_type": data.vote_type}


# =====================================================
# БИЗНЕС-ЭНДПОИНТЫ (для владельцев туров)
# =====================================================

@router.get("/business/reviews", response_model=ReviewListResponse)
async def get_business_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    tour_id: Optional[int] = None,
    rating: Optional[int] = Query(None, ge=1, le=5),
    has_reply: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить отзывы на туры бизнеса"""
    
    business_id = current_user.business_profile.id
    
    # Получаем ID туров бизнеса
    tour_ids = db.query(Tour.id).filter(Tour.business_id == business_id).all()
    tour_ids = [t[0] for t in tour_ids]
    
    if not tour_ids:
        return ReviewListResponse(items=[], total=0, page=page, per_page=per_page, pages=0)
    
    # Базовый запрос
    query = db.query(Review).filter(Review.tour_id.in_(tour_ids))
    
    # Фильтры
    if tour_id:
        query = query.filter(Review.tour_id == tour_id)
    if rating:
        query = query.filter(Review.rating == rating)
    if has_reply is not None:
        if has_reply:
            query = query.filter(Review.business_reply != None)
        else:
            query = query.filter(Review.business_reply == None)
    
    query = query.order_by(desc(Review.created_at))
    
    total = query.count()
    offset = (page - 1) * per_page
    reviews = query.offset(offset).limit(per_page).all()
    
    # Формируем ответ (аналогично публичному)
    items = []
    for review in reviews:
        author_name = "Анонимный пользователь" if review.is_anonymous else (
            review.author_name or (review.user.full_name if review.user else "Гость")
        )
        
        items.append(ReviewResponse(
            id=review.id,
            tour_id=review.tour_id,
            booking_id=review.booking_id,
            author=ReviewAuthor(
                id=review.user_id,
                name=author_name,
                is_verified=review.is_verified,
                reviews_count=0
            ),
            is_anonymous=review.is_anonymous,
            is_verified=review.is_verified,
            rating=review.rating,
            rating_guide=review.rating_guide,
            rating_organization=review.rating_organization,
            rating_value=review.rating_value,
            rating_safety=review.rating_safety,
            title=review.title,
            review_text=review.review_text,
            pros=review.pros,
            cons=review.cons,
            photos=review.photos or [],
            helpful_count=review.helpful_count,
            not_helpful_count=review.not_helpful_count,
            user_vote=None,
            business_reply=review.business_reply,
            business_reply_at=review.business_reply_at,
            visit_date=review.visit_date,
            created_at=review.created_at
        ))
    
    return ReviewListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=(total + per_page - 1) // per_page
    )


@router.post("/business/reviews/{review_id}/reply")
async def reply_to_review(
    review_id: int,
    data: BusinessReplyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Ответить на отзыв"""
    
    business_id = current_user.business_profile.id
    
    review = db.query(Review).join(Tour).filter(
        Review.id == review_id,
        Tour.business_id == business_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    review.business_reply = data.reply_text
    review.business_reply_at = datetime.utcnow()
    review.business_reply_by = current_user.id
    
    db.commit()
    
    return {"message": "Ответ добавлен", "reply": data.reply_text}


@router.delete("/business/reviews/{review_id}/reply")
async def delete_reply(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить ответ на отзыв"""
    
    business_id = current_user.business_profile.id
    
    review = db.query(Review).join(Tour).filter(
        Review.id == review_id,
        Tour.business_id == business_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    review.business_reply = None
    review.business_reply_at = None
    review.business_reply_by = None
    
    db.commit()
    
    return {"message": "Ответ удалён"}


# =====================================================
# МОДЕРАЦИЯ (скрытие отзывов)
# =====================================================

@router.patch("/business/reviews/{review_id}/visibility")
async def toggle_review_visibility(
    review_id: int,
    is_published: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Скрыть/показать отзыв (только для явно оскорбительных)"""
    
    business_id = current_user.business_profile.id
    
    review = db.query(Review).join(Tour).filter(
        Review.id == review_id,
        Tour.business_id == business_id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    
    review.is_published = is_published
    db.commit()
    
    return {"message": "Статус изменён", "is_published": is_published}
