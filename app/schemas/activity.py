from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal


# === ACTIVITY TYPE ===
class ActivityTypeResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True


# === LOCATION ===
class LocationCreate(BaseModel):
    name: str
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    country: str = "Россия"
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None


class LocationUpdate(BaseModel):
    name: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None


class LocationResponse(BaseModel):
    id: int
    business_id: int
    name: str
    region: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    country: str
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    description: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


# === ACTIVITY ===
class ActivityCreate(BaseModel):
    activity_type_id: int
    location_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal
    duration_minutes: Optional[int] = None
    min_participants: int = 1
    max_participants: Optional[int] = None
    min_age: Optional[int] = None
    difficulty_level: Optional[str] = None
    what_included: Optional[List[str]] = None
    what_to_bring: Optional[List[str]] = None
    photos: Optional[List[str]] = None


class ActivityUpdate(BaseModel):
    activity_type_id: Optional[int] = None
    location_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Optional[Decimal] = None
    duration_minutes: Optional[int] = None
    min_participants: Optional[int] = None
    max_participants: Optional[int] = None
    min_age: Optional[int] = None
    difficulty_level: Optional[str] = None
    what_included: Optional[List[str]] = None
    what_to_bring: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ActivityResponse(BaseModel):
    id: int
    business_id: int
    activity_type_id: Optional[int] = None
    location_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal
    currency: str
    duration_minutes: Optional[int] = None
    min_participants: int
    max_participants: Optional[int] = None
    min_age: Optional[int] = None
    difficulty_level: Optional[str] = None
    what_included: Optional[List[str]] = None
    what_to_bring: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    activity_type: Optional[ActivityTypeResponse] = None
    location: Optional[LocationResponse] = None
    
    class Config:
        from_attributes = True


# === SCHEDULE ===
class ActivityScheduleCreate(BaseModel):
    activity_id: int
    date: date
    start_time: time
    end_time: Optional[time] = None
    available_slots: int
    price_override: Optional[Decimal] = None


class ActivityScheduleResponse(BaseModel):
    id: int
    activity_id: int
    date: date
    start_time: time
    end_time: Optional[time] = None
    available_slots: int
    booked_slots: int
    price_override: Optional[Decimal] = None
    is_available: bool
    
    class Config:
        from_attributes = True
