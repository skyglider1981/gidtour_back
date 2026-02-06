import sys
sys.path.insert(0, '.')

try:
    from app.models import *
    print("✅ Все модели успешно импортированы!")
    print("\nСписок моделей:")
    models = [
        "User", "BusinessProfile", "CustomerProfile", "Booking",
        "ActivityType", "Location", "Activity", "LocationActivity",
        "ResourceType", "Resource", "Instructor", "ScheduleResource", "ActivityResourceType",
        "Tour", "TourActivity", "TourResource", "TourInstructor", "TourLocation", "TourSchedule",
        "ScheduleTemplate"
    ]
    for model in models:
        try:
            eval(model)
            print(f"  ✅ {model}")
        except:
            print(f"  ❌ {model} (не найден)")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    import traceback
    traceback.print_exc()
