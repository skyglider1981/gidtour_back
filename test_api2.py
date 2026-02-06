import sys
sys.path.insert(0, '.')

print("Проверка импортов...")

try:
    # Проверяем импорт моделей
    from app.models.schedule import ScheduleTemplate
    print("✅ ScheduleTemplate импортирован")
    
    from app.models.tour import Tour
    print("✅ Tour импортирован")
    
    # Проверяем импорт API
    from app.api.routes.schedule_templates import router
    print("✅ Router schedule_templates импортирован")
    
    # Проверяем импорт сервиса
    from app.services.schedule_generator import ScheduleGenerator
    print("✅ ScheduleGenerator импортирован")
    
    print("\n✅ Все импорты успешны!")
    
    # Проверим эндпоинты роутера
    print(f"\nЭндпоинты роутера:")
    for route in router.routes:
        print(f"  {route.methods} {route.path}")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
