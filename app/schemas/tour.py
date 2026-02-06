from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date, time, datetime


# === TOUR ACTIVITY ===
class TourActivityCreate(BaseModel):
    activity_id: int
    order_index: int = 0
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None


class TourActivityResponse(BaseModel):
    id: int
    tour_id: int
    activity_id: int
    order_index: int
    duration_minutes: Optional[int] = None
    notes: Optional[str] = None
    activity_name: Optional[str] = None

    class Config:
        from_attributes = True


# === TOUR RESOURCE ===
class TourResourceCreate(BaseModel):
    resource_id: int
    quantity_needed: int = 1


class TourResourceResponse(BaseModel):
    id: int
    tour_id: int
    resource_id: int
    quantity_needed: int
    resource_name: Optional[str] = None
    resource_type: Optional[str] = None
    available_quantity: Optional[int] = None  # сколько всего есть

    class Config:
        from_attributes = True


# === TOUR INSTRUCTOR ===
class TourInstructorCreate(BaseModel):
    instructor_id: int
    is_lead: bool = False


class TourInstructorResponse(BaseModel):
    id: int
    tour_id: int
    instructor_id: int
    is_lead: bool
    instructor_name: Optional[str] = None

    class Config:
        from_attributes = True


# === TOUR LOCATION ===
class TourLocationCreate(BaseModel):
    location_id: int
    is_meeting_point: bool = False
    is_activity_point: bool = True
    notes: Optional[str] = None


class TourLocationResponse(BaseModel):
    id: int
    tour_id: int
    location_id: int
    is_meeting_point: bool
    is_activity_point: bool
    notes: Optional[str] = None
    location_name: Optional[str] = None
    location_address: Optional[str] = None

    class Config:
        from_attributes = True


# === TOUR ===
class TourCreate(BaseModel):
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
    weather_restrictions: Optional[str] = None
    health_restrictions: Optional[str] = None

    # Связи
    activities: Optional[List[TourActivityCreate]] = []
    resources: Optional[List[TourResourceCreate]] = []
    locations: Optional[List[TourLocationCreate]] = []


class TourUpdate(BaseModel):
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
    weather_restrictions: Optional[str] = None
    health_restrictions: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class TourResponse(BaseModel):
    id: int
    business_id: int
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal
    currency: str = "RUB"
    duration_minutes: Optional[int] = None
    min_participants: int = 1
    max_participants: Optional[int] = None
    min_age: Optional[int] = None
    difficulty_level: Optional[str] = None
    what_included: Optional[List[str]] = None
    what_to_bring: Optional[List[str]] = None
    photos: Optional[List[str]] = None
    weather_restrictions: Optional[str] = None
    health_restrictions: Optional[str] = None
    status: str = "active"
    is_active: bool = True
    created_at: datetime

    # Связи
    activities: Optional[List[TourActivityResponse]] = []
    resources: Optional[List[TourResourceResponse]] = []
    instructors: Optional[List[TourInstructorResponse]] = []
    locations: Optional[List[TourLocationResponse]] = []

    class Config:
        from_attributes = True


# === SCHEDULE RESOURCE ===
class ScheduleResourceCreate(BaseModel):
    resource_id: int
    quantity_used: int = 1


class ScheduleResourceResponse(BaseModel):
    id: int
    tour_schedule_id: int
    resource_id: int
    quantity_used: int
    resource_name: Optional[str] = None

    class Config:
        from_attributes = True


# === TOUR SCHEDULE ===
class TourScheduleCreate(BaseModel):
    date: date
    start_time: time
    end_time: Optional[time] = None
    available_slots: int
    instructor_id: Optional[int] = None
    price_override: Optional[Decimal] = None
    notes: Optional[str] = None
    resources: Optional[List[ScheduleResourceCreate]] = []  # какие ресурсы занять


class TourScheduleUpdate(BaseModel):
    date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    available_slots: Optional[int] = None
    instructor_id: Optional[int] = None
    price_override: Optional[Decimal] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class TourScheduleResponse(BaseModel):
    id: int
    tour_id: int
    instructor_id: Optional[int] = None
    date: date
    start_time: time
    end_time: Optional[time] = None
    available_slots: int
    booked_slots: int = 0
    price_override: Optional[Decimal] = None
    status: str = "available"
    notes: Optional[str] = None

    # Вычисляемые/дополнительные поля
    free_slots: Optional[int] = None
    tour_name: Optional[str] = None
    instructor_name: Optional[str] = None
    schedule_resources: Optional[List[ScheduleResourceResponse]] = []

    class Config:
        from_attributes = True
