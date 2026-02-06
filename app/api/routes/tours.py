from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import List, Optional
from datetime import date, time, timedelta, datetime
from app.core.database import get_db
from app.api.deps import get_current_business_user
from app.models.user import User
from app.models.tour import Tour, TourActivity, TourResource, TourInstructor, TourLocation, TourSchedule
from app.models.activity import Activity, ActivityType, Location
from app.models.resource import Resource, ResourceType, Instructor, ScheduleResource, ActivityResourceType
from app.schemas.tour import (
    TourCreate, TourUpdate, TourResponse,
    TourActivityCreate, TourActivityResponse,
    TourResourceCreate, TourResourceResponse,
    TourInstructorCreate, TourInstructorResponse,
    TourLocationCreate, TourLocationResponse,
    TourScheduleCreate, TourScheduleUpdate, TourScheduleResponse,
    ScheduleResourceCreate, ScheduleResourceResponse
)

router = APIRouter(prefix="/business", tags=["Туры"])


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def get_tour_response(tour, db) -> TourResponse:
    """Формируем полный ответ тура со всеми связями"""
    tour_data = TourResponse.model_validate(tour)
    
    tour_data.activities = [
        TourActivityResponse(
            id=ta.id,
            tour_id=ta.tour_id,
            activity_id=ta.activity_id,
            order_index=ta.order_index,
            duration_minutes=ta.duration_minutes,
            notes=ta.notes,
            activity_name=ta.activity.name if ta.activity else None
        ) for ta in tour.tour_activities
    ]
    
    tour_data.resources = [
        TourResourceResponse(
            id=tr.id,
            tour_id=tr.tour_id,
            resource_id=tr.resource_id,
            quantity_needed=tr.quantity_needed,
            resource_name=tr.resource.name if tr.resource else None,
            resource_type=tr.resource.resource_type if tr.resource else None,
            available_quantity=tr.resource.quantity if tr.resource else None
        ) for tr in tour.tour_resources
    ]
    
    tour_data.instructors = [
        TourInstructorResponse(
            id=ti.id,
            tour_id=ti.tour_id,
            instructor_id=ti.instructor_id,
            is_lead=ti.is_lead,
            instructor_name=ti.instructor.full_name if ti.instructor else None
        ) for ti in tour.tour_instructors
    ]
    
    tour_data.locations = [
        TourLocationResponse(
            id=tl.id,
            tour_id=tl.tour_id,
            location_id=tl.location_id,
            is_meeting_point=tl.is_meeting_point,
            is_activity_point=tl.is_activity_point,
            notes=tl.notes,
            location_name=tl.location.name if tl.location else None,
            location_address=tl.location.address if tl.location else None
        ) for tl in tour.tour_locations
    ]
    
    return tour_data


# === TOURS ===

