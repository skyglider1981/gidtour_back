from pydantic import BaseModel, field_validator, ConfigDict
from typing import Optional, List
from datetime import time, date, datetime
from decimal import Decimal


class ScheduleTemplateCreate(BaseModel):
    tour_id: int
    week_days: List[int] = [1, 2, 3, 4, 5, 6, 7]
    start_time: time
    end_time: time
    slot_duration_minutes: int
    break_duration_minutes: int = 0
    is_active: bool = True
    
    @field_validator('slot_duration_minutes')
    @classmethod
    def validate_slot_duration(cls, v):
        if v <= 0:
            raise ValueError('Длительность слота должна быть положительной')
        if v > 480:  # 8 часов
            raise ValueError('Слишком длинный слот (макс 8 часов)')
        return v
    
    @field_validator('week_days')
    @classmethod
    def validate_week_days(cls, v):
        if not v:
            raise ValueError('Должен быть выбран хотя бы один день недели')
        for day in v:
            if day < 1 or day > 7:
                raise ValueError('Дни недели должны быть в диапазоне 1-7')
        return sorted(set(v))  # Убираем дубликаты и сортируем
    
    @field_validator('end_time')
    @classmethod
    def validate_times(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('Время окончания должно быть позже времени начала')
        return v


class ScheduleTemplateUpdate(BaseModel):
    week_days: Optional[List[int]] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    slot_duration_minutes: Optional[int] = None
    break_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class ScheduleTemplateResponse(BaseModel):
    id: int
    tour_id: int
    week_days: List[int]
    start_time: time
    end_time: time
    slot_duration_minutes: int
    break_duration_minutes: int
    is_active: bool
    created_at: datetime
    
    # Дополнительные поля
    tour_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ScheduleGenerateRequest(BaseModel):
    template_id: int
    start_date: date
    end_date: date
    overwrite_existing: bool = False
    check_resource_conflicts: bool = True
    
    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError('Дата окончания должна быть позже даты начала')
        if (v - info.data['start_date']).days > 365:
            raise ValueError('Нельзя генерировать расписание более чем на год вперед')
        return v


class ScheduleResourceResponse(BaseModel):
    id: int
    tour_schedule_id: int
    resource_id: int
    quantity_used: int
    resource_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class GeneratedScheduleInfo(BaseModel):
    message: str
    slots_created: int
    slots_skipped: int
    conflicts: List[str] = []
    template_id: int
    tour_id: int
    start_date: date
    end_date: date
