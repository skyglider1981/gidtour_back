# app/schemas/booking.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ========== БАЗОВЫЕ СХЕМЫ ==========

class BookingResourceBase(BaseModel):
    resource_id: int
    quantity: int = 1
    price_per_unit: Optional[Decimal] = None


class BookingResourceCreate(BookingResourceBase):
    pass


class BookingResourceResponse(BookingResourceBase):
    id: int
    resource_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== СХЕМЫ БРОНИРОВАНИЯ ==========

class BookingBase(BaseModel):
    tour_schedule_id: int
    participants_count: int = Field(..., ge=1, le=100)
    customer_name: str = Field(..., min_length=2, max_length=255)
    customer_phone: str = Field(..., min_length=10, max_length=50)
    customer_email: Optional[EmailStr] = None
    notes: Optional[str] = None


class BookingCreate(BookingBase):
    """Создание бронирования (публичный API)"""
    pass


class BookingCreateCRM(BookingBase):
    """Создание бронирования из CRM"""
    customer_id: Optional[int] = None
    status: Optional[str] = 'pending'
    total_price: Optional[Decimal] = None


class BookingUpdate(BaseModel):
    """Обновление бронирования"""
    participants_count: Optional[int] = Field(None, ge=1, le=100)
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class BookingStatusUpdate(BaseModel):
    """Изменение статуса бронирования"""
    status: str = Field(..., pattern="^(pending|confirmed|paid|cancelled|completed)$")
    notes: Optional[str] = None


class BookingResponse(BaseModel):
    """Ответ с данными бронирования"""
    id: int
    booking_code: str
    booking_type: str
    tour_schedule_id: Optional[int] = None
    activity_schedule_id: Optional[int] = None
    
    # Данные клиента
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    
    # Детали бронирования
    participants_count: int
    total_price: Decimal
    currency: str = 'RUB'
    status: str
    notes: Optional[str] = None
    
    # Даты
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    
    # Связанные данные
    booking_resources: List[BookingResourceResponse] = []
    
    # Дополнительные данные (заполняются из связей)
    tour_name: Optional[str] = None
    schedule_date: Optional[str] = None
    schedule_time: Optional[str] = None
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Список бронирований с пагинацией"""
    items: List[BookingResponse]
    total: int
    page: int
    per_page: int
    pages: int


# ========== СХЕМЫ ДЛЯ ПУБЛИЧНОГО API ==========

class PublicTourResponse(BaseModel):
    """Тур для публичного API"""
    id: int
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    base_price: Decimal
    duration_minutes: Optional[int] = None
    min_participants: int = 1
    max_participants: Optional[int] = None
    photos: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class PublicScheduleResponse(BaseModel):
    """Слот расписания для публичного API"""
    id: int
    date: str
    start_time: str
    end_time: str
    available_slots: int
    booked_slots: int
    free_slots: int  # available - booked
    status: str  # available, partially_booked, fully_booked
    price_per_person: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


class BookingCalculation(BaseModel):
    """Расчёт стоимости бронирования"""
    tour_id: int
    schedule_id: int
    participants_count: int
    
    # Результат расчёта
    base_price: Decimal
    total_price: Decimal
    resources_needed: List[dict] = []
    available: bool
    message: Optional[str] = None


class BookingConfirmation(BaseModel):
    """Подтверждение бронирования"""
    booking_code: str
    status: str
    message: str
    tour_name: str
    schedule_date: str
    schedule_time: str
    participants_count: int
    total_price: Decimal
    customer_name: str
    customer_phone: str
