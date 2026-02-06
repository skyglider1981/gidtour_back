"""
Роутер для работы с Яндекс Картами
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from decimal import Decimal
from app.api.deps import get_current_user
from app.services.yandex_maps import yandex_maps_service

router = APIRouter()


@router.get("/maps/geocode")
async def geocode_address(
    address: str = Query(..., description="Адрес для геокодирования"),
    limit: int = Query(5, description="Максимальное количество результатов", ge=1, le=10),
    current_user = Depends(get_current_user)
):
    """
    Геокодирование адреса в координаты
    """
    try:
        results = await yandex_maps_service.geocode(address, limit)
        return {
            "success": True,
            "count": len(results),
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/maps/reverse-geocode")
async def reverse_geocode(
    lat: Decimal = Query(..., description="Широта"),
    lon: Decimal = Query(..., description="Долгота"),
    current_user = Depends(get_current_user)
):
    """
    Обратное геокодирование: координаты в адрес
    """
    try:
        result = await yandex_maps_service.reverse_geocode(lat, lon)
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/maps/suggest")
async def suggest_address(
    query: str = Query(..., description="Текст для подсказки адреса"),
    limit: int = Query(5, description="Максимальное количество подсказок", ge=1, le=10),
    current_user = Depends(get_current_user)
):
    """
    Подсказки адресов
    """
    try:
        suggestions = await yandex_maps_service.suggest_address(query, limit)
        return {
            "success": True,
            "count": len(suggestions),
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
