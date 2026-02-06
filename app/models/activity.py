from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, Numeric, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ActivityType(Base):
    """Справочник типов активностей"""
    __tablename__ = "activity_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    category = Column(String(100))
    description = Column(Text)
    icon = Column(String(50))
    element = Column(String(20))  # air, land, water, winter
    is_active = Column(Boolean, default=True)
    
    # Связи
    activities = relationship("Activity", back_populates="activity_type")
    resource_types = relationship("ResourceType", secondary="activity_resource_types", back_populates="activity_types")


class Activity(Base):
    """Активности бизнеса"""
    __tablename__ = "activities"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"))
    activity_type_id = Column(Integer, ForeignKey("activity_types.id"))
    location_id = Column(Integer, ForeignKey("locations.id"))
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    short_description = Column(String(500))
    base_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="RUB")
    duration_minutes = Column(Integer)
    
    min_participants = Column(Integer, default=1)
    max_participants = Column(Integer)
    min_age = Column(Integer)
    difficulty_level = Column(String(50))
    
    what_included = Column(ARRAY(Text))
    what_to_bring = Column(ARRAY(Text))
    photos = Column(ARRAY(Text))
    
    status = Column(String(20), default="active")  # active, moderation, rejected, frozen
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    business = relationship("BusinessProfile", back_populates="activities")
    activity_type = relationship("ActivityType", back_populates="activities")
    location = relationship("Location", back_populates="activities")
    tour_activities = relationship("TourActivity", back_populates="activity")
    location_activities = relationship("LocationActivity", back_populates="activity")


class Location(Base):
    """Локации"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"))
    
    name = Column(String(255), nullable=False)
    region = Column(String(100))
    city = Column(String(100))
    address = Column(Text)
    country = Column(String(100), default="Россия")
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    business = relationship("BusinessProfile", back_populates="locations")
    activities = relationship("Activity", back_populates="location")
    resources = relationship("Resource", back_populates="location")
    tour_locations = relationship("TourLocation", back_populates="location")
    location_activities = relationship("LocationActivity", back_populates="location")


class LocationActivity(Base):
    """Связь локация - активность (какие активности доступны на локации)"""
    __tablename__ = "location_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"))
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    
    # Связи
    location = relationship("Location", back_populates="location_activities")
    activity = relationship("Activity", back_populates="location_activities")
