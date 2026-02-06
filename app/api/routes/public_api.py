# app/api/routes/public_api.py
"""
Публичный API для клиентов - бронирование туров без авторизации
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional, List
from datetime import date, datetime

from app.core.database import get_db
from app.models.tour import Tour, TourSchedule, TourResource, TourLocation, TourActivity
from app.models.resource import Resource
from app.models.activity import Location, Activity, ActivityType
from app.models.booking import Booking
from app.schemas.booking_schemas import (
    BookingCreate, BookingConfirmation, PublicTourResponse, 
    PublicScheduleResponse, BookingCalculation
)
from app.services.booking_service import BookingService

router = APIRouter(prefix="/public", tags=["Public API"])


# ========== СПРАВОЧНИКИ ДЛЯ ФИЛЬТРОВ ==========

@router.get("/activity-types")
async def get_activity_types(
    db: Session = Depends(get_db)
):
    """Получить все типы активностей для фильтров"""
    activity_types = db.query(ActivityType).filter(
        ActivityType.is_active == True
    ).order_by(ActivityType.name).all()
    
    result = []
    for at in activity_types:
        # Считаем количество активных туров для этого типа
        tours_count = db.query(func.count(func.distinct(Tour.id))).join(
            TourActivity, TourActivity.tour_id == Tour.id
        ).join(
            Activity, Activity.id == TourActivity.activity_id
        ).filter(
            Activity.activity_type_id == at.id,
            Tour.is_active == True,
            Tour.status == 'active'
        ).scalar() or 0
        
        result.append({
            'id': at.id,
            'name': at.name,
            'category': at.category,
            'icon': at.icon,
            'tours_count': tours_count
        })
    
    # Сортируем: сначала с турами, потом по имени
    result.sort(key=lambda x: (-x['tours_count'], x['name']))
    
    return result


@router.get("/locations")
async def get_locations(
    db: Session = Depends(get_db)
):
    """Получить все локации для фильтров"""
    locations = db.query(Location).filter(
        Location.is_active == True
    ).order_by(Location.name).all()
    
    result = []
    for loc in locations:
        tours_count = db.query(func.count(func.distinct(Tour.id))).join(
            TourLocation, TourLocation.tour_id == Tour.id
        ).filter(
            TourLocation.location_id == loc.id,
            Tour.is_active == True,
            Tour.status == 'active'
        ).scalar() or 0
        
        if tours_count > 0:
            result.append({
                'id': loc.id,
                'name': loc.name,
                'city': loc.city,
                'region': loc.region,
                'latitude': float(loc.latitude) if loc.latitude else None,
                'longitude': float(loc.longitude) if loc.longitude else None,
                'tours_count': tours_count
            })
    
    return result


# ========== ТУРЫ ==========

@router.get("/tours")
async def get_public_tours(
    activity_type_id: Optional[int] = Query(None, description="Фильтр по типу активности"),
    location_id: Optional[int] = Query(None, description="Фильтр по локации"),
    min_price: Optional[float] = Query(None, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, description="Максимальная цена"),
    db: Session = Depends(get_db)
):
    """Список доступных туров для клиентов"""
    query = db.query(Tour).filter(
        Tour.is_active == True,
        Tour.status == 'active'
    )
    
    if min_price:
        query = query.filter(Tour.base_price >= min_price)
    if max_price:
        query = query.filter(Tour.base_price <= max_price)
    
    tours = query.order_by(Tour.name).all()
    
    result = []
    for tour in tours:
        # Проверяем есть ли доступные слоты
        has_slots = db.query(TourSchedule).filter(
            TourSchedule.tour_id == tour.id,
            TourSchedule.date >= date.today(),
            TourSchedule.status == 'available'
        ).first() is not None
        
        if not has_slots:
            continue
        
        # Получаем локации
        locations = db.query(Location).join(TourLocation).filter(
            TourLocation.tour_id == tour.id
        ).all()
        
        # Фильтр по локации
        if location_id:
            if not any(l.id == location_id for l in locations):
                continue
        
        # Получаем активности и activity_type_id
        tour_activity_type_id = None
        activities_list = []
        
        tour_activities = db.query(TourActivity).filter(
            TourActivity.tour_id == tour.id
        ).all()
        
        for ta in tour_activities:
            activity = db.query(Activity).filter(Activity.id == ta.activity_id).first()
            if activity:
                activities_list.append({
                    'id': activity.id,
                    'name': activity.name,
                    'activity_type_id': activity.activity_type_id
                })
                if tour_activity_type_id is None and activity.activity_type_id:
                    tour_activity_type_id = activity.activity_type_id
        
        # Фильтр по типу активности
        if activity_type_id:
            if tour_activity_type_id != activity_type_id:
                continue
        
        result.append({
            'id': tour.id,
            'name': tour.name,
            'description': tour.description,
            'short_description': tour.short_description,
            'base_price': float(tour.base_price),
            'currency': tour.currency or 'RUB',
            'duration_minutes': tour.duration_minutes,
            'min_participants': tour.min_participants or 1,
            'max_participants': tour.max_participants,
            'photos': tour.photos or [],
            'difficulty_level': tour.difficulty_level,
            'what_included': tour.what_included or [],
            'activity_type_id': tour_activity_type_id,
            'activities': activities_list,
            'locations': [{
                'id': l.id, 
                'name': l.name, 
                'latitude': float(l.latitude) if l.latitude else None, 
                'longitude': float(l.longitude) if l.longitude else None, 
                'address': l.address, 
                'city': l.city, 
                'region': l.region
            } for l in locations]
        })
    
    return result


@router.get("/tours/{tour_id}")
async def get_public_tour(
    tour_id: int,
    db: Session = Depends(get_db)
):
    """Детальная информация о туре"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.is_active == True
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Ресурсы
    tour_resources = db.query(TourResource).filter(
        TourResource.tour_id == tour_id
    ).all()
    
    resources = []
    for tr in tour_resources:
        resource = db.query(Resource).filter(Resource.id == tr.resource_id).first()
        if resource:
            resources.append({
                'name': resource.name,
                'type': resource.resource_type,
                'quantity': tr.quantity_needed,
                'seats_per_unit': resource.seats_per_unit or 1
            })
    
    # Локации
    locations = db.query(Location).join(TourLocation).filter(
        TourLocation.tour_id == tour_id
    ).all()
    
    # Активности
    activities = []
    activity_type_id = None
    
    tour_activities = db.query(TourActivity).filter(
        TourActivity.tour_id == tour_id
    ).all()
    
    for ta in tour_activities:
        activity = db.query(Activity).filter(Activity.id == ta.activity_id).first()
        if activity:
            activities.append({
                'id': activity.id,
                'name': activity.name,
                'activity_type_id': activity.activity_type_id
            })
            if activity_type_id is None and activity.activity_type_id:
                activity_type_id = activity.activity_type_id
    
    return {
        'id': tour.id,
        'name': tour.name,
        'description': tour.description,
        'short_description': tour.short_description,
        'base_price': float(tour.base_price),
        'currency': tour.currency or 'RUB',
        'duration_minutes': tour.duration_minutes,
        'min_participants': tour.min_participants or 1,
        'max_participants': tour.max_participants,
        'min_age': tour.min_age,
        'difficulty_level': tour.difficulty_level,
        'photos': tour.photos or [],
        'what_included': tour.what_included or [],
        'what_to_bring': tour.what_to_bring or [],
        'activity_type_id': activity_type_id,
        'activities': activities,
        'resources': resources,
        'locations': [{
            'id': l.id, 
            'name': l.name, 
            'address': l.address,
            'latitude': float(l.latitude) if l.latitude else None,
            'longitude': float(l.longitude) if l.longitude else None,
            'city': l.city,
            'region': l.region
        } for l in locations]
    }


