from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.api.deps import get_current_business_user
from app.models.user import User
from app.models.resource import Resource, ResourceType, Instructor, ScheduleResource, ActivityResourceType
from app.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceResponse, ResourceTypeResponse,
    InstructorCreate, InstructorUpdate, InstructorResponse
)

router = APIRouter(prefix="/business", tags=["Ресурсы"])


# === RESOURCE TYPES (справочник) ===
@router.get("/resource-types", response_model=List[ResourceTypeResponse])
async def get_resource_types(
    element: str = None,
    db: Session = Depends(get_db)
):
    """Получить типы ресурсов (справочник)"""
    query = db.query(ResourceType).filter(ResourceType.is_active == True)
    if element:
        query = query.filter(ResourceType.element == element)
    return query.order_by(ResourceType.element, ResourceType.name).all()


# === RESOURCES ===
@router.get("/resources", response_model=List[ResourceResponse])
async def get_resources(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить ресурсы бизнеса"""
    resources = db.query(Resource).filter(
        Resource.business_id == current_user.business_profile.id
    ).order_by(Resource.resource_type, Resource.name).all()
    
    # Добавляем вычисляемое поле total_seats
    result = []
    for r in resources:
        data = ResourceResponse.model_validate(r)
        data.total_seats = r.quantity * r.seats_per_unit
        result.append(data)
    return result


@router.post("/resources", response_model=ResourceResponse)
async def create_resource(
    data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать ресурс"""
    resource = Resource(
        business_id=current_user.business_profile.id,
        **data.model_dump()
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    
    response = ResourceResponse.model_validate(resource)
    response.total_seats = resource.quantity * resource.seats_per_unit
    return response


@router.get("/resources/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить ресурс по ID"""
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.business_id == current_user.business_profile.id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    
    response = ResourceResponse.model_validate(resource)
    response.total_seats = resource.quantity * resource.seats_per_unit
    return response


@router.put("/resources/{resource_id}", response_model=ResourceResponse)
async def update_resource(
    resource_id: int,
    data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить ресурс"""
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.business_id == current_user.business_profile.id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(resource, field, value)
    
    db.commit()
    db.refresh(resource)
    
    response = ResourceResponse.model_validate(resource)
    response.total_seats = resource.quantity * resource.seats_per_unit
    return response


@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить ресурс"""
    resource = db.query(Resource).filter(
        Resource.id == resource_id,
        Resource.business_id == current_user.business_profile.id
    ).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Ресурс не найден")
    
    db.delete(resource)
    db.commit()
    return {"message": "Ресурс удалён"}


# === INSTRUCTORS ===
@router.get("/instructors", response_model=List[InstructorResponse])
async def get_instructors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Получить инструкторов бизнеса"""
    return db.query(Instructor).filter(
        Instructor.business_id == current_user.business_profile.id
    ).order_by(Instructor.full_name).all()


@router.post("/instructors", response_model=InstructorResponse)
async def create_instructor(
    data: InstructorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Создать инструктора"""
    instructor = Instructor(
        business_id=current_user.business_profile.id,
        **data.model_dump()
    )
    db.add(instructor)
    db.commit()
    db.refresh(instructor)
    return instructor


@router.put("/instructors/{instructor_id}", response_model=InstructorResponse)
async def update_instructor(
    instructor_id: int,
    data: InstructorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Обновить инструктора"""
    instructor = db.query(Instructor).filter(
        Instructor.id == instructor_id,
        Instructor.business_id == current_user.business_profile.id
    ).first()
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Инструктор не найден")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(instructor, field, value)
    
    db.commit()
    db.refresh(instructor)
    return instructor


@router.delete("/instructors/{instructor_id}")
async def delete_instructor(
    instructor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_business_user)
):
    """Удалить инструктора"""
    instructor = db.query(Instructor).filter(
        Instructor.id == instructor_id,
        Instructor.business_id == current_user.business_profile.id
    ).first()
    
    if not instructor:
        raise HTTPException(status_code=404, detail="Инструктор не найден")
    
    db.delete(instructor)
    db.commit()
    return {"message": "Инструктор удалён"}
