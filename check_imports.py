import sys
sys.path.insert(0, '.')

print("Проверка импортов для schedule_templates.py...")

try:
    # Импорты из models
    from app.models.user import User
    print("✅ from app.models.user import User")
    
    from app.models.tour import Tour, TourSchedule
    print("✅ from app.models.tour import Tour, TourSchedule")
    
    from app.models.schedule import ScheduleTemplate
    print("✅ from app.models.schedule import ScheduleTemplate")
    
    # Импорты из schemas
    from app.schemas.schedule import (
        ScheduleTemplateCreate, 
        ScheduleTemplateUpdate,
        ScheduleTemplateResponse,
        ScheduleGenerateRequest,
        GeneratedScheduleInfo
    )
    print("✅ from app.schemas.schedule import ...")
    
    # Импорты из services
    from app.services.schedule_generator import ScheduleGenerator
    print("✅ from app.services.schedule_generator import ScheduleGenerator")
    
    # Импорты из core
    from app.core.database import get_db
    print("✅ from app.core.database import get_db")
    
    from app.api.deps import get_current_business_user
    print("✅ from app.api.deps import get_current_business_user")
    
    print("\n✅ Все импорты успешны!")
    
except ImportError as e:
    print(f"\n❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
