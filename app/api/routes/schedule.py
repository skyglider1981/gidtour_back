from sqlalchemy import Column, Integer, ForeignKey, Time, Boolean, ARRAY, DateTime, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ScheduleTemplate(Base):
    """Шаблон расписания для массовой генерации тайм-слотов"""
    __tablename__ = "schedule_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"), nullable=False)
    
    # Дни недели: [1,2,3,4,5,6,7] где 1=Понедельник, 7=Воскресенье
    week_days = Column(ARRAY(Integer), default=[1, 2, 3, 4, 5, 6, 7])
    start_time = Column(Time, nullable=False)  # Начало рабочего дня (09:00:00)
    end_time = Column(Time, nullable=False)    # Конец рабочего дня (18:00:00)
    
    slot_duration_minutes = Column(Integer, nullable=False)  # 60, 90, 120 минут
    break_duration_minutes = Column(Integer, default=0)      # 0, 15, 30 минут
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    tour = relationship("Tour", back_populates="schedule_templates")


class ResourceAllocation(Base):
    """
    Распределение ресурсов при бронировании.
    Фиксирует какие ресурсы заняты какой бронью на какое время.
    """
    __tablename__ = "resource_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    tour_schedule_id = Column(Integer, ForeignKey("tour_schedules.id", ondelete="CASCADE"), nullable=False)
    
    quantity = Column(Integer, default=1, nullable=False)
    
    # reserved = предварительно занято (корзина)
    # confirmed = подтверждено (оплачено)
    # released = освобождено (отмена)
    allocation_type = Column(String(20), default='confirmed', nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    
    # Связи
    booking = relationship("Booking", backref="resource_allocations")
    resource = relationship("Resource", backref="allocations")
    tour_schedule = relationship("TourSchedule", backref="resource_allocations")
