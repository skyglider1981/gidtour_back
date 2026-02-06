# app/api/routes/customer_api.py
"""
API для личного кабинета туриста (customer)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from datetime import date, datetime

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_customer_user
from app.models.user import User, CustomerProfile
from app.models.booking import Booking
from app.models.tour import Tour, TourSchedule, TourActivity
from app.models.activity import Activity, Location
from app.models.review import Review
from pydantic import BaseModel, EmailStr
from decimal import Decimal


router = APIRouter(prefix="/customer", tags=["Customer Account"])


# ========== СХЕМЫ ==========

class CustomerProfileUpdate(BaseModel):
    """Обновление профиля клиента"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    city: Optional[str] = None


class CustomerProfileResponse(BaseModel):
    """Профиль клиента"""
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    city: Optional[str] = None
    created_at: datetime
    bookings_count: int = 0
    completed_tours: int = 0
    
    class Config:
        from_attributes = True


class CustomerBookingResponse(BaseModel):
    """Бронирование для ЛК туриста"""
    id: int
    booking_code: str
    status: str
    
    # Информация о туре
    tour_id: Optional[int] = None
    tour_name: Optional[str] = None
    tour_photo: Optional[str] = None
    
    # Дата и время
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None
    
    # Детали
    participants_count: int
    total_price: float
    currency: str = 'RUB'
    
    # Даты событий
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Можно ли оставить отзыв
    can_review: bool = False
    has_review: bool = False
    
    class Config:
        from_attributes = True


class CustomerBookingsListResponse(BaseModel):
    """Список бронирований с пагинацией"""
    items: List[CustomerBookingResponse]
    total: int
    page: int
    per_page: int
    pages: int


class TourRecommendation(BaseModel):
    """Рекомендованный тур"""
    id: int
    name: str
    short_description: Optional[str] = None
    base_price: float
    duration_minutes: Optional[int] = None
    photo: Optional[str] = None
    difficulty_level: Optional[str] = None
    location_name: Optional[str] = None
    reason: str  # Почему рекомендуем
    
    class Config:
        from_attributes = True


class CustomerStatsResponse(BaseModel):
    """Статистика клиента"""
    total_bookings: int = 0
    completed_tours: int = 0
    cancelled_bookings: int = 0
    total_spent: float = 0.0
    favorite_activity_type: Optional[str] = None
    member_since: datetime


# ========== ПРОФИЛЬ ==========

@router.get("/profile", response_model=CustomerProfileResponse)
async def get_customer_profile(
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Получить профиль текущего пользователя"""
    
    # Считаем статистику
    bookings_count = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id
    ).scalar() or 0
    
    completed_tours = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id,
        Booking.status == 'completed'
    ).scalar() or 0
    
    # Получаем данные профиля
    profile = current_user.customer_profile
    
    return {
        'id': current_user.id,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'phone': current_user.phone,
        'birth_date': profile.birth_date if profile else None,
        'city': profile.city if profile else None,
        'created_at': current_user.created_at,
        'bookings_count': bookings_count,
        'completed_tours': completed_tours
    }


@router.put("/profile", response_model=CustomerProfileResponse)
async def update_customer_profile(
    data: CustomerProfileUpdate,
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Обновить профиль пользователя"""
    
    # Обновляем данные пользователя
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.phone is not None:
        current_user.phone = data.phone
    
    # Обновляем профиль клиента
    profile = current_user.customer_profile
    if not profile:
        profile = CustomerProfile(user_id=current_user.id)
        db.add(profile)
    
    if data.birth_date is not None:
        profile.birth_date = data.birth_date
    if data.city is not None:
        profile.city = data.city
    
    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    
    # Считаем статистику
    bookings_count = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id
    ).scalar() or 0
    
    completed_tours = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id,
        Booking.status == 'completed'
    ).scalar() or 0
    
    return {
        'id': current_user.id,
        'email': current_user.email,
        'full_name': current_user.full_name,
        'phone': current_user.phone,
        'birth_date': profile.birth_date,
        'city': profile.city,
        'created_at': current_user.created_at,
        'bookings_count': bookings_count,
        'completed_tours': completed_tours
    }


# ========== СТАТИСТИКА ==========

