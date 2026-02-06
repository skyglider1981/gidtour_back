import sys
sys.path.insert(0, '.')

from app.core.config import settings
print("Конфигурация БД:")
print(f"DATABASE_URL: {settings.DATABASE_URL}")
print(f"SQLALCHEMY_DATABASE_URL: {settings.SQLALCHEMY_DATABASE_URL if hasattr(settings, 'SQLALCHEMY_DATABASE_URL') else 'Не найден'}")

# Проверим подключение
from sqlalchemy import create_engine, text
try:
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_user, current_database()"))
        user, db = result.fetchone()
        print(f"Подключение успешно: пользователь={user}, БД={db}")
        
        # Проверим таблицы
        result = conn.execute(text("""
            SELECT table_name, table_owner 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('schedule_templates', 'tours', 'business_profiles')
            ORDER BY table_name
        """))
        
        print("\nПроверка таблиц:")
        tables = result.fetchall()
        for table in tables:
            print(f"  ✅ {table[0]} (владелец: {table[1]})")
        
        if not tables:
            print("  ❌ Таблицы не найдены!")
            
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
