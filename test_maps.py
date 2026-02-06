#!/usr/bin/env python3
"""
Дебаггер для проверки эндпоинтов schedule-templates
Проверяет: доступность, схему данных, ошибки
"""

import requests
import json
import sys
from typing import Dict, Any

# Конфигурация
BASE_URL = "http://93.183.104.20:8000/api"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzY5NzY1NDIzfQ.o6sCl-hjYFIS4MIBOLN7Y7GyJIuhQ9Oj7N4jc0-r3ew"  # Замени на реальный токен

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def print_section(title: str):
    """Красивый вывод секции"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_endpoint(method: str, endpoint: str, data: Dict = None, params: Dict = None):
    """Тестирует эндпоинт"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🔍 Тест: {method.upper()} {endpoint}")
    print(f"   URL: {url}")
    
    if data:
        print(f"   Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
    if params:
        print(f"   Параметры: {params}")
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method.lower() == "post":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        elif method.lower() == "put":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            print(f"   ❌ Неподдерживаемый метод: {method}")
            return None
        
        print(f"   📊 Статус: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"   ❌ Ошибка {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"   📝 Ответ: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return response_data
        except:
            print(f"   📝 Ответ (текст): {response.text[:500]}")
            return response.text
            
    except Exception as e:
        print(f"   💥 Исключение: {e}")
        return None

def test_schedule_templates_flow():
    """Тестирует полный цикл работы с шаблонами"""
    
    print_section("1. ПОЛУЧЕНИЕ ТЕКУЩИХ ТУРОВ")
    tours = test_endpoint("GET", "/business/tours")
    
    if not tours or not isinstance(tours, list) or len(tours) == 0:
        print("❌ Нет доступных туров для теста")
        return
    
    tour_id = tours[0].get('id')
    print(f"\n✅ Выбран тур ID: {tour_id} - {tours[0].get('name', 'Без названия')}")
    
    print_section("2. ПОЛУЧЕНИЕ ТЕКУЩИХ ШАБЛОНОВ")
    templates = test_endpoint("GET", "/business/schedule-templates/", params={"tour_id": tour_id})
    
    print_section("3. ТЕСТ 1: СОЗДАНИЕ SCHEDULE-TEMPLATE (шаблон)")
    # Данные для ScheduleTemplate
    template_data = {
        "tour_id": tour_id,
        "week_days": [1, 2, 3, 4, 5],  # Пн-Пт
        "start_time": "09:00:00",
        "end_time": "18:00:00",
        "slot_duration_minutes": 60,
        "break_duration_minutes": 0,
        "is_active": True
    }
    
    created_template = test_endpoint("POST", "/business/schedule-templates/", data=template_data)
    
    if created_template and isinstance(created_template, dict) and 'id' in created_template:
        template_id = created_template['id']
        
        print_section("4. ТЕСТ 2: ОБНОВЛЕНИЕ ШАБЛОНА")
        update_data = template_data.copy()
        update_data["week_days"] = [1, 3, 5]  # Только Пн, Ср, Пт
        test_endpoint("PUT", f"/business/schedule-templates/{template_id}", data=update_data)
        
        print_section("5. ТЕСТ 3: PREVIEW ГЕНЕРАЦИИ")
        test_endpoint("GET", f"/business/schedule-templates/{template_id}/preview", 
                     params={"start_date": "2024-01-15", "end_date": "2024-01-31"})
        
        print_section("6. ТЕСТ 4: УДАЛЕНИЕ ШАБЛОНА")
        test_endpoint("DELETE", f"/business/schedule-templates/{template_id}")
    
    print_section("7. ТЕСТ 5: СОЗДАНИЕ TOUR-SCHEDULE (конкретный слот)")
    # Данные для TourSchedule (это ДРУГОЙ эндпоинт!)
    schedule_data = {
        "date": "2024-01-15",
        "start_time": "10:00:00",
        "end_time": "12:00:00",
        "available_slots": 10,
        "price_override": 1500.0
    }
    
    test_endpoint("POST", f"/business/tours/{tour_id}/schedules", data=schedule_data)
    
    print_section("8. ПРОВЕРКА СХЕМ ДАННЫХ")
    check_schemas()

def check_schemas():
    """Проверяет схемы данных через OpenAPI"""
    print("\n📋 Получение OpenAPI схемы...")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi = response.json()
            
            # Ищем схему ScheduleTemplate
            print("\n🔍 Поиск ScheduleTemplateCreate схемы...")
            schemas = openapi.get('components', {}).get('schemas', {})
            
            for schema_name, schema in schemas.items():
                if 'scheduletemplate' in schema_name.lower() and 'create' in schema_name.lower():
                    print(f"\n✅ Найдена схема: {schema_name}")
                    print(f"   Обязательные поля: {schema.get('required', [])}")
                    print(f"   Свойства: {json.dumps(schema.get('properties', {}), indent=2, ensure_ascii=False)}")
                
                if 'tourschedule' in schema_name.lower() and 'create' in schema_name.lower():
                    print(f"\n✅ Найдена схема: {schema_name} (TourSchedule)")
                    print(f"   Обязательные поля: {schema.get('required', [])}")
                    print(f"   Свойства: {json.dumps(schema.get('properties', {}), indent=2, ensure_ascii=False)}")
            
    except Exception as e:
        print(f"❌ Ошибка получения схемы: {e}")

def test_specific_problem():
    """Тестирует конкретную проблему с 422 ошибкой"""
    print_section("ТЕСТИРОВАНИЕ 422 ОШИБКИ")
    
    # Данные которые вызывали 422
    problem_data = {
        "tour_id": 28,
        "start_time": "09:00:00",
        "end_time": "18:00:00",
        "week_days": [1, 2, 3, 4, 5],
        "duration_minutes": 60,
        "break_between_tours": 0,
        "is_active": True,
        "max_participants": 10,
        "price": 1000,
        "guide_id": None
    }
    
    print("\n🔍 Тестирую данные из фронтенда:")
    print(json.dumps(problem_data, indent=2, ensure_ascii=False))
    
    print("\n📤 Отправляю в /business/schedule-templates/")
    test_endpoint("POST", "/business/schedule-templates/", data=problem_data)
    
    print("\n📤 Отправляю в /business/tours/28/schedules")
    problem_data_with_date = problem_data.copy()
    problem_data_with_date["date"] = "2024-01-15"
    problem_data_with_date["available_slots"] = 10
    test_endpoint("POST", "/business/tours/28/schedules", data=problem_data_with_date)

if __name__ == "__main__":
    print("🚀 ДЕБАГГЕР БЭКЕНДА ДЛЯ SCHEDULE-TEMPLATES")
    print("="*60)
    
    # Запрос токена если нет
    if "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in TOKEN:
        print("⚠️  Замените TOKEN на реальный!")
        print("   Получите из localStorage браузера: localStorage.getItem('token')")
        sys.exit(1)
    
    # Проверка доступности API
    print("🔗 Проверка доступности API...")
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code == 200:
            print("✅ API доступен")
        else:
            print(f"⚠️  API отвечает с кодом: {health.status_code}")
    except:
        print("❌ API недоступен")
    
    # Меню
    print("\nВыберите тест:")
    print("1. Полный цикл работы с шаблонами")
    print("2. Тестирование 422 ошибки")
    print("3. Проверка всех эндпоинтов")
    print("4. Проверка OpenAPI схем")
    
    choice = input("\nВведите номер (1-4): ").strip()
    
    if choice == "1":
        test_schedule_templates_flow()
    elif choice == "2":
        test_specific_problem()
    elif choice == "3":
        test_all_endpoints()
    elif choice == "4":
        check_schemas()
    else:
        print("❌ Неверный выбор")
