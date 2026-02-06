"""
Сервис для работы с Яндекс Картами API
"""
import httpx
import os
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException
from decimal import Decimal
import logging
from app.core.config import settings  # Добавляем импорт настроек

logger = logging.getLogger(__name__)


class YandexMapsService:
    def __init__(self):
        # Берем ключ из настроек
        self.api_key = settings.YANDEX_MAPS_API_KEY
        self.geocode_url = "https://geocode-maps.yandex.ru/1.x/"
        self.reverse_geocode_url = "https://geocode-maps.yandex.ru/1.x/"
        
        if not self.api_key:
            logger.warning("YANDEX_MAPS_API_KEY not set in settings. Maps functionality will not work.")
    
    async def geocode(self, address: str, limit: int = 5) -> List[Dict]:
        """
        Геокодирование адреса в координаты
        
        Args:
            address: Адрес для поиска
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных мест
        """
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="Yandex Maps API key not configured in application settings"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.geocode_url,
                    params={
                        "apikey": self.api_key,
                        "geocode": address,
                        "format": "json",
                        "lang": "ru_RU",
                        "results": limit
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Geocoding failed: {response.status_code}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="Geocoding service error"
                    )
                
                data = response.json()
                return self._parse_geocoding_results(data)
                
        except httpx.RequestError as e:
            logger.error(f"Geocoding request error: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Geocoding service unavailable"
            )
    
    async def reverse_geocode(self, lat: Decimal, lon: Decimal) -> Dict:
        """
        Обратное геокодирование: координаты в адрес
        
        Args:
            lat: Широта
            lon: Долгота
            
        Returns:
            Информация об адресе
        """
        if not self.api_key:
            raise HTTPException(
                status_code=500,
                detail="Yandex Maps API key not configured in application settings"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.reverse_geocode_url,
                    params={
                        "apikey": self.api_key,
                        "geocode": f"{float(lon)},{float(lat)}",
                        "format": "json",
                        "lang": "ru_RU"
                    }
                )
                
                data = response.json()
                return self._parse_reverse_geocoding_result(data, float(lat), float(lon))
                
        except Exception as e:
            logger.error(f"Reverse geocoding error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )
    
    def _parse_geocoding_results(self, data: Dict) -> List[Dict]:
        """Парсинг результатов геокодирования"""
        features = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
        
        results = []
        for feature in features:
            geo_object = feature.get("GeoObject", {})
            name = geo_object.get("name", "")
            description = geo_object.get("description", "")
            pos = geo_object.get("Point", {}).get("pos", "")
            
            if pos:
                # Координаты в формате "долгота широта"
                lon, lat = map(float, pos.split())
                
                results.append({
                    "name": name,
                    "description": description,
                    "address": f"{name}, {description}" if description else name,
                    "coordinates": {"lat": lat, "lon": lon}
                })
        
        return results
    
    def _parse_reverse_geocoding_result(self, data: Dict, lat: float, lon: float) -> Dict:
        """Парсинг результатов обратного геокодирования"""
        features = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])
        
        if features:
            geo_object = features[0].get("GeoObject", {})
            name = geo_object.get("name", "")
            description = geo_object.get("description", "")
            
            return {
                "address": name,
                "description": description,
                "coordinates": {"lat": lat, "lon": lon},
                "full_address": f"{name}, {description}" if description else name
            }
        
        return {
            "address": "Адрес не найден",
            "coordinates": {"lat": lat, "lon": lon},
            "full_address": "Адрес не найден"
        }


# Глобальный экземпляр сервиса
yandex_maps_service = YandexMapsService()
