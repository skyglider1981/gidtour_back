from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Date, Time, Numeric, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Tour(Base):
    """Туры"""
    __tablename__ = "tours"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="RUB")
    duration_minutes = Column(Integer)
    duration_hours = Column(Numeric(5, 2))  # legacy
    
    min_participants = Column(Integer, default=1)
    max_participants = Column(Integer)
    min_age = Column(Integer)
    difficulty_level = Column(String(50))
    
    meeting_point = Column(Text)  # legacy - используем tour_locations
    what_included = Column(ARRAY(Text))
    what_to_bring = Column(ARRAY(Text))
    photos = Column(ARRAY(Text))
    
    weather_restrictions = Column(Text)
    health_restrictions = Column(Text)
    
    status = Column(String(20), default="active")  # active, moderation, rejected, frozen
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    business = relationship("BusinessProfile", back_populates="tours")
    tour_activities = relationship("TourActivity", back_populates="tour", cascade="all, delete-orphan")
    tour_resources = relationship("TourResource", back_populates="tour", cascade="all, delete-orphan")
    tour_instructors = relationship("TourInstructor", back_populates="tour", cascade="all, delete-orphan")
    tour_locations = relationship("TourLocation", back_populates="tour", cascade="all, delete-orphan")
    schedules = relationship("TourSchedule", back_populates="tour", cascade="all, delete-orphan")
    schedule_templates = relationship("ScheduleTemplate", back_populates="tour", cascade="all, delete-orphan")
    
    # === НОВОЕ: Связи для отзывов ===
    reviews = relationship("Review", back_populates="tour", cascade="all, delete-orphan")
    rating_stats = relationship("TourRatingStats", back_populates="tour", uselist=False, cascade="all, delete-orphan")


class TourActivity(Base):
    """Связь тур - активность"""
    __tablename__ = "tour_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    order_index = Column(Integer, default=0, nullable=False)
    duration_minutes = Column(Integer)
    notes = Column(Text)
    
    # Связи
    tour = relationship("Tour", back_populates="tour_activities")
    activity = relationship("Activity", back_populates="tour_activities")


class TourResource(Base):
    """Связь тур - ресурс (сколько ресурсов нужно для тура)"""
    __tablename__ = "tour_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"))
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"))
    quantity_needed = Column(Integer, default=1, nullable=False)
    
    # Связи
    tour = relationship("Tour", back_populates="tour_resources")
    resource = relationship("Resource", back_populates="tour_resources")


class TourInstructor(Base):
    """Связь тур - инструктор"""
    __tablename__ = "tour_instructors"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"))
    instructor_id = Column(Integer, ForeignKey("instructors.id", ondelete="CASCADE"))
    is_lead = Column(Boolean, default=False)
    
    # Связи
    tour = relationship("Tour", back_populates="tour_instructors")
    instructor = relationship("Instructor", back_populates="tour_instructors")


class TourLocation(Base):
    """Связь тур - локация"""
    __tablename__ = "tour_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"))
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"))
    is_meeting_point = Column(Boolean, default=False)  # точка сбора
    is_activity_point = Column(Boolean, default=True)   # место проведения
    notes = Column(Text)
    
    # Связи
    tour = relationship("Tour", back_populates="tour_locations")
    location = relationship("Location", back_populates="tour_locations")


class TourSchedule(Base):
    """Расписание туров (тайм-слоты)"""
    __tablename__ = "tour_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_id = Column(Integer, ForeignKey("tours.id", ondelete="CASCADE"))
    instructor_id = Column(Integer, ForeignKey("instructors.id"))
    schedule_template_id = Column(Integer, ForeignKey("schedule_templates.id", ondelete="SET NULL"))
    
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time)
    
    available_slots = Column(Integer, nullable=False)  # сколько мест доступно
    booked_slots = Column(Integer, default=0)  # сколько забронировано
    price_override = Column(Numeric(10, 2))  # особая цена на этот слот
    
    status = Column(String(20), default="available")  # available, booked, cancelled
    is_available = Column(Boolean, default=True)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    tour = relationship("Tour", back_populates="schedules")
    instructor = relationship("Instructor", back_populates="tour_schedules")
    schedule_template = relationship("ScheduleTemplate")
    schedule_resources = relationship("ScheduleResource", back_populates="tour_schedule", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="tour_schedule")
