from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, timedelta
from typing import List

from app.core.database import get_db
from app.api.deps import get_current_business_user
from app.models.user import User
from app.models.tour import Tour, TourSchedule
from app.models.schedule import ScheduleTemplate  # Импортируем из schedule
from app.schemas.schedule import (
    ScheduleTemplateCreate, 
    ScheduleTemplateUpdate,
    ScheduleTemplateResponse,
    ScheduleGenerateRequest,
    GeneratedScheduleInfo
)
from app.services.schedule_generator import ScheduleGenerator

router = APIRouter(prefix="/business/schedule-templates", tags=["Шаблоны расписаний"])


@router.get("/", response_model=List[ScheduleTemplateResponse])
async def get_schedule_templates(
    tour_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить шаблоны расписаний"""
    business_id = current_user.business_profile.id
    
    query = db.query(ScheduleTemplate).join(Tour).filter(
        Tour.business_id == business_id
    )
    
    if tour_id:
        query = query.filter(ScheduleTemplate.tour_id == tour_id)
    
    templates = query.order_by(ScheduleTemplate.created_at.desc()).all()
    
    result = []
    for template in templates:
        template_data = ScheduleTemplateResponse.model_validate(template)
        template_data.tour_name = template.tour.name if template.tour else None
        result.append(template_data)
    
    return result


@router.get("/{template_id}", response_model=ScheduleTemplateResponse)
async def get_schedule_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить шаблон по ID"""
    business_id = current_user.business_profile.id
    
    template = db.query(ScheduleTemplate).join(Tour).filter(
        ScheduleTemplate.id == template_id,
        Tour.business_id == business_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    response = ScheduleTemplateResponse.model_validate(template)
    response.tour_name = template.tour.name if template.tour else None
    
    return response


@router.post("/", response_model=ScheduleTemplateResponse)
async def create_schedule_template(
    data: ScheduleTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать шаблон расписания"""
    business_id = current_user.business_profile.id
    
    # Проверяем что тур принадлежит бизнесу
    tour = db.query(Tour).filter(
        Tour.id == data.tour_id,
        Tour.business_id == business_id
    ).first()
    
    if not tour:
        raise HTTPException(status_code=404, detail="Тур не найден")
    
    # Создаем шаблон
    template = ScheduleTemplate(**data.model_dump())
    db.add(template)
    db.commit()
    db.refresh(template)
    
    response = ScheduleTemplateResponse.model_validate(template)
    response.tour_name = tour.name
    
    return response


@router.put("/{template_id}", response_model=ScheduleTemplateResponse)
async def update_schedule_template(
    template_id: int,
    data: ScheduleTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить шаблон расписания"""
    business_id = current_user.business_profile.id
    
    template = db.query(ScheduleTemplate).join(Tour).filter(
        ScheduleTemplate.id == template_id,
        Tour.business_id == business_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Обновляем только переданные поля
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    response = ScheduleTemplateResponse.model_validate(template)
    response.tour_name = template.tour.name if template.tour else None
    
    return response


@router.delete("/{template_id}")
async def delete_schedule_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить шаблон расписания"""
    business_id = current_user.business_profile.id
    
    template = db.query(ScheduleTemplate).join(Tour).filter(
        ScheduleTemplate.id == template_id,
        Tour.business_id == business_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Проверяем есть ли сгенерированные расписания
    schedules_count = db.query(TourSchedule).filter(
        TourSchedule.schedule_template_id == template_id
    ).count()
    
    if schedules_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Нельзя удалить шаблон, так как существует {schedules_count} сгенерированных расписаний"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "Шаблон удален"}


@router.post("/{template_id}/generate", response_model=GeneratedScheduleInfo)
async def generate_schedules(
    template_id: int,
    data: ScheduleGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Сгенерировать расписания из шаблона"""
    business_id = current_user.business_profile.id
    
    template = db.query(ScheduleTemplate).join(Tour).filter(
        ScheduleTemplate.id == template_id,
        Tour.business_id == business_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Генерируем расписания
    try:
        slots_created, slots_skipped, conflicts = ScheduleGenerator.generate_schedules_from_template(
            db=db,
            template=template,
            start_date=data.start_date,
            end_date=data.end_date,
            overwrite_existing=data.overwrite_existing,
            check_resource_conflicts=data.check_resource_conflicts
        )
        
        return GeneratedScheduleInfo(
            message=f"Создано {slots_created} слотов, пропущено {slots_skipped}",
            slots_created=slots_created,
            slots_skipped=slots_skipped,
            conflicts=conflicts,
            template_id=template_id,
            tour_id=template.tour_id,
            start_date=data.start_date,
            end_date=data.end_date
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@router.get("/{template_id}/preview")
async def preview_schedule_generation(
    template_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Предпросмотр генерации расписаний (без сохранения)"""
    business_id = current_user.business_profile.id
    
    template = db.query(ScheduleTemplate).join(Tour).filter(
        ScheduleTemplate.id == template_id,
        Tour.business_id == business_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    # Рассчитываем сколько слотов будет создано
    tour = template.tour
    current_date = start_date
    total_slots = 0
    preview_dates = []
    
    while current_date <= end_date:
        weekday = current_date.weekday() + 1
        
        if weekday in template.week_days:
            # Рассчитываем количество слотов на день
            start_dt = datetime.combine(current_date, template.start_time)
            end_dt = datetime.combine(current_date, template.end_time)
            
            slots_in_day = 0
            current_dt = start_dt
            
            while current_dt < end_dt:
                slot_end_dt = current_dt + timedelta(minutes=template.slot_duration_minutes)
                if slot_end_dt > end_dt:
                    break
                slots_in_day += 1
                current_dt = slot_end_dt + timedelta(minutes=template.break_duration_minutes)
            
            total_slots += slots_in_day
            preview_dates.append({
                "date": current_date,
                "weekday": weekday,
                "slots": slots_in_day,
                "start_time": template.start_time,
                "end_time": template.end_time
            })
        
        current_date += timedelta(days=1)
    
    return {
        "template_id": template_id,
        "tour_id": tour.id,
        "tour_name": tour.name,
        "start_date": start_date,
        "end_date": end_date,
        "total_slots": total_slots,
        "preview_dates": preview_dates,
        "estimated_duration_minutes": tour.duration_minutes,
        "resources_needed": [
            {
                "resource_id": tr.resource_id,
                "resource_name": tr.resource.name if tr.resource else None,
                "quantity_needed": tr.quantity_needed
            }
            for tr in tour.tour_resources
        ]
    }