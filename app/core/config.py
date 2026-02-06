from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 часа

    # App
    APP_NAME: str = "GidTur API"
    DEBUG: bool = True

    # Yandex Maps API
    YANDEX_MAPS_API_KEY: str = Field(default="", env="YANDEX_MAPS_API_KEY")

    class Config:
        env_file = ".env"

settings = Settings()
