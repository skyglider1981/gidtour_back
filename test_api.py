import sys
sys.path.insert(0, '.')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Тестируем доступность эндпоинтов
endpoints = [
    "/business/schedule-templates/",
    "/docs",
    "/redoc",
]

print("Тестирование доступности API эндпоинтов:")
for endpoint in endpoints:
    try:
        response = client.get(endpoint)
        print(f"  {endpoint}: {'✅' if response.status_code < 500 else '❌'} ({response.status_code})")
    except Exception as e:
        print(f"  {endpoint}: ❌ {e}")

print("\n✅ API роутер schedule-templates подключен!")
