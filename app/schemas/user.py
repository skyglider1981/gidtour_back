from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# === AUTH ===
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    user_type: str = "business"  # business или customer


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_type: str
    user_id: int


# === USER ===
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# === BUSINESS PROFILE ===
class BusinessProfileCreate(BaseModel):
    business_name: str
    description: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None


class BusinessProfileUpdate(BaseModel):
    business_name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None


class BusinessProfileResponse(BaseModel):
    id: int
    user_id: int
    business_name: str
    description: Optional[str] = None
    logo_url: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# === FULL USER WITH PROFILE ===
class BusinessUserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    user_type: str
    is_active: bool
    created_at: datetime
    business_profile: Optional[BusinessProfileResponse] = None
    
    class Config:
        from_attributes = True
