# app/api/routes/bookings_api.py
"""
API эндпоинты для управления бронированиями (CRM - для бизнеса)
С мультитенантностью — каждый бизнес видит только свои бронирования
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
from typing import Optional, List
from datetime import datetime, date

from app.core.database import get_db
from app.api.deps import get_current_business_user
from app.models.user import User
from app.models.booking import Booking, BookingResource
from app.models.tour import Tour, TourSchedule
from app.models.resource import Resource
from app.schemas.booking_schemas import (
    BookingCreate, BookingCreateCRM, BookingUpdate, BookingStatusUpdate,
    BookingResponse, BookingListResponse, BookingResourceResponse
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/business/bookings", tags=["CRM Bookings"])


def get_business_booking_query(db: Session, business_id: int):
    """Базовый запрос бронирований только для указанного бизнеса"""
    # Получаем ID всех слотов расписания туров этого бизнеса
    business_schedule_ids = db.query(TourSchedule.id).join(Tour).filter(
        Tour.business_id == business_id
    ).subquery()
    
    return db.query(Booking).filter(
        Booking.tour_schedule_id.in_(business_schedule_ids)
    )


def booking_to_response(booking: Booking, db: Session) -> dict:
    """Преобразование модели в response с дополнительными данными"""
    data = {
        'id': booking.id,
        'booking_code': booking.booking_code,
        'booking_type': booking.booking_type,
        'tour_schedule_id': booking.tour_schedule_id,
        'activity_schedule_id': booking.activity_schedule_id,
        'customer_id': booking.customer_id,
        'customer_name': booking.customer_name,
        'customer_phone': booking.customer_phone,
        'customer_email': booking.customer_email,
        'participants_count': booking.participants_count,
        'total_price': booking.total_price,
        'currency': booking.currency or 'RUB',
        'status': booking.status,
        'notes': booking.notes,
        'created_at': booking.created_at,
        'confirmed_at': booking.confirmed_at,
        'paid_at': booking.paid_at,
        'cancelled_at': booking.cancelled_at,
        'booking_resources': []
    }
    
    # Добавляем данные о туре и расписании
    if booking.tour_schedule_id:
        schedule = db.query(TourSchedule).filter(
            TourSchedule.id == booking.tour_schedule_id
        ).first()
        if schedule:
            data['schedule_date'] = str(schedule.date)
            data['schedule_time'] = f"{schedule.start_time} - {schedule.end_time}"
            
            tour = db.query(Tour).filter(Tour.id == schedule.tour_id).first()
            if tour:
                data['tour_name'] = tour.name
    
    # Добавляем ресурсы
    for br in booking.booking_resources:
        resource = db.query(Resource).filter(Resource.id == br.resource_id).first()
        data['booking_resources'].append({
            'id': br.id,
            'resource_id': br.resource_id,
            'resource_name': resource.name if resource else None,
            'quantity': br.quantity,
            'price_per_unit': br.price_per_unit
        })
    
    return data


@router.get("/", response_model=None)
async def get_bookings(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    tour_id: Optional[int] = Query(None, description="Фильтр по туру"),
    date_from: Optional[date] = Query(None, description="Дата от"),
    date_to: Optional[date] = Query(None, description="Дата до"),
    search: Optional[str] = Query(None, description="Поиск по имени/телефону/коду"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получение списка бронирований с фильтрами (только для своего бизнеса)"""
    business_id = current_user.business_profile.id
    
    # Базовый запрос с фильтрацией по бизнесу
    query = get_business_booking_query(db, business_id).options(
        joinedload(Booking.booking_resources)
    )
    
    # Фильтры
    if status:
        query = query.filter(Booking.status == status)
    
    if tour_id:
        # Проверяем что тур принадлежит этому бизнесу
        tour = db.query(Tour).filter(
            Tour.id == tour_id,
            Tour.business_id == business_id
        ).first()
        if not tour:
            raise HTTPException(status_code=404, detail="Тур не найден")
        
        schedule_ids = db.query(TourSchedule.id).filter(
            TourSchedule.tour_id == tour_id
        ).subquery()
        query = query.filter(Booking.tour_schedule_id.in_(schedule_ids))
    
    if date_from:
        query = query.filter(func.date(Booking.created_at) >= date_from)
    
    if date_to:
        query = query.filter(func.date(Booking.created_at) <= date_to)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(or_(
            Booking.booking_code.ilike(search_term),
            Booking.customer_name.ilike(search_term),
            Booking.customer_phone.ilike(search_term),
            Booking.customer_email.ilike(search_term)
        ))
    
    # Подсчёт
    total = query.count()
    
    # Пагинация
    bookings = query.order_by(desc(Booking.created_at)).offset(
        (page - 1) * per_page
    ).limit(per_page).all()
    
    # Формируем ответ
    items = [booking_to_response(b, db) for b in bookings]
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


