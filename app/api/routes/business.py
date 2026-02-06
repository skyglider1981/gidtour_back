from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_business_user
from app.models.user import User, BusinessProfile
from app.models.activity import Activity, Location, ActivityType
from app.models.tour import Tour
from app.schemas.user import BusinessProfileUpdate, BusinessProfileResponse
from app.schemas.activity import (
    ActivityCreate, ActivityUpdate, ActivityResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    ActivityTypeResponse
)

router = APIRouter(prefix="/business", tags=["Бизнес-панель"])


# === DASHBOARD ===
@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Данные для дашборда бизнеса"""
    profile = current_user.business_profile
    
    activities_count = db.query(Activity).filter(
        Activity.business_id == profile.id
    ).count()
    
    tours_count = db.query(Tour).filter(
        Tour.business_id == profile.id
    ).count()
    
    locations_count = db.query(Location).filter(
        Location.business_id == profile.id
    ).count()
    
    return {
        "business_name": profile.business_name,
        "is_verified": profile.is_verified,
        "stats": {
            "activities": activities_count,
            "tours": tours_count,
            "locations": locations_count,
            "bookings": 0  # TODO: добавить подсчёт бронирований
        }
    }


# === PROFILE ===
@router.get("/profile", response_model=BusinessProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_business_user)
):
    """Получить профиль бизнеса"""
    return current_user.business_profile


@router.put("/profile", response_model=BusinessProfileResponse)
async def update_profile(
    data: BusinessProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить профиль бизнеса"""
    profile = current_user.business_profile
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    return profile


# === ACTIVITY TYPES (справочник) ===
@router.get("/activity-types", response_model=List[ActivityTypeResponse])
async def get_activity_types(db: Session = Depends(get_db)):
    """Получить список типов активностей"""
    return db.query(ActivityType).filter(ActivityType.is_active == True).all()


# === LOCATIONS ===
@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить локации бизнеса"""
    return db.query(Location).filter(
        Location.business_id == current_user.business_profile.id
    ).all()


@router.post("/locations", response_model=LocationResponse)
async def create_location(
    data: LocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать локацию"""
    location = Location(
        business_id=current_user.business_profile.id,
        **data.model_dump()
    )
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить локацию по ID"""
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == current_user.business_profile.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    
    return location


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: int,
    data: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить локацию"""
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == current_user.business_profile.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(location, field, value)
    
    db.commit()
    db.refresh(location)
    return location


@router.delete("/locations/{location_id}")
async def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить локацию"""
    location = db.query(Location).filter(
        Location.id == location_id,
        Location.business_id == current_user.business_profile.id
    ).first()
    
    if not location:
        raise HTTPException(status_code=404, detail="Локация не найдена")
    
    db.delete(location)
    db.commit()
    return {"message": "Локация удалена"}


# === ACTIVITIES ===
@router.get("/activities", response_model=List[ActivityResponse])
async def get_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить активности бизнеса"""
    return db.query(Activity).filter(
        Activity.business_id == current_user.business_profile.id
    ).all()


@router.post("/activities", response_model=ActivityResponse)
async def create_activity(
    data: ActivityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать активность"""
    activity = Activity(
        business_id=current_user.business_profile.id,
        **data.model_dump()
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


@router.get("/activities/{activity_id}", response_model=ActivityResponse)
async def get_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить активность по ID"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_user.business_profile.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    return activity


@router.put("/activities/{activity_id}", response_model=ActivityResponse)
async def update_activity(
    activity_id: int,
    data: ActivityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить активность"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_user.business_profile.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    return activity


@router.delete("/activities/{activity_id}")
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить активность"""
    activity = db.query(Activity).filter(
        Activity.id == activity_id,
        Activity.business_id == current_user.business_profile.id
    ).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="Активность не найдена")
    
    db.delete(activity)
    db.commit()
    return {"message": "Активность удалена"}