@router.get("/tours", response_model=List[TourResponse])
async def get_tours(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить все туры бизнеса"""
    tours = db.query(Tour).filter(
        Tour.business_id == current_user.business_profile.id
    ).options(
        joinedload(Tour.tour_activities).joinedload(TourActivity.activity),
        joinedload(Tour.tour_resources).joinedload(TourResource.resource),
        joinedload(Tour.tour_instructors).joinedload(TourInstructor.instructor),
        joinedload(Tour.tour_locations).joinedload(TourLocation.location)
    ).order_by(Tour.created_at.desc()).all()
    
    return [get_tour_response(tour, db) for tour in tours]


@router.post("/tours", response_model=TourResponse)
async def create_tour(
    data: TourCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать тур"""
    business_id = current_user.business_profile.id
    
    # Валидация ресурсов — проверяем что не указано больше чем есть
    if data.resources:
        for res_data in data.resources:
            resource = db.query(Resource).filter(
                Resource.id == res_data.resource_id,
                Resource.business_id == business_id
            ).first()
            if not resource:
                raise HTTPException(status_code=404, detail=f"Ресурс {res_data.resource_id} не найден")
            if res_data.quantity_needed > resource.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Недостаточно ресурса '{resource.name}': запрошено {res_data.quantity_needed}, доступно {resource.quantity}"
                )
    
    # Создаём тур
    tour_fields = data.model_dump(exclude={'activities', 'resources', 'locations'})
    tour = Tour(business_id=business_id, **tour_fields)
    db.add(tour)
    db.flush()
    
    # Добавляем активности
    if data.activities:
        for act_data in data.activities:
            db.add(TourActivity(tour_id=tour.id, **act_data.model_dump()))
    
    # Добавляем ресурсы
    if data.resources:
        for res_data in data.resources:
            db.add(TourResource(tour_id=tour.id, **res_data.model_dump()))
    
    # Добавляем локации
    if data.locations:
        for loc_data in data.locations:
            db.add(TourLocation(tour_id=tour.id, **loc_data.model_dump()))
    
    try:
        db.commit()
        db.refresh(tour)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания тура: {str(e)}")
    
    # Загружаем со связями
    tour = db.query(Tour).options(
        joinedload(Tour.tour_activities).joinedload(TourActivity.activity),
        joinedload(Tour.tour_resources).joinedload(TourResource.resource),
        joinedload(Tour.tour_instructors).joinedload(TourInstructor.instructor),
        joinedload(Tour.tour_locations).joinedload(TourLocation.location)
    ).filter(Tour.id == tour.id).first()
    
    return get_tour_response(tour, db)


