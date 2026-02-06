from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ResourceType(Base):
    """Справочник типов ресурсов"""
    __tablename__ = "resource_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    element = Column(String(20))  # air, land, water, winter
    icon = Column(String(50))
    is_active = Column(Boolean, default=True)
    
    # Связи
    resources = relationship("Resource", back_populates="resource_type_rel")
    activity_types = relationship("ActivityType", secondary="activity_resource_types", back_populates="resource_types")


class Resource(Base):
    """Ресурсы бизнеса (конкретные единицы техники/оборудования)"""
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"))
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="SET NULL"))
    resource_type_id = Column(Integer, ForeignKey("resource_types.id"))
    
    name = Column(String(255), nullable=False)
    resource_type = Column(String(100), nullable=False)  # legacy, используем resource_type_id
    quantity = Column(Integer, default=1, nullable=False)
    seats_per_unit = Column(Integer, default=1, nullable=False)
    description = Column(Text)
    equipment = Column(Text)  # комплектация
    requires_license = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    business = relationship("BusinessProfile", back_populates="resources")
    location = relationship("Location", back_populates="resources")
    resource_type_rel = relationship("ResourceType", back_populates="resources")
    tour_resources = relationship("TourResource", back_populates="resource")
    schedule_resources = relationship("ScheduleResource", back_populates="resource")


class Instructor(Base):
    """Инструкторы"""
    __tablename__ = "instructors"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"))
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    email = Column(String(255))
    photo_url = Column(String(500))
    specialties = Column(ARRAY(Text))
    certifications = Column(ARRAY(Text))
    languages = Column(ARRAY(Text))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    business = relationship("BusinessProfile", back_populates="instructors")
    tour_instructors = relationship("TourInstructor", back_populates="instructor")
    tour_schedules = relationship("TourSchedule", back_populates="instructor")


class ScheduleResource(Base):
    """Занятость ресурсов на таймслотах"""
    __tablename__ = "schedule_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    tour_schedule_id = Column(Integer, ForeignKey("tour_schedules.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="CASCADE"), nullable=False)
    quantity_used = Column(Integer, default=1, nullable=False)
    
    # Связи
    tour_schedule = relationship("TourSchedule", back_populates="schedule_resources")
    resource = relationship("Resource", back_populates="schedule_resources")


class ActivityResourceType(Base):
    """Связь типов активностей с типами ресурсов"""
    __tablename__ = "activity_resource_types"
    
    id = Column(Integer, primary_key=True, index=True)
    activity_type_id = Column(Integer, ForeignKey("activity_types.id", ondelete="CASCADE"))
    resource_type_id = Column(Integer, ForeignKey("resource_types.id", ondelete="CASCADE"))