@router.get("/stats", response_model=CustomerStatsResponse)
async def get_customer_stats(
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Получить статистику клиента"""
    
    # Общее количество бронирований
    total_bookings = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id
    ).scalar() or 0
    
    # Завершённые туры
    completed_tours = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id,
        Booking.status == 'completed'
    ).scalar() or 0
    
    # Отменённые бронирования
    cancelled_bookings = db.query(func.count(Booking.id)).filter(
        Booking.customer_id == current_user.id,
        Booking.status == 'cancelled'
    ).scalar() or 0
    
    # Общая сумма потраченных средств (только оплаченные)
    total_spent = db.query(func.coalesce(func.sum(Booking.total_price), 0)).filter(
        Booking.customer_id == current_user.id,
        Booking.status.in_(['paid', 'completed'])
    ).scalar() or 0
    
    # Любимый тип активности (по количеству бронирований)
    favorite_activity = None
    activity_stats = db.query(
        Activity.activity_type_id,
        func.count(Booking.id).label('cnt')
    ).join(
        TourActivity, TourActivity.activity_id == Activity.id
    ).join(
        TourSchedule, TourSchedule.tour_id == TourActivity.tour_id
    ).join(
        Booking, Booking.tour_schedule_id == TourSchedule.id
    ).filter(
        Booking.customer_id == current_user.id,
        Booking.status.in_(['confirmed', 'paid', 'completed'])
    ).group_by(
        Activity.activity_type_id
    ).order_by(
        desc('cnt')
    ).first()
    
    if activity_stats:
        from app.models.activity import ActivityType
        activity_type = db.query(ActivityType).filter(
            ActivityType.id == activity_stats[0]
        ).first()
        if activity_type:
            favorite_activity = activity_type.name
    
    return {
        'total_bookings': total_bookings,
        'completed_tours': completed_tours,
        'cancelled_bookings': cancelled_bookings,
        'total_spent': float(total_spent),
        'favorite_activity_type': favorite_activity,
        'member_since': current_user.created_at
    }


# ========== БРОНИРОВАНИЯ ==========

@router.get("/bookings", response_model=CustomerBookingsListResponse)
async def get_customer_bookings(
    status: Optional[str] = Query(None, description="Фильтр по статусу: pending, confirmed, paid, completed, cancelled"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Получить список бронирований текущего пользователя"""
    
    query = db.query(Booking).filter(Booking.customer_id == current_user.id)
    
    # Фильтр по статусу
    if status:
        query = query.filter(Booking.status == status)
    
    # Общее количество
    total = query.count()
    
    # Пагинация
    pages = (total + per_page - 1) // per_page
    offset = (page - 1) * per_page
    
    bookings = query.order_by(desc(Booking.created_at)).offset(offset).limit(per_page).all()
    
    # Формируем ответ
    items = []
    for booking in bookings:
        tour_id = None
        tour_name = None
        tour_photo = None
        schedule_date = None
        schedule_time = None
        can_review = False
        has_review = False
        
        if booking.tour_schedule_id:
            schedule = db.query(TourSchedule).filter(
                TourSchedule.id == booking.tour_schedule_id
            ).first()
            
            if schedule:
                schedule_date = str(schedule.date)
                schedule_time = f"{schedule.start_time} - {schedule.end_time}"
                
                tour = db.query(Tour).filter(Tour.id == schedule.tour_id).first()
                if tour:
                    tour_id = tour.id
                    tour_name = tour.name
                    tour_photo = tour.photos[0] if tour.photos else None
        
        # Проверяем, можно ли оставить отзыв (завершённые бронирования)
        if booking.status == 'completed':
            can_review = True
            # Проверяем, есть ли уже отзыв
            existing_review = db.query(Review).filter(
                Review.booking_id == booking.id
            ).first()
            has_review = existing_review is not None
            can_review = not has_review
        
        items.append({
            'id': booking.id,
            'booking_code': booking.booking_code,
            'status': booking.status,
            'tour_id': tour_id,
            'tour_name': tour_name,
            'tour_photo': tour_photo,
            'schedule_date': schedule_date,
            'schedule_time': schedule_time,
            'participants_count': booking.participants_count,
            'total_price': float(booking.total_price),
            'currency': booking.currency or 'RUB',
            'created_at': booking.created_at,
            'confirmed_at': booking.confirmed_at,
            'paid_at': booking.paid_at,
            'cancelled_at': booking.cancelled_at,
            'can_review': can_review,
            'has_review': has_review
        })
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': pages
    }