@router.get("/tours/{tour_id}", response_model=TourResponse)
async def get_tour(
    tour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить тур по ID"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).options(
        joinedload(Tour.tour_activities).joinedload(TourActivity.activity),
        joinedload(Tour.tour_resources).joinedload(TourResource.resource),
        joinedload(Tour.tour_instructors).joinedload(TourInstructor.instructor),
        joinedload(Tour.tour_locations).joinedload(TourLocation.location)
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    return get_tour_response(tour, db)


@router.put("/tours/{tour_id}", response_model=TourResponse)
async def update_tour(
    tour_id: int,
    data: TourCreate,  # Используем TourCreate чтобы получить activities, resources, locations
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить тур (включая связи: активности, ресурсы, локации)"""
    business_id = current_user.business_profile.id
    
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == business_id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Валидация ресурсов
    if data.resources:
        for res_data in data.resources:
            resource = db.query(Resource).filter(
                Resource.id == res_data.resource_id,
                Resource.business_id == business_id
            ).first()
            if not resource:
                raise HTTPException(status_code=404, detail=f"Ресурс {res_data.resource_id} не найден")
            if res_data.quantity_needed > resource.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Недостаточно ресурса '{resource.name}': запрошено {res_data.quantity_needed}, доступно {resource.quantity}"
                )
    
    # Обновляем простые поля тура
    simple_fields = data.model_dump(exclude={'activities', 'resources', 'locations'}, exclude_unset=True)
    for field, value in simple_fields.items():
        if value is not None:
            setattr(tour, field, value)
    
    # === ОБНОВЛЯЕМ АКТИВНОСТИ ===
    if data.activities is not None:
        # Удаляем старые
        db.query(TourActivity).filter(TourActivity.tour_id == tour_id).delete()
        # Добавляем новые
        for act_data in data.activities:
            db.add(TourActivity(tour_id=tour_id, **act_data.model_dump()))
    
    # === ОБНОВЛЯЕМ РЕСУРСЫ ===
    if data.resources is not None:
        # Удаляем старые
        db.query(TourResource).filter(TourResource.tour_id == tour_id).delete()
        # Добавляем новые
        for res_data in data.resources:
            db.add(TourResource(tour_id=tour_id, **res_data.model_dump()))
    
    # === ОБНОВЛЯЕМ ЛОКАЦИИ ===
    if data.locations is not None:
        # Удаляем старые
        db.query(TourLocation).filter(TourLocation.tour_id == tour_id).delete()
        # Добавляем новые
        for loc_data in data.locations:
            db.add(TourLocation(tour_id=tour_id, **loc_data.model_dump()))
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления тура: {str(e)}")
    
    # Загружаем со связями
    tour = db.query(Tour).options(
        joinedload(Tour.tour_activities).joinedload(TourActivity.activity),
        joinedload(Tour.tour_resources).joinedload(TourResource.resource),
        joinedload(Tour.tour_instructors).joinedload(TourInstructor.instructor),
        joinedload(Tour.tour_locations).joinedload(TourLocation.location)
    ).filter(Tour.id == tour_id).first()
    
    return get_tour_response(tour, db)


@router.delete("/tours/{tour_id}")
async def delete_tour(
    tour_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить тур"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    db.delete(tour)
    db.commit()
    return {"message": "Тур удалён"}


# === TOUR ACTIVITIES ===

@router.post("/tours/{tour_id}/activities", response_model=TourActivityResponse)
async def add_tour_activity(
    tour_id: int,
    data: TourActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Добавить активность к туру"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    activity = db.query(Activity).filter(Activity.id == data.activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    tour_activity = TourActivity(tour_id=tour_id, **data.model_dump())
    db.add(tour_activity)
    db.commit()
    db.refresh(tour_activity)
    
    return TourActivityResponse(
        id=tour_activity.id,
        tour_id=tour_activity.tour_id,
        activity_id=tour_activity.activity_id,
        order_index=tour_activity.order_index,
        duration_minutes=tour_activity.duration_minutes,
        notes=tour_activity.notes,
        activity_name=activity.name
    )


@router.delete("/tours/{tour_id}/activities/{activity_id}")
async def remove_tour_activity(
    tour_id: int,
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить активность из тура"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    tour_activity = db.query(TourActivity).filter(
        TourActivity.tour_id == tour_id,
        TourActivity.activity_id == activity_id
    ).first()
    
    if not tour_activity:
        raise HTTPException(status_code=404, detail="Активность не привязана к туру")
    
    db.delete(tour_activity)
    db.commit()
    return {"message": "Активность удалена из тура"}


# === TOUR RESOURCES ===

@router.post("/tours/{tour_id}/resources", response_model=TourResourceResponse)
async def add_tour_resource(
    tour_id: int,
    data: TourResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Добавить ресурс к туру"""
    business_id = current_user.business_profile.id
    
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == business_id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    resource = db.query(Resource).filter(
        Resource.id == data.resource_id,
        Resource.business_id == business_id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    
    if data.quantity_needed > resource.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Запрошено {data.quantity_needed}, доступно {resource.quantity}"
        )
    
    tour_resource = TourResource(tour_id=tour_id, **data.model_dump())
    db.add(tour_resource)
    db.commit()
    db.refresh(tour_resource)
    
    return TourResourceResponse(
        id=tour_resource.id,
        tour_id=tour_resource.tour_id,
        resource_id=tour_resource.resource_id,
        quantity_needed=tour_resource.quantity_needed,
        resource_name=resource.name,
        resource_type=resource.resource_type,
        available_quantity=resource.quantity
    )


@router.delete("/tours/{tour_id}/resources/{resource_id}")
async def remove_tour_resource(
    tour_id: int,
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить ресурс из тура"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    tour_resource = db.query(TourResource).filter(
        TourResource.tour_id == tour_id,
        TourResource.resource_id == resource_id
    ).first()
    
    if not tour_resource:
        raise HTTPException(status_code=404, detail="Ресурс не привязан к туру")
    
    db.delete(tour_resource)
    db.commit()
    return {"message": "Ресурс удалён из тура"}


# === TOUR LOCATIONS ===

@router.post("/tours/{tour_id}/locations", response_model=TourLocationResponse)
async def add_tour_location(
    tour_id: int,
    data: TourLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Добавить локацию к туру"""
    business_id = current_user.business_profile.id
    
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == business_id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    location = db.query(Location).filter(
        Location.id == data.location_id,
        Location.business_id == business_id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    
    tour_location = TourLocation(tour_id=tour_id, **data.model_dump())
    db.add(tour_location)
    db.commit()
    db.refresh(tour_location)
    
    return TourLocationResponse(
        id=tour_location.id,
        tour_id=tour_location.tour_id,
        location_id=tour_location.location_id,
        is_meeting_point=tour_location.is_meeting_point,
        is_activity_point=tour_location.is_activity_point,
        notes=tour_location.notes,
        location_name=location.name,
        location_address=location.address
    )


@router.delete("/tours/{tour_id}/locations/{location_id}")
async def remove_tour_location(
    tour_id: int,
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить локацию из тура"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    tour_location = db.query(TourLocation).filter(
        TourLocation.tour_id == tour_id,
        TourLocation.location_id == location_id
    ).first()
    
    if not tour_location:
        raise HTTPException(status_code=404, detail="Локация не привязана к туру")
    
    db.delete(tour_location)
    db.commit()
    return {"message": "Локация удалена из тура"}


# === TOUR SCHEDULES ===

@router.get("/tours/{tour_id}/schedules", response_model=List[TourScheduleResponse])
async def get_tour_schedules(
    tour_id: int,
    from_date: date = None,
    to_date: date = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить расписание тура"""
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    query = db.query(TourSchedule).filter(TourSchedule.tour_id == tour_id)
    
    if from_date:
        query = query.filter(TourSchedule.date >= from_date)
    if to_date:
        query = query.filter(TourSchedule.date <= to_date)
    
    schedules = query.options(
        joinedload(TourSchedule.instructor),
        joinedload(TourSchedule.schedule_resources).joinedload(ScheduleResource.resource)
    ).order_by(TourSchedule.date, TourSchedule.start_time).all()
    
    result = []
    for s in schedules:
        schedule_data = TourScheduleResponse.model_validate(s)
        schedule_data.free_slots = s.available_slots - s.booked_slots
        schedule_data.tour_name = tour.name
        if s.instructor:
            schedule_data.instructor_name = s.instructor.full_name
        schedule_data.schedule_resources = [
            ScheduleResourceResponse(
                id=sr.id,
                tour_schedule_id=sr.tour_schedule_id,
                resource_id=sr.resource_id,
                quantity_used=sr.quantity_used,
                resource_name=sr.resource.name if sr.resource else None
            ) for sr in s.schedule_resources
        ]
        result.append(schedule_data)
    
    return result


@router.post("/tours/{tour_id}/schedules", response_model=TourScheduleResponse)
async def create_tour_schedule(
    tour_id: int,
    data: TourScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать слот в расписании с проверкой доступности ресурсов"""
    business_id = current_user.business_profile.id
    
    tour = db.query(Tour).filter(
        Tour.id == tour_id,
        Tour.business_id == business_id
    ).options(
        joinedload(Tour.tour_resources).joinedload(TourResource.resource)
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Проверяем доступность ресурсов на это время
    # Получаем все слоты на эту дату которые пересекаются по времени
    conflicting_schedules = db.query(TourSchedule).join(Tour).filter(
        Tour.business_id == business_id,
        TourSchedule.date == data.date,
        TourSchedule.status != 'cancelled'
    ).all()
    
    # Считаем занятые ресурсы
    for tr in tour.tour_resources:
        resource = tr.resource
        needed = tr.quantity_needed
        
        # Считаем сколько уже занято
        used = 0
        for sched in conflicting_schedules:
            # Проверяем пересечение времени
            if data.end_time:
                # Есть время окончания — проверяем пересечение
                sched_end = sched.end_time or (
                    # Если нет end_time — считаем что слот 2 часа
                    (datetime.combine(date.today(), sched.start_time) + timedelta(hours=2)).time()
                )
                if not (data.end_time <= sched.start_time or data.start_time >= sched_end):
                    # Пересекаются — считаем занятые ресурсы
                    for sr in sched.schedule_resources:
                        if sr.resource_id == resource.id:
                            used += sr.quantity_used
        
        available = resource.quantity - used
        if needed > available:
            raise HTTPException(
                status_code=400,
                detail=f"Недостаточно ресурса '{resource.name}' на {data.date} {data.start_time}: нужно {needed}, доступно {available}"
            )
    
    # Создаём слот
    schedule = TourSchedule(
        tour_id=tour_id,
        instructor_id=data.instructor_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        available_slots=data.available_slots,
        price_override=data.price_override,
        notes=data.notes
    )
    db.add(schedule)
    db.flush()
    
    # Добавляем занятость ресурсов
    for tr in tour.tour_resources:
        db.add(ScheduleResource(
            tour_schedule_id=schedule.id,
            resource_id=tr.resource_id,
            quantity_used=tr.quantity_needed
        ))
    
    db.commit()
    db.refresh(schedule)
    
    response = TourScheduleResponse.model_validate(schedule)
    response.free_slots = schedule.available_slots - schedule.booked_slots
    response.tour_name = tour.name
    
    return response


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить слот расписания"""
    schedule = db.query(TourSchedule).join(Tour).filter(
        TourSchedule.id == schedule_id,
        Tour.business_id == current_user.business_profile.id
    ).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Слот не найден")
    
    if schedule.booked_slots > 0:
        raise HTTPException(status_code=400, detail="Нельзя удалить слот с бронированиями")
    
    db.delete(schedule)
    db.commit()
    return {"message": "Слот удалён"}


# === CALENDAR ===

@router.get("/calendar")
async def get_calendar(
    from_date: date = None,
    to_date: date = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить календарь всех туров на период"""
    if not from_date:
        from_date = date.today()
    if not to_date:
        to_date = from_date + timedelta(days=30)
    
    schedules = db.query(TourSchedule).join(Tour).filter(
        Tour.business_id == current_user.business_profile.id,
        TourSchedule.date >= from_date,
        TourSchedule.date <= to_date
    ).options(
        joinedload(TourSchedule.tour),
        joinedload(TourSchedule.instructor),
        joinedload(TourSchedule.schedule_resources).joinedload(ScheduleResource.resource)
    ).order_by(TourSchedule.date, TourSchedule.start_time).all()
    
    calendar = {}
    for s in schedules:
        date_str = s.date.isoformat()
        if date_str not in calendar:
            calendar[date_str] = []
        
        calendar[date_str].append({
            "id": s.id,
            "tour_id": s.tour_id,
            "tour_name": s.tour.name if s.tour else None,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "available_slots": s.available_slots,
            "booked_slots": s.booked_slots,
            "free_slots": s.available_slots - s.booked_slots,
            "status": s.status,
            "instructor_name": s.instructor.full_name if s.instructor else None,
            "price": float(s.price_override) if s.price_override else float(s.tour.base_price) if s.tour else None,
            "resources": [{
                "id": sr.resource_id,
                "name": sr.resource.name if sr.resource else None,
                "quantity_used": sr.quantity_used
            } for sr in s.schedule_resources]
        })
    
    return {
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
        "calendar": calendar
    }


# === RESOURCE AVAILABILITY ===

@router.get("/resources/availability")
async def check_resource_availability(
    resource_id: int,
    check_date: date,
    start_time: time,
    end_time: time = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Проверить доступность ресурса на дату/время"""
    business_id = current_user.business_profile.id
    
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.business_id == business_id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    
    # Считаем занятость на это время
    used = db.query(
        func.coalesce(func.sum(ScheduleResource.quantity_used), 0)
    ).join(TourSchedule).join(Tour).filter(
        Tour.business_id == business_id,
        ScheduleResource.resource_id == resource_id,
        TourSchedule.date == check_date,
        TourSchedule.status != 'cancelled'
    ).scalar()
    
    return {
        "resource_id": resource.id,
        "resource_name": resource.name,
        "total_quantity": resource.quantity,
        "used_quantity": int(used),
        "available_quantity": resource.quantity - int(used),
        "date": check_date.isoformat(),
        "start_time": start_time.isoformat()
    }
