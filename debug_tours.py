#!/usr/bin/env python3
"""
Простой скрипт для тестирования API создания туров.
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"  # или твой IP

def get_token():
    """Получаем токен из .env или вводим вручную"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("TEST_TOKEN")
        if token:
            return token
    except:
        pass
    
    # Или попросим ввести
    print("Введите JWT токен (из фронтенда localStorage.getItem('token')): ")
    token = input().strip()
    return token

def test_api(token):
    """Тестируем API с реальным токеном"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("=" * 60)
    print("ТЕСТ СОЗДАНИЯ ТУРА")
    print("=" * 60)
    
    # 1. Проверяем доступ к профилю
    print("\n1. Проверяем доступ к профилю...")
    response = requests.get(f"{BASE_URL}/api/business/profile", headers=headers)
    print(f"   GET /api/business/profile: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print(f"   ✅ Успех! Business ID: {profile.get('id')}")
    else:
        print(f"   ❌ Ошибка: {response.json()}")
        return False
    
    # 2. Получаем существующие активности
    print("\n2. Получаем активности...")
    response = requests.get(f"{BASE_URL}/api/business/activities", headers=headers)
    print(f"   GET /api/business/activities: {response.status_code}")
    if response.status_code == 200:
        activities = response.json()
        print(f"   ✅ Найдено активностей: {len(activities)}")
        activity_id = activities[0]['id'] if activities else None
    else:
        print(f"   ❌ Ошибка: {response.json()}")
        activity_id = None
    
    # 3. Получаем существующие ресурсы
    print("\n3. Получаем ресурсы...")
    response = requests.get(f"{BASE_URL}/api/business/resources", headers=headers)
    print(f"   GET /api/business/resources: {response.status_code}")
    if response.status_code == 200:
        resources = response.json()
        print(f"   ✅ Найдено ресурсов: {len(resources)}")
        resource_id = resources[0]['id'] if resources else None
    else:
        print(f"   ❌ Ошибка: {response.json()}")
        resource_id = None
    
    # 4. Пробуем создать простой тур
    print("\n4. Пробуем создать простой тур...")
    tour_data = {
        "name": "Тестовый тур из скрипта",
        "description": "Создан автоматически для тестирования",
        "base_price": 2500.50,
        "min_participants": 1,
        "duration_minutes": 60,
    }
    
    # Добавляем активности и ресурсы если они есть
    if activity_id:
        tour_data["activities"] = [{"activity_id": activity_id, "order_index": 0}]
    if resource_id:
        tour_data["resources"] = [{"resource_id": resource_id, "quantity_needed": 1}]
    
    print(f"   Отправляемые данные: {json.dumps(tour_data, indent=2, ensure_ascii=False)}")
    
    response = requests.post(f"{BASE_URL}/api/business/tours", 
                           json=tour_data, 
                           headers=headers)
    
    print(f"   POST /api/business/tours: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ УСПЕХ! Тур создан!")
        print(f"   ID тура: {result.get('id')}")
        print(f"   Название: {result.get('name')}")
        print(f"   Цена: {result.get('base_price')}")
        return True
    else:
        print(f"   ❌ ОШИБКА!")
        print(f"   Код: {response.status_code}")
        print(f"   Ответ: {response.text}")
        return False

if __name__ == "__main__":
    print("Тестирование API создания туров")
    print(f"Базовый URL: {BASE_URL}")
    
    token = get_token()
    if not token:
        print("❌ Токен не получен")
        sys.exit(1)
    
    print(f"Токен: {token[:50]}...")
    
    success = test_api(token)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ ТЕСТ ПРОВАЛЕН")
        print("=" * 60)
        sys.exit(1)