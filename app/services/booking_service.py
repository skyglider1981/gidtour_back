# app/services/booking_service.py
"""
Сервис бронирований.

Логика ценообразования:
- Цена тура = tour.base_price × кол-во участников
- Ресурсы учитываются только для занятости/вместимости (без влияния на цену)
"""
import uuid
import math
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.booking import Booking, BookingResource
from app.models.tour import Tour, TourSchedule, TourResource
from app.models.resource import Resource


class BookingService:
    """Сервис для работы с бронированиями"""
    
    @staticmethod
    def generate_booking_code() -> str:
        """Генерация уникального кода бронирования"""
        return f"BK{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def calculate_resources_needed(
        db: Session,
        tour_id: int,
        participants_count: int
    ) -> Tuple[List[dict], int]:
        """
        Расчёт необходимых ресурсов для бронирования (справочно, без цен)
        
        Returns:
            (список ресурсов, общая вместимость)
        """
        # Получаем ресурсы тура
        tour_resources = db.query(TourResource).filter(
            TourResource.tour_id == tour_id
        ).all()
        
        resources_needed = []
        total_capacity = 0
        
        for tr in tour_resources:
            resource = db.query(Resource).filter(Resource.id == tr.resource_id).first()
            if not resource:
                continue
            
            seats_per_unit = resource.seats_per_unit or 1
            
            # Сколько единиц ресурса нужно для этого количества участников
            units_needed = math.ceil(participants_count / seats_per_unit)
            
            # Ограничиваем количеством указанным в туре
            units_needed = min(units_needed, tr.quantity_needed)
            
            capacity = units_needed * seats_per_unit
            total_capacity += capacity
            
            # Ресурсы — справочно, без цен
            resources_needed.append({
                'resource_id': resource.id,
                'resource_name': resource.name,
                'resource_type': resource.resource_type,
                'quantity_needed': units_needed,
                'quantity_available': resource.quantity,
                'seats_per_unit': seats_per_unit,
                'capacity': capacity
            })
        
        return resources_needed, total_capacity
    
    @staticmethod
    def check_availability(
        db: Session,
        tour_schedule_id: int,
        participants_count: int
    ) -> Tuple[bool, str, int]:
        """
        Проверка доступности слота для бронирования
        
        Returns:
            (доступен, сообщение, свободных мест)
        """
        schedule = db.query(TourSchedule).filter(
            TourSchedule.id == tour_schedule_id
        ).first()
        
        if not schedule:
            return False, "Слот не найден", 0
        
        # Считаем занятые места
        booked = db.query(func.coalesce(func.sum(Booking.participants_count), 0)).filter(
            Booking.tour_schedule_id == tour_schedule_id,
            Booking.status.in_(['pending', 'confirmed', 'paid'])
        ).scalar() or 0
        
        available = schedule.available_slots - booked
        
        if available < participants_count:
            return False, f"Недостаточно мест. Свободно: {available}", available
        
        return True, "Доступно", available
    
    @staticmethod
    def calculate_price(
        db: Session,
        tour_id: int,
        schedule_id: int,
        participants_count: int
    ) -> Tuple[float, List[dict]]:
        """
        Расчёт стоимости бронирования.
        
        Логика: цена тура × кол-во участников.
        Ресурсы возвращаются справочно.
        
        Returns:
            (общая стоимость, список ресурсов)
        """
        tour = db.query(Tour).filter(Tour.id == tour_id).first()
        if not tour:
            return 0, []
        
        # Цена из тура × кол-во участников
        base_price = float(tour.base_price or 0)
        total_price = base_price * participants_count
        
        # Ресурсы — справочно
        resources_needed, _ = BookingService.calculate_resources_needed(
            db, tour_id, participants_count
        )
        
        return total_price, resources_needed
    
    @staticmethod
    def create_booking(
        db: Session,
        tour_schedule_id: int,
        participants_count: int,
        customer_name: str,
        customer_phone: str,
        customer_email: Optional[str] = None,
        customer_id: Optional[int] = None,
        notes: Optional[str] = None,
        status: str = 'pending'
    ) -> Tuple[Optional[Booking], str]:
        """
        Создание бронирования
        
        Returns:
            (бронирование, сообщение об ошибке или успехе)
        """
        # Получаем слот
        schedule = db.query(TourSchedule).filter(
            TourSchedule.id == tour_schedule_id
        ).first()
        
        if not schedule:
            return None, "Слот расписания не найден"
        
        # Проверяем доступность
        available, message, free_slots = BookingService.check_availability(
            db, tour_schedule_id, participants_count
        )
        
        if not available:
            return None, message
        
        # Расчёт стоимости (из тура)
        total_price, resources_needed = BookingService.calculate_price(
            db, schedule.tour_id, tour_schedule_id, participants_count
        )
        
        # Создаём бронирование
        booking = Booking(
            booking_code=BookingService.generate_booking_code(),
            booking_type='tour',
            tour_schedule_id=tour_schedule_id,
            customer_id=customer_id,
            participants_count=participants_count,
            total_price=total_price,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_email=customer_email,
            notes=notes,
            status=status
        )
        
        db.add(booking)
        db.flush()  # Получаем ID
        
        # Создаём записи о ресурсах (справочно, без цен)
        for res in resources_needed:
            booking_resource = BookingResource(
                booking_id=booking.id,
                resource_id=res['resource_id'],
                quantity=res['quantity_needed'],
                price_per_unit=None  # Цена не из ресурса
            )
            db.add(booking_resource)
        
        # Обновляем booked_slots в расписании
        schedule.booked_slots = (schedule.booked_slots or 0) + participants_count
        
        db.commit()
        db.refresh(booking)
        
        return booking, "Бронирование успешно создано"
    
    @staticmethod
    def update_status(
        db: Session,
        booking_id: int,
        new_status: str,
        notes: Optional[str] = None
    ) -> Tuple[Optional[Booking], str]:
        """Изменение статуса бронирования"""
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        
        if not booking:
            return None, "Бронирование не найдено"
        
        old_status = booking.status
        booking.status = new_status
        
        # Обновляем даты
        now = datetime.utcnow()
        if new_status == 'confirmed' and not booking.confirmed_at:
            booking.confirmed_at = now
        elif new_status == 'paid' and not booking.paid_at:
            booking.paid_at = now
            if not booking.confirmed_at:
                booking.confirmed_at = now
        elif new_status == 'cancelled' and not booking.cancelled_at:
            booking.cancelled_at = now
            # Освобождаем места
            if booking.tour_schedule_id:
                schedule = db.query(TourSchedule).filter(
                    TourSchedule.id == booking.tour_schedule_id
                ).first()
                if schedule:
                    schedule.booked_slots = max(0, (schedule.booked_slots or 0) - booking.participants_count)
        
        if notes:
            booking.notes = f"{booking.notes or ''}\n[{now}] {notes}".strip()
        
        db.commit()
        db.refresh(booking)
        
        return booking, f"Статус изменён с {old_status} на {new_status}"
    
    @staticmethod
    def cancel_booking(
        db: Session,
        booking_id: int,
        reason: Optional[str] = None
    ) -> Tuple[Optional[Booking], str]:
        """Отмена бронирования"""
        return BookingService.update_status(
            db, booking_id, 'cancelled', 
            notes=f"Причина отмены: {reason}" if reason else None
        )
    
    @staticmethod
    def get_bookings_for_schedule(
        db: Session,
        tour_schedule_id: int
    ) -> List[Booking]:
        """Получение всех бронирований для слота"""
        return db.query(Booking).filter(
            Booking.tour_schedule_id == tour_schedule_id,
            Booking.status.notin_(['cancelled'])
        ).all()
    
    @staticmethod
    def get_schedule_stats(
        db: Session,
        tour_schedule_id: int
    ) -> dict:
        """Статистика по слоту"""
        schedule = db.query(TourSchedule).filter(
            TourSchedule.id == tour_schedule_id
        ).first()
        
        if not schedule:
            return {}
        
        bookings = BookingService.get_bookings_for_schedule(db, tour_schedule_id)
        
        total_booked = sum(b.participants_count for b in bookings)
        pending = sum(b.participants_count for b in bookings if b.status == 'pending')
        confirmed = sum(b.participants_count for b in bookings if b.status in ['confirmed', 'paid'])
        
        return {
            'schedule_id': tour_schedule_id,
            'available_slots': schedule.available_slots,
            'booked_slots': total_booked,
            'free_slots': schedule.available_slots - total_booked,
            'pending_count': pending,
            'confirmed_count': confirmed,
            'bookings_count': len(bookings),
            'status': 'fully_booked' if total_booked >= schedule.available_slots else 
                     'partially_booked' if total_booked > 0 else 'available'
        }
