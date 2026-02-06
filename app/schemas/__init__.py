from .activity import ActivityCreate, ActivityUpdate, ActivityResponse, ActivityTypeResponse
from .resource import ResourceCreate, ResourceUpdate, ResourceResponse, InstructorCreate, InstructorResponse
from .location import LocationCreate, LocationUpdate, LocationResponse
from .tour import (
    TourCreate, TourUpdate, TourResponse,
    TourActivityCreate, TourActivityResponse,
    TourResourceCreate, TourResourceResponse,
    TourInstructorCreate, TourInstructorResponse,
    TourLocationCreate, TourLocationResponse,
    TourScheduleCreate, TourScheduleUpdate, TourScheduleResponse,
    ScheduleResourceCreate, ScheduleResourceResponse
)
from .schedule import (
    ScheduleTemplateCreate, 
    ScheduleTemplateUpdate,
    ScheduleTemplateResponse,
    ScheduleGenerateRequest,
    ScheduleResourceResponse,
    GeneratedScheduleInfo
)

# User схемы импортируем осторожно
try:
    from .user import UserCreate, UserLogin, UserResponse, BusinessProfileCreate, BusinessProfileResponse
    USER_SCHEMAS_AVAILABLE = True
except ImportError:
    # Ищем какие схемы на самом деле есть в user.py
    import importlib
    import sys
    USER_SCHEMAS_AVAILABLE = False

__all__ = [
    "ActivityCreate", "ActivityUpdate", "ActivityResponse", "ActivityTypeResponse",
    "ResourceCreate", "ResourceUpdate", "ResourceResponse",
    "InstructorCreate", "InstructorResponse",
    "LocationCreate", "LocationUpdate", "LocationResponse",
    "TourCreate", "TourUpdate", "TourResponse",
    "TourActivityCreate", "TourActivityResponse",
    "TourResourceCreate", "TourResourceResponse",
    "TourInstructorCreate", "TourInstructorResponse",
    "TourLocationCreate", "TourLocationResponse",
    "TourScheduleCreate", "TourScheduleUpdate", "TourScheduleResponse",
    "ScheduleResourceCreate", "ScheduleResourceResponse",
    "ScheduleTemplateCreate",
    "ScheduleTemplateUpdate", 
    "ScheduleTemplateResponse",
    "ScheduleGenerateRequest",
    "GeneratedScheduleInfo",
]

if USER_SCHEMAS_AVAILABLE:
    __all__ = [
        "UserCreate", "UserLogin", "UserResponse", 
        "BusinessProfileCreate", "BusinessProfileResponse",
    ] + __all__