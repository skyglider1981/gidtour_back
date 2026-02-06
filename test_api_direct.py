import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User
from app.models.tour import Tour
from app.models.schedule import ScheduleTemplate
from datetime import time

# Подключение к БД
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== Тестирование БД и прав ===")
    
    # 1. Проверим что можем читать schedule_templates
    templates_count = db.query(ScheduleTemplate).count()
    print(f"1. Записей в schedule_templates: {templates_count}")
    
    # 2. Проверим наличие туров
    test_tour = db.query(Tour).first()
    if test_tour:
        print(f"2. Найден тур для теста: {test_tour.name} (ID: {test_tour.id})")
        print(f"   Business ID: {test_tour.business_id}")
        
        # 3. Проверим что можем создавать запись
        test_template = ScheduleTemplate(
            tour_id=test_tour.id,
            week_days=[1, 2, 3, 4, 5],
            start_time=time(9, 0),
            end_time=time(18, 0),
            slot_duration_minutes=60,
            break_duration_minutes=30,
            is_active=True
        )
        
        db.add(test_template)
        db.flush()  # Пробуем сохранить без коммита
        print(f"3. Тестовый шаблон создан (ID: {test_template.id})")
        
        # Откатываем чтобы не оставлять тестовые данные
        db.rollback()
        print("4. Rollback выполнен (тестовые данные не сохранены)")
    else:
        print("2. ❌ Нет туров для теста!")
        # Создадим тестовый тур если нужно
        from app.models.user import BusinessProfile
        business = db.query(BusinessProfile).first()
        if business:
            test_tour = Tour(
                business_id=business.id,
                name="Тестовый тур для расписаний",
                base_price=1000,
                duration_minutes=60
            )
            db.add(test_tour)
            db.commit()
            print(f"   Создан тестовый тур (ID: {test_tour.id})")
    
    # 5. Проверим соединение с таблицей tours
    tours_count = db.query(Tour).count()
    print(f"5. Всего туров в БД: {tours_count}")
    
    # 6. Проверим JOIN запрос (как в API)
    from sqlalchemy.orm import joinedload
    templates_with_tours = db.query(ScheduleTemplate)\
        .join(Tour)\
        .options(joinedload(ScheduleTemplate.tour))\
        .limit(5)\
        .all()
    
    print(f"6. JOIN запрос выполнен успешно, найдено: {len(templates_with_tours)}")
    
    # 7. Проверим реальные данные
    print("\n7. Существующие шаблоны:")
    existing_templates = db.query(ScheduleTemplate).all()
    for t in existing_templates:
        print(f"   - ID: {t.id}, Тур ID: {t.tour_id}, Дни: {t.week_days}")
    
    print("\n✅ Тест БД пройден успешно!")
    
except Exception as e:
    print(f"\n❌ Ошибка при тесте БД: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
