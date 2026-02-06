from pydantic import BaseModel
from typing import Optional
from decimal import Decimal


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
