from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.auth import router as auth_router
from app.api.routes.business import router as business_router
from app.api.routes.upload import router as upload_router
from app.api.routes.maps import router as maps_router
from app.api.routes.maps_public import router as maps_public_router
from app.api.routes.resources import router as resources_router
from app.api.routes.tours import router as tours_router
from app.api.routes.schedule_templates import router as schedule_templates_router
from app.api.routes.bookings_api import router as bookings_router
from app.api.routes.public_api import router as public_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.customer_api import router as customer_router  # ЛК туриста
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="API для туристического сервиса бронирования активностей и туров",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth_router, prefix="/api")
app.include_router(business_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(maps_router, prefix="/api")
app.include_router(maps_public_router, prefix="/api")
app.include_router(resources_router, prefix="/api")
app.include_router(tours_router, prefix="/api")
app.include_router(schedule_templates_router, prefix="/api")
app.include_router(bookings_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(reviews_router, prefix="/api")
app.include_router(customer_router, prefix="/api")  # ЛК туриста

@app.get("/")
async def root():
    return {
        "message": "GidTur API работает!",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