@router.get("/bookings/{booking_id}", response_model=CustomerBookingResponse)
async def get_customer_booking(
    booking_id: int,
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Получить детали конкретного бронирования"""
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    tour_id = None
    tour_name = None
    tour_photo = None
    schedule_date = None
    schedule_time = None
    can_review = False
    has_review = False
    
    if booking.tour_schedule_id:
        schedule = db.query(TourSchedule).filter(
            TourSchedule.id == booking.tour_schedule_id
        ).first()
        
        if schedule:
            schedule_date = str(schedule.date)
            schedule_time = f"{schedule.start_time} - {schedule.end_time}"
            
            tour = db.query(Tour).filter(Tour.id == schedule.tour_id).first()
            if tour:
                tour_id = tour.id
                tour_name = tour.name
                tour_photo = tour.photos[0] if tour.photos else None
    
    # Проверяем отзыв
    if booking.status == 'completed':
        can_review = True
        existing_review = db.query(Review).filter(
            Review.booking_id == booking.id
        ).first()
        has_review = existing_review is not None
        can_review = not has_review
    
    return {
        'id': booking.id,
        'booking_code': booking.booking_code,
        'status': booking.status,
        'tour_id': tour_id,
        'tour_name': tour_name,
        'tour_photo': tour_photo,
        'schedule_date': schedule_date,
        'schedule_time': schedule_time,
        'participants_count': booking.participants_count,
        'total_price': float(booking.total_price),
        'currency': booking.currency or 'RUB',
        'created_at': booking.created_at,
        'confirmed_at': booking.confirmed_at,
        'paid_at': booking.paid_at,
        'cancelled_at': booking.cancelled_at,
        'can_review': can_review,
        'has_review': has_review
    }


@router.put("/bookings/{booking_id}/cancel")
async def cancel_customer_booking(
    booking_id: int,
    reason: Optional[str] = Query(None, description="Причина отмены"),
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Отменить своё бронирование"""
    
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.customer_id == current_user.id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status in ['cancelled', 'completed']:
        raise HTTPException(status_code=400, detail="Бронирование уже отменено или завершено")
    
    # Отменяем
    from app.services.booking_service import BookingService
    booking, message = BookingService.cancel_booking(
        db=db,
        booking_id=booking.id,
        reason=f"Отмена клиентом: {reason}" if reason else "Отмена клиентом"
    )
    
    return {
        'success': True,
        'message': 'Бронирование отменено',
        'booking_code': booking.booking_code,
        'status': booking.status
    }


# ========== РЕКОМЕНДАЦИИ ==========

@router.get("/recommendations", response_model=List[TourRecommendation])
async def get_recommendations(
    limit: int = Query(6, ge=1, le=20),
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """Получить рекомендованные туры на основе истории бронирований"""
    
    recommendations = []
    added_tour_ids = set()
    
    # 1. Находим типы активностей, которые пользователь бронировал
    user_activity_types = db.query(Activity.activity_type_id).distinct().join(
        TourActivity, TourActivity.activity_id == Activity.id
    ).join(
        TourSchedule, TourSchedule.tour_id == TourActivity.tour_id
    ).join(
        Booking, Booking.tour_schedule_id == TourSchedule.id
    ).filter(
        Booking.customer_id == current_user.id,
        Activity.activity_type_id.isnot(None)
    ).all()
    
    user_activity_type_ids = [at[0] for at in user_activity_types]
    
    # 2. Находим локации, где пользователь бронировал
    from app.models.tour import TourLocation
    
    user_location_ids = db.query(TourLocation.location_id).distinct().join(
        TourSchedule, TourSchedule.tour_id == TourLocation.tour_id
    ).join(
        Booking, Booking.tour_schedule_id == TourSchedule.id
    ).filter(
        Booking.customer_id == current_user.id
    ).all()
    
    user_location_ids = [loc[0] for loc in user_location_ids]
    
    # 3. Туры, которые пользователь уже бронировал (исключаем)
    booked_tour_ids = db.query(Tour.id).distinct().join(
        TourSchedule, TourSchedule.tour_id == Tour.id
    ).join(
        Booking, Booking.tour_schedule_id == TourSchedule.id
    ).filter(
        Booking.customer_id == current_user.id
    ).all()
    
    booked_tour_ids = {t[0] for t in booked_tour_ids}
    
    # 4. Рекомендуем туры по типу активности
    if user_activity_type_ids:
        similar_tours = db.query(Tour).join(
            TourActivity, TourActivity.tour_id == Tour.id
        ).join(
            Activity, Activity.id == TourActivity.activity_id
        ).filter(
            Tour.is_active == True,
            Tour.status == 'active',
            Activity.activity_type_id.in_(user_activity_type_ids),
            Tour.id.notin_(booked_tour_ids)
        ).distinct().limit(limit // 2).all()
        
        for tour in similar_tours:
            if tour.id not in added_tour_ids and len(recommendations) < limit:
                # Получаем локацию
                location = db.query(Location).join(
                    TourLocation, TourLocation.location_id == Location.id
                ).filter(TourLocation.tour_id == tour.id).first()
                
                recommendations.append({
                    'id': tour.id,
                    'name': tour.name,
                    'short_description': tour.short_description,
                    'base_price': float(tour.base_price),
                    'duration_minutes': tour.duration_minutes,
                    'photo': tour.photos[0] if tour.photos else None,
                    'difficulty_level': tour.difficulty_level,
                    'location_name': location.name if location else None,
                    'reason': 'Похожий тип активности'
                })
                added_tour_ids.add(tour.id)
    
    # 5. Рекомендуем туры по локации
    if user_location_ids and len(recommendations) < limit:
        location_tours = db.query(Tour).join(
            TourLocation, TourLocation.tour_id == Tour.id
        ).filter(
            Tour.is_active == True,
            Tour.status == 'active',
            TourLocation.location_id.in_(user_location_ids),
            Tour.id.notin_(booked_tour_ids),
            Tour.id.notin_(added_tour_ids)
        ).distinct().limit(limit - len(recommendations)).all()
        
        for tour in location_tours:
            if tour.id not in added_tour_ids and len(recommendations) < limit:
                location = db.query(Location).join(
                    TourLocation, TourLocation.location_id == Location.id
                ).filter(TourLocation.tour_id == tour.id).first()
                
                recommendations.append({
                    'id': tour.id,
                    'name': tour.name,
                    'short_description': tour.short_description,
                    'base_price': float(tour.base_price),
                    'duration_minutes': tour.duration_minutes,
                    'photo': tour.photos[0] if tour.photos else None,
                    'difficulty_level': tour.difficulty_level,
                    'location_name': location.name if location else None,
                    'reason': 'В знакомой локации'
                })
                added_tour_ids.add(tour.id)
    
    # 6. Если мало рекомендаций — добавляем популярные туры
    if len(recommendations) < limit:
        # Популярные = больше всего бронирований
        popular_tours = db.query(
            Tour,
            func.count(Booking.id).label('bookings_count')
        ).join(
            TourSchedule, TourSchedule.tour_id == Tour.id
        ).outerjoin(
            Booking, Booking.tour_schedule_id == TourSchedule.id
        ).filter(
            Tour.is_active == True,
            Tour.status == 'active',
            Tour.id.notin_(booked_tour_ids),
            Tour.id.notin_(added_tour_ids)
        ).group_by(Tour.id).order_by(
            desc('bookings_count')
        ).limit(limit - len(recommendations)).all()
        
        for tour, _ in popular_tours:
            if tour.id not in added_tour_ids and len(recommendations) < limit:
                location = db.query(Location).join(
                    TourLocation, TourLocation.location_id == Location.id
                ).filter(TourLocation.tour_id == tour.id).first()
                
                recommendations.append({
                    'id': tour.id,
                    'name': tour.name,
                    'short_description': tour.short_description,
                    'base_price': float(tour.base_price),
                    'duration_minutes': tour.duration_minutes,
                    'photo': tour.photos[0] if tour.photos else None,
                    'difficulty_level': tour.difficulty_level,
                    'location_name': location.name if location else None,
                    'reason': 'Популярный тур'
                })
                added_tour_ids.add(tour.id)
    
    return recommendations


# ========== ПРИВЯЗКА БРОНИРОВАНИЙ ==========

@router.post("/link-booking")
async def link_booking_to_account(
    booking_code: str = Query(..., description="Код бронирования"),
    phone: str = Query(..., description="Телефон для верификации"),
    current_user: User = Depends(get_current_customer_user),
    db: Session = Depends(get_db)
):
    """
    Привязать существующее бронирование (сделанное без авторизации) к аккаунту.
    Полезно когда пользователь сначала забронировал, а потом зарегистрировался.
    """
    
    booking = db.query(Booking).filter(
        Booking.booking_code == booking_code.upper()
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    # Проверяем телефон
    clean_phone = ''.join(filter(str.isdigit, phone))
    booking_phone = ''.join(filter(str.isdigit, booking.customer_phone or ''))
    
    if clean_phone[-10:] != booking_phone[-10:]:
        raise HTTPException(status_code=403, detail="Неверный телефон")
    
    # Проверяем, не привязано ли уже к другому аккаунту
    if booking.customer_id and booking.customer_id != current_user.id:
        raise HTTPException(status_code=400, detail="Бронирование уже привязано к другому аккаунту")
    
    # Привязываем
    booking.customer_id = current_user.id
    db.commit()
    
    return {
        'success': True,
        'message': 'Бронирование успешно привязано к вашему аккаунту',
        'booking_code': booking.booking_code
    }
