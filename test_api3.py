import sys
sys.path.insert(0, '.')

print("Проверка всех импортов...")

try:
    # 1. Проверяем модели
    from app.models.schedule import ScheduleTemplate
    print("✅ ScheduleTemplate импортирован")
    
    from app.models.tour import Tour
    print("✅ Tour импортирован")
    
    # 2. Проверяем схемы
    from app.schemas.schedule import ScheduleTemplateCreate, ScheduleTemplateResponse
    print("✅ Схемы schedule импортированы")
    
    # 3. Проверяем сервис
    from app.services.schedule_generator import ScheduleGenerator
    print("✅ ScheduleGenerator импортирован")
    
    # 4. Проверяем API роутер
    from app.api.routes.schedule_templates import router
    print("✅ Router schedule_templates импортирован")
    
    print("\n" + "="*50)
    print("✅ ВСЕ ИМПОРТЫ УСПЕШНЫ!")
    print("="*50)
    
    # Дополнительная информация
    print(f"\nЭндпоинты роутера ({len(router.routes)} шт):")
    for route in router.routes:
        methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'UNKNOWN'
        print(f"  {methods:15} {route.path}")
    
except Exception as e:
    print(f"\n❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
