import sys
sys.path.insert(0, '.')

print("Финальная проверка...")

try:
    # 1. Проверяем схемы
    from app.schemas.schedule import ScheduleTemplateCreate
    print("✅ Схемы schedule импортированы")
    
    # 2. Проверяем модели
    from app.models.schedule import ScheduleTemplate
    from app.models.tour import Tour
    print("✅ Модели импортированы")
    
    # 3. Проверяем сервис
    from app.services.schedule_generator import ScheduleGenerator
    print("✅ ScheduleGenerator импортирован")
    
    # 4. Проверяем API роутер
    from app.api.routes.schedule_templates import router
    print("✅ Router schedule_templates импортирован")
    
    print(f"\n✅ Все импорты успешны!")
    print(f"✅ Роутер имеет {len(router.routes)} эндпоинтов")
    
    # Покажем эндпоинты
    print("\nЭндпоинты:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods:20} {route.path}")
    
except Exception as e:
    print(f"\n❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