@router.get("/stats")
async def get_bookings_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Статистика по бронированиям (только для своего бизнеса)"""
    business_id = current_user.business_profile.id
    
    # Базовый запрос с фильтрацией по бизнесу
    query = get_business_booking_query(db, business_id)
    
    if date_from:
        query = query.filter(func.date(Booking.created_at) >= date_from)
    if date_to:
        query = query.filter(func.date(Booking.created_at) <= date_to)
    
    total = query.count()
    pending = query.filter(Booking.status == 'pending').count()
    confirmed = query.filter(Booking.status == 'confirmed').count()
    paid = query.filter(Booking.status == 'paid').count()
    cancelled = query.filter(Booking.status == 'cancelled').count()
    completed = query.filter(Booking.status == 'completed').count()
    
    # Выручка — только для своего бизнеса
    revenue_query = get_business_booking_query(db, business_id).filter(
        Booking.status.in_(['confirmed', 'paid', 'completed'])
    )
    if date_from:
        revenue_query = revenue_query.filter(func.date(Booking.created_at) >= date_from)
    if date_to:
        revenue_query = revenue_query.filter(func.date(Booking.created_at) <= date_to)
    
    # Получаем суммы
    total_revenue = db.query(func.sum(Booking.total_price)).filter(
        Booking.id.in_(revenue_query.with_entities(Booking.id))
    ).scalar() or 0
    
    total_participants = db.query(func.sum(Booking.participants_count)).filter(
        Booking.id.in_(revenue_query.with_entities(Booking.id))
    ).scalar() or 0
    
    return {
        'total': total,
        'by_status': {
            'pending': pending,
            'confirmed': confirmed,
            'paid': paid,
            'cancelled': cancelled,
            'completed': completed
        },
        'total_revenue': float(total_revenue),
        'total_participants': total_participants
    }


@router.get("/{booking_id}")
async def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получение деталей бронирования (только если принадлежит бизнесу)"""
    business_id = current_user.business_profile.id
    
    # Проверяем что бронирование принадлежит этому бизнесу
    booking = get_business_booking_query(db, business_id).options(
        joinedload(Booking.booking_resources)
    ).filter(Booking.id == booking_id).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    return booking_to_response(booking, db)


@router.post("/")
async def create_booking(
    data: BookingCreateCRM,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создание бронирования из CRM (проверка что тур принадлежит бизнесу)"""
    business_id = current_user.business_profile.id
    
    # Проверяем что расписание принадлежит туру этого бизнеса
    schedule = db.query(TourSchedule).join(Tour).filter(
        TourSchedule.id == data.tour_schedule_id,
        Tour.business_id == business_id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Слот расписания не найден")
    
    booking, message = BookingService.create_booking(
        db=db,
        tour_schedule_id=data.tour_schedule_id,
        participants_count=data.participants_count,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        customer_id=data.customer_id,
        notes=data.notes,
        status=data.status or 'pending'
    )
    
    if not booking:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        'message': message,
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}")
async def update_booking(
    booking_id: int,
    data: BookingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновление бронирования (только если принадлежит бизнесу)"""
    business_id = current_user.business_profile.id
    
    # Проверяем что бронирование принадлежит этому бизнесу
    booking = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    # Обновляем поля
    update_data = data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(booking, field) and value is not None:
            setattr(booking, field, value)
    
    db.commit()
    db.refresh(booking)
    
    return {
        'message': 'Бронирование обновлено',
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}/status")
async def update_booking_status(
    booking_id: int,
    data: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Изменение статуса бронирования (только если принадлежит бизнесу)"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    booking = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking, message = BookingService.update_status(
        db=db,
        booking_id=booking_id,
        new_status=data.status,
        notes=data.notes
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail=message)
    
    return {
        'message': message,
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}/confirm")
async def confirm_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Подтверждение бронирования"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    existing = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking, message = BookingService.update_status(
        db=db,
        booking_id=booking_id,
        new_status='confirmed'
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail=message)
    
    return {
        'message': 'Бронирование подтверждено',
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}/paid")
async def mark_booking_paid(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Отметка об оплате"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    existing = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking, message = BookingService.update_status(
        db=db,
        booking_id=booking_id,
        new_status='paid'
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail=message)
    
    return {
        'message': 'Оплата зафиксирована',
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}/completed")
async def mark_booking_completed(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Отметка о завершении тура"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    existing = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking, message = BookingService.update_status(
        db=db,
        booking_id=booking_id,
        new_status='completed'
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail=message)
    
    return {
        'message': 'Тур завершён',
        'booking': booking_to_response(booking, db)
    }


@router.put("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    reason: Optional[str] = Query(None, description="Причина отмены"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Отмена бронирования"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    existing = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not existing:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    booking, message = BookingService.cancel_booking(
        db=db,
        booking_id=booking_id,
        reason=reason
    )
    
    if not booking:
        raise HTTPException(status_code=404, detail=message)
    
    return {
        'message': 'Бронирование отменено',
        'booking': booking_to_response(booking, db)
    }


@router.delete("/{booking_id}")
async def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удаление бронирования (только для cancelled или pending)"""
    business_id = current_user.business_profile.id
    
    # Проверяем принадлежность
    booking = get_business_booking_query(db, business_id).filter(
        Booking.id == booking_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    if booking.status not in ['cancelled', 'pending']:
        raise HTTPException(
            status_code=400, 
            detail="Можно удалить только отменённые или ожидающие бронирования"
        )
    
    db.delete(booking)
    db.commit()
    
    return {'message': 'Бронирование удалено'}
