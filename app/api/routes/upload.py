import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Загрузка файлов"])

UPLOAD_DIR = "/opt/gidtur_back/uploads/photos"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Создаём папку если нет
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_extension(filename: str) -> str:
    if not filename or "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...)):
    """Загрузка одного фото"""
    
    logger.info(f"Upload attempt: filename={file.filename}, content_type={file.content_type}")
    
    # Проверяем что файл есть
    if not file.filename:
        raise HTTPException(400, "Файл не выбран")
    
    # Проверяем расширение
    ext = get_extension(file.filename)
    logger.info(f"Extension: {ext}")
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Недопустимый формат '{ext}'. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Читаем содержимое
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(400, f"Ошибка чтения файла: {str(e)}")
    
    logger.info(f"File size: {len(contents)} bytes")
    
    # Проверяем размер
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(400, "Файл слишком большой. Максимум 10MB")
    
    if len(contents) == 0:
        raise HTTPException(400, "Файл пустой")
    
    # Генерируем уникальное имя
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    # Сохраняем
    try:
        with open(filepath, "wb") as f:
            f.write(contents)
        logger.info(f"File saved: {filepath}")
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(500, f"Ошибка сохранения файла: {str(e)}")
    
    return {
        "filename": filename,
        "url": f"/api/upload/photos/{filename}",
        "size": len(contents)
    }


@router.post("/photos")
async def upload_photos(files: List[UploadFile] = File(...)):
    """Загрузка нескольких фото"""
    results = []
    
    for file in files:
        ext = get_extension(file.filename)
        if ext not in ALLOWED_EXTENSIONS:
            continue
        
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE or len(contents) == 0:
            continue
        
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as f:
            f.write(contents)
        
        results.append({
            "filename": filename,
            "url": f"/api/upload/photos/{filename}",
            "size": len(contents)
        })
    
    return {"uploaded": results, "count": len(results)}


@router.get("/photos/{filename}")
async def get_photo(filename: str):
    """Получение фото по имени"""
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(404, "Файл не найден")
    
    return FileResponse(filepath)
