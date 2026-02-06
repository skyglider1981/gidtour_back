import sys
sys.path.insert(0, '.')

try:
    # Импортируем основные модели
    from app.models.schedule import ScheduleTemplate
    from app.models.resource import ScheduleResource
    from app.models.tour import Tour, TourSchedule
    
    print("✅ ScheduleTemplate импортирована успешно")
    print("✅ ScheduleResource импортирована успешно")
    
    # Проверим что ScheduleTemplate имеет все поля
    template = ScheduleTemplate
    print(f"\nПоля ScheduleTemplate: {[c.key for c in template.__table__.columns]}")
    
    # Проверим что TourSchedule имеет schedule_template_id
    schedule = TourSchedule
    columns = [c.key for c in schedule.__table__.columns]
    print(f"\nПоля TourSchedule: {columns}")
    
    if 'schedule_template_id' in columns:
        print("✅ TourSchedule имеет schedule_template_id")
    else:
        print("❌ TourSchedule НЕ ИМЕЕТ schedule_template_id!")
    
    if 'schedule_templates' in dir(Tour):
        print("✅ Tour имеет связь schedule_templates")
    else:
        print("❌ Tour НЕ ИМЕЕТ связь schedule_templates")
        
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
