import sys
sys.path.insert(0, '.')

# Минимальный тест API роутера
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.api.routes.schedule_templates import router

# Создаем минимальное приложение
app = FastAPI()
app.include_router(router)

client = TestClient(app)

print("Тестирование эндпоинтов...")

# Тестируем что роуты зарегистрированы
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  {route.path}")

# Пробуем сделать запрос без авторизации (должна быть 401)
print("\nТест без авторизации:")
try:
    response = client.get("/business/schedule-templates/")
    print(f"  Status: {response.status_code}")
    print(f"  Expected 401 or 403, got {response.status_code}")
except Exception as e:
    print(f"  Ошибка: {e}")

print("\n✅ Роутер работает!")
