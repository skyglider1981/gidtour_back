from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, time, datetime, timedelta
from typing import List, Tuple
from app.models.tour import Tour, TourSchedule, TourResource
from app.models.schedule import ScheduleTemplate
from app.models.resource import ScheduleResource, Resource
import logging

logger = logging.getLogger(__name__)


class ScheduleGenerator:
    """Сервис для генерации расписаний из шаблонов"""
    
    @staticmethod
    def generate_schedules_from_template(
        db: Session,
        template: ScheduleTemplate,
        start_date: date,
        end_date: date,
        overwrite_existing: bool = False,
        check_resource_conflicts: bool = True
    ) -> Tuple[int, int, List[str]]:
        """
        Генерирует расписания из шаблона на указанный период
        
        Возвращает: (создано_слотов, пропущено_слотов, конфликты)
        """
        tour = db.query(Tour).filter(Tour.id == template.tour_id).first()
        if not tour:
            raise ValueError(f"Тур {template.tour_id} не найден")
        
        # Получаем ресурсы тура
        tour_resources = db.query(TourResource).filter(
            TourResource.tour_id == tour.id
        ).all()
        
        if not tour_resources:
            logger.warning(f"Тур {tour.id} не имеет ресурсов")
        
        slots_created = 0
        slots_skipped = 0
        conflicts = []
        
        current_date = start_date
        while current_date <= end_date:
            # Проверяем день недели (Python: 0=пн, 6=вс)
            weekday = current_date.weekday() + 1  # Приводим к нашему формату 1-7
            
            if weekday in template.week_days:
                created, skipped, day_conflicts = ScheduleGenerator._generate_slots_for_day(
                    db=db,
                    tour=tour,
                    template=template,
                    schedule_date=current_date,
                    tour_resources=tour_resources,
                    overwrite_existing=overwrite_existing,
                    check_resource_conflicts=check_resource_conflicts
                )
                
                slots_created += created
                slots_skipped += skipped
                conflicts.extend(day_conflicts)
            
            current_date += timedelta(days=1)
        
        db.commit()
        return slots_created, slots_skipped, conflicts
    
    @staticmethod
    def _generate_slots_for_day(
        db: Session,
        tour: Tour,
        template: ScheduleTemplate,
        schedule_date: date,
        tour_resources: List[TourResource],
        overwrite_existing: bool,
        check_resource_conflicts: bool
    ) -> Tuple[int, int, List[str]]:
        """Генерирует тайм-слоты на конкретный день"""
        slots_created = 0
        slots_skipped = 0
        conflicts = []
        
        current_time = template.start_time
        end_time = template.end_time
        
        # Конвертируем в datetime для вычислений
        current_dt = datetime.combine(schedule_date, current_time)
        end_dt = datetime.combine(schedule_date, end_time)
        
        while current_dt < end_dt:
            slot_end_dt = current_dt + timedelta(minutes=template.slot_duration_minutes)
            
            # Проверяем что слот не выходит за границы рабочего дня
            if slot_end_dt > end_dt:
                break
            
            # Проверяем существующий слот
            existing_slot = db.query(TourSchedule).filter(
                TourSchedule.tour_id == tour.id,
                TourSchedule.date == schedule_date,
                TourSchedule.start_time == current_dt.time()
            ).first()
            
            if existing_slot and not overwrite_existing:
                slots_skipped += 1
                current_dt = slot_end_dt + timedelta(minutes=template.break_duration_minutes)
                continue
            
            # Проверяем доступность ресурсов
            resource_check = True
            if check_resource_conflicts and tour_resources:
                # Если мы собираемся перезаписать существующий слот, 
                # не нужно исключать его из проверки доступности
                exclude_id = None
                if existing_slot and not overwrite_existing:
                    exclude_id = existing_slot.id
                
                resource_check, conflict_msg = ScheduleGenerator._check_resource_availability(
                    db=db,
                    tour_resources=tour_resources,
                    schedule_date=schedule_date,
                    start_time=current_dt.time(),
                    end_time=slot_end_dt.time(),
                    exclude_schedule_id=exclude_id
                )
                
                if not resource_check:
                    conflicts.append(f"{schedule_date} {current_dt.time()}: {conflict_msg}")
                    slots_skipped += 1
                    current_dt = slot_end_dt + timedelta(minutes=template.break_duration_minutes)
                    continue
            
            # Удаляем существующий слот если overwrite_existing = True
            if existing_slot and overwrite_existing:
                db.delete(existing_slot)
                db.flush()
            
            # Создаем новый слот
            schedule = TourSchedule(
                tour_id=tour.id,
                schedule_template_id=template.id,
                date=schedule_date,
                start_time=current_dt.time(),
                end_time=slot_end_dt.time(),
                available_slots=tour.max_participants or 10,
                status='available'
            )
            db.add(schedule)
            db.flush()  # Получаем ID
            
            # Бронируем ресурсы для этого слота
            if resource_check and tour_resources:
                for tr in tour_resources:
                    schedule_resource = ScheduleResource(
                        tour_schedule_id=schedule.id,
                        resource_id=tr.resource_id,
                        quantity_used=tr.quantity_needed
                    )
                    db.add(schedule_resource)
            
            slots_created += 1
            
            # Добавляем перерыв
            current_dt = slot_end_dt + timedelta(minutes=template.break_duration_minutes)
        
        return slots_created, slots_skipped, conflicts
    
    @staticmethod
    def _check_resource_availability(
        db: Session,
        tour_resources: List[TourResource],
        schedule_date: date,
        start_time: time,
        end_time: time,
        exclude_schedule_id: int = None
    ) -> Tuple[bool, str]:
        """
        Проверяет доступность всех ресурсов тура на указанное время
        
        Возвращает: (доступно, сообщение_об_ошибке)
        """
        for tr in tour_resources:
            resource = db.query(Resource).filter(Resource.id == tr.resource_id).first()
            if not resource:
                return False, f"Ресурс {tr.resource_id} не найден"
            
            # Находим все слоты, которые пересекаются с нашим временным интервалом
            overlapping_schedules = db.query(TourSchedule).filter(
                TourSchedule.date == schedule_date,
                TourSchedule.status != 'cancelled',
                # Проверка пересечения времени: НЕ (конец1 <= начало2 ИЛИ начало1 >= конец2)
                # Т.е. слоты, которые пересекаются с нашим интервалом
                ~((TourSchedule.end_time <= start_time) | (TourSchedule.start_time >= end_time))
            )
            
            if exclude_schedule_id:
                overlapping_schedules = overlapping_schedules.filter(TourSchedule.id != exclude_schedule_id)
            
            overlapping_ids = [s.id for s in overlapping_schedules.all()]
            
            if overlapping_ids:
                # Считаем сколько ресурсов уже занято в пересекающихся слотах
                total_used = db.query(
                    func.coalesce(func.sum(ScheduleResource.quantity_used), 0)
                ).filter(
                    ScheduleResource.resource_id == resource.id,
                    ScheduleResource.tour_schedule_id.in_(overlapping_ids)
                ).scalar() or 0
            else:
                total_used = 0
            
            available = resource.quantity - total_used
            if tr.quantity_needed > available:
                return False, f"Недостаточно '{resource.name}': нужно {tr.quantity_needed}, доступно {available}"
        
        return True, ""