# ========== РАСПИСАНИЕ ==========

@router.get("/tours/{tour_id}/schedules")
async def get_tour_schedules(
    tour_id: int,
    date_from: Optional[date] = Query(None, description="Дата от"),
    date_to: Optional[date] = Query(None, description="Дата до"),
    db: Session = Depends(get_db)
):
    """Доступные слоты расписания тура"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.is_active == True
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    query = db.query(TourSchedule).filter(
        TourSchedule.tour_id == tour_id,
        TourSchedule.date >= (date_from or date.today())
    )
    
    if date_to:
        query = query.filter(TourSchedule.date <= date_to)
    
    schedules = query.order_by(TourSchedule.date, TourSchedule.start_time).all()
    
    result = []
    for schedule in schedules:
        booked = db.query(func.coalesce(func.sum(Booking.participants_count), 0)).filter(
            Booking.tour_schedule_id == schedule.id,
            Booking.status.in_(['pending', 'confirmed', 'paid'])
        ).scalar() or 0
        
        available = schedule.available_slots
        free = available - booked
        
        if free <= 0:
            status = 'fully_booked'
        elif booked > 0:
            status = 'partially_booked'
        else:
            status = 'available'
        
        result.append({
            'id': schedule.id,
            'date': str(schedule.date),
            'start_time': str(schedule.start_time),
            'end_time': str(schedule.end_time),
            'available_slots': available,
            'booked_slots': booked,
            'free_slots': max(0, free),
            'status': status,
            'price_per_person': float(tour.base_price)
        })
    
    return result


# ========== РАСЧЁТ СТОИМОСТИ ==========

@router.post("/calculate")
async def calculate_booking(
    tour_id: int,
    schedule_id: int,
    participants_count: int = Query(..., ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Расчёт стоимости бронирования"""
    tour = db.query(Tour).filter(Tour.id == tour_id).first()
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    if tour.min_participants and participants_count < tour.min_participants:
        raise HTTPException(status_code=400, detail=f"Минимум участников: {tour.min_participants}")
    if tour.max_participants and participants_count > tour.max_participants:
        raise HTTPException(status_code=400, detail=f"Максимум участников: {tour.max_participants}")
    
    available, message, free_slots = BookingService.check_availability(db, schedule_id, participants_count)
    total_price, resources_needed = BookingService.calculate_price(db, tour_id, schedule_id, participants_count)
    
    return {
        'tour_id': tour_id,
        'tour_name': tour.name,
        'schedule_id': schedule_id,
        'participants_count': participants_count,
        'base_price': float(tour.base_price),
        'total_price': total_price,
        'resources_needed': resources_needed,
        'available': available,
        'free_slots': free_slots,
        'message': message if not available else 'Доступно для бронирования'
    }


