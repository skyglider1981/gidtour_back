import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.user import User, BusinessProfile
from app.models.tour import Tour
from app.models.schedule import ScheduleTemplate
from datetime import time
import random

# Подключение к БД
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("Создание тестовых данных...")
    
    # 1. Проверим есть ли бизнес-пользователь
    business = db.query(BusinessProfile).first()
    if not business:
        print("❌ Нет бизнес-профилей!")
        
        # Создаем тестового пользователя
        user = User(
            email="test_business@example.com",
            password_hash="hashed_password",  # В реальности нужно хешировать
            user_type="business",
            full_name="Тестовый Бизнес"
        )
        db.add(user)
        db.flush()
        
        business = BusinessProfile(
            user_id=user.id,
            business_name="Тестовый бизнес",
            city="Москва"
        )
        db.add(business)
        db.commit()
        print(f"✅ Создан бизнес-профиль: {business.business_name}")
    
    # 2. Создадим тестовый тур если нет
    tour = db.query(Tour).filter(Tour.business_id == business.id).first()
    if not tour:
        tour = Tour(
            business_id=business.id,
            name="Тестовый тур на квадроциклах",
            description="Тестовое описание тура",
            base_price=2000,
            duration_minutes=120,
            min_participants=1,
            max_participants=5,
            difficulty_level="medium"
        )
        db.add(tour)
        db.commit()
        print(f"✅ Создан тур: {tour.name}")
    
    # 3. Создадим тестовый шаблон
    template = db.query(ScheduleTemplate).filter(ScheduleTemplate.tour_id == tour.id).first()
    if not template:
        template = ScheduleTemplate(
            tour_id=tour.id,
            week_days=[1, 2, 3, 4, 5],  # Пн-Пт
            start_time=time(9, 0),
            end_time=time(18, 0),
            slot_duration_minutes=60,
            break_duration_minutes=30,
            is_active=True
        )
        db.add(template)
        db.commit()
        print(f"✅ Создан шаблон расписания для тура '{tour.name}'")
        print(f"   ID шаблона: {template.id}")
        print(f"   Дни: {template.week_days}")
        print(f"   Время: {template.start_time} - {template.end_time}")
    
    # 4. Проверим итог
    templates_count = db.query(ScheduleTemplate).count()
    tours_count = db.query(Tour).count()
    
    print(f"\n✅ Итог:")
    print(f"   Бизнес-профилей: {db.query(BusinessProfile).count()}")
    print(f"   Туров: {tours_count}")
    print(f"   Шаблонов расписания: {templates_count}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
    db.rollback()
    import traceback
    traceback.print_exc()
finally:
    db.close()
