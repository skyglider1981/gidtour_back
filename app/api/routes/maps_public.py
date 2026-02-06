"""
Публичный роутер для работы с Яндекс Картами (без авторизации)
Используется в модалках где пользователь ещё не полностью авторизован
"""
from fastapi import APIRouter, HTTPException, Query
from decimal import Decimal
from app.services.yandex_maps import yandex_maps_service

router = APIRouter(tags=["Карты (публичный доступ)"])


@router.get("/maps/public/geocode")
async def public_geocode_address(
    address: str = Query(..., description="Адрес для геокодирования"),
    limit: int = Query(5, description="Максимальное количество результатов", ge=1, le=10)
):
    """
    Публичное геокодирование адреса в координаты
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


@router.get("/maps/public/reverse-geocode")
async def public_reverse_geocode(
    lat: Decimal = Query(..., description="Широта"),
    lon: Decimal = Query(..., description="Долгота")
):
    """
    Публичное обратное геокодирование: координаты в адрес
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