# ========== БРОНИРОВАНИЕ ==========

@router.post("/bookings")
async def create_public_booking(
    data: BookingCreate,
    db: Session = Depends(get_db)
):
    """Создание бронирования (публичный API)"""
    schedule = db.query(TourSchedule).filter(TourSchedule.id == data.tour_schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Слот не найден")
    
    tour = db.query(Tour).filter(Tour.id == schedule.tour_id, Tour.is_active == True).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур недоступен")
    
    if tour.min_participants and data.participants_count < tour.min_participants:
        raise HTTPException(status_code=400, detail=f"Минимум участников: {tour.min_participants}")
    if tour.max_participants and data.participants_count > tour.max_participants:
        raise HTTPException(status_code=400, detail=f"Максимум участников: {tour.max_participants}")
    
    booking, message = BookingService.create_booking(
        db=db,
        tour_schedule_id=data.tour_schedule_id,
        participants_count=data.participants_count,
        customer_name=data.customer_name,
        customer_phone=data.customer_phone,
        customer_email=data.customer_email,
        notes=data.notes,
        status='pending'
    )
    
    if not booking:
        raise HTTPException(status_code=400, detail=message)
    
    return {
        'success': True,
        'message': 'Бронирование создано! Ожидайте подтверждения.',
        'booking': {
            'booking_code': booking.booking_code,
            'status': booking.status,
            'tour_name': tour.name,
            'schedule_date': str(schedule.date),
            'schedule_time': f"{schedule.start_time} - {schedule.end_time}",
            'participants_count': booking.participants_count,
            'total_price': float(booking.total_price),
            'customer_name': booking.customer_name,
            'customer_phone': booking.customer_phone
        }
    }


@router.get("/bookings/{booking_code}")
async def get_booking_by_code(
    booking_code: str,
    phone: str = Query(..., description="Телефон для верификации"),
    db: Session = Depends(get_db)
):
    """Проверка статуса бронирования по коду"""
    booking = db.query(Booking).filter(Booking.booking_code == booking_code.upper()).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    clean_phone = ''.join(filter(str.isdigit, phone))
    booking_phone = ''.join(filter(str.isdigit, booking.customer_phone or ''))
    
    if clean_phone[-10:] != booking_phone[-10:]:
        raise HTTPException(status_code=403, detail="Неверный телефон")
    
    tour_name = None
    schedule_date = None
    schedule_time = None
    
    if booking.tour_schedule_id:
        schedule = db.query(TourSchedule).filter(TourSchedule.id == booking.tour_schedule_id).first()
        if schedule:
            schedule_date = str(schedule.date)
            schedule_time = f"{schedule.start_time} - {schedule.end_time}"
            tour = db.query(Tour).filter(Tour.id == schedule.tour_id).first()
            if tour:
                tour_name = tour.name
    
    return {
        'booking_code': booking.booking_code,
        'status': booking.status,
        'tour_name': tour_name,
        'schedule_date': schedule_date,
        'schedule_time': schedule_time,
        'participants_count': booking.participants_count,
        'total_price': float(booking.total_price),
        'customer_name': booking.customer_name,
        'created_at': booking.created_at,
        'confirmed_at': booking.confirmed_at,
        'paid_at': booking.paid_at
    }


@router.put("/bookings/{booking_code}/cancel")
async def cancel_public_booking(
    booking_code: str,
    phone: str = Query(..., description="Телефон для верификации"),
    reason: Optional[str] = Query(None, description="Причина отмены"),
    db: Session = Depends(get_db)
):
    """Отмена бронирования клиентом"""
    booking = db.query(Booking).filter(Booking.booking_code == booking_code.upper()).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    
    clean_phone = ''.join(filter(str.isdigit, phone))
    booking_phone = ''.join(filter(str.isdigit, booking.customer_phone or ''))
    
    if clean_phone[-10:] != booking_phone[-10:]:
        raise HTTPException(status_code=403, detail="Неверный телефон")
    
    if booking.status in ['cancelled', 'completed']:
        raise HTTPException(status_code=400, detail="Бронирование уже отменено или завершено")
    
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
