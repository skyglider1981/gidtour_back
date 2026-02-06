import sys
sys.path.insert(0, '.')

print("Проверка доступных моделей...")

try:
    # Импортируем то что точно есть
    from app.models import __all__ as all_models
    print("Доступные модели:", all_models)
    
    # Проверим каждую
    for model_name in all_models:
        try:
            exec(f"from app.models import {model_name}")
            print(f"✅ {model_name}")
        except ImportError as e:
            print(f"❌ {model_name}: {e}")
    
except Exception as e:
    print(f"Ошибка: {e}")
    import traceback
    traceback.print_exc()
