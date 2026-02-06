from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# === RESOURCE TYPE (справочник) ===
class ResourceTypeResponse(BaseModel):
    id: int
    name: str
    element: Optional[str] = None
    icon: Optional[str] = None
    
    class Config:
        from_attributes = True


# === RESOURCE ===
class ResourceCreate(BaseModel):
    name: str
    resource_type: str
    location_id: Optional[int] = None
    quantity: int = 1
    seats_per_unit: int = 1
    description: Optional[str] = None
    equipment: Optional[str] = None
    requires_license: bool = False


class ResourceUpdate(BaseModel):
    name: Optional[str] = None
    resource_type: Optional[str] = None
    location_id: Optional[int] = None
    quantity: Optional[int] = None
    seats_per_unit: Optional[int] = None
    description: Optional[str] = None
    equipment: Optional[str] = None
    requires_license: Optional[bool] = None
    is_active: Optional[bool] = None


class ResourceResponse(BaseModel):
    id: int
    business_id: int
    location_id: Optional[int] = None
    name: str
    resource_type: str
    quantity: int
    seats_per_unit: int
    total_seats: Optional[int] = None  # Вычисляемое поле
    description: Optional[str] = None
    equipment: Optional[str] = None
    requires_license: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_total(cls, obj):
        response = cls.model_validate(obj)
        response.total_seats = obj.quantity * obj.seats_per_unit
        return response


# === ACTIVITY RESOURCE (связь) ===
class ActivityResourceCreate(BaseModel):
    resource_id: int
    quantity_needed: int = 1
    requires_instructor: bool = True
    instructor_takes_seat: bool = False
    client_can_drive: bool = False
    notes: Optional[str] = None


class ActivityResourceResponse(BaseModel):
    id: int
    activity_id: int
    resource_id: int
    quantity_needed: int
    requires_instructor: bool
    instructor_takes_seat: bool
    client_can_drive: bool
    notes: Optional[str] = None
    resource: Optional[ResourceResponse] = None
    
    class Config:
        from_attributes = True


# === INSTRUCTOR ===
class InstructorCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    description: Optional[str] = None


class InstructorUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InstructorResponse(BaseModel):
    id: int
    business_id: int
    full_name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    photo_url: Optional[str] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
