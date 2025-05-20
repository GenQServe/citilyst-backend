import logging
import os
import sys
from pydantic_settings import BaseSettings
from pydantic import EmailStr, SecretStr

from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: Optional[str] = None
    PYTHONUNBUFFERED: Optional[int] = None
    ENVIRONTMENT: str = "development"
    REDIS_URL: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    PGDATABASE: Optional[str] = None
    PGHOST: Optional[str] = None
    PGPORT: Optional[int] = None
    PGUSER: Optional[str] = None
    PGPASSWORD: Optional[str] = None
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    ALLOWED_ORIGINS: Optional[str] = None
    MAIL_USER_NAME: Optional[str] = None
    MAIL_PASSWORD: Optional[SecretStr] = None
    MAIL_FROM: Optional[str] = None
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None
    MAIL_PORT: Optional[int] = None
    MAIL_SERVER: Optional[str] = None
    ONESIGNAL_APP_ID: Optional[str] = None
    ONESIGNAL_API_KEY: Optional[str] = None
    ONESIGNAL_OTP_TEMPLATE_ID: Optional[str] = None
    N8N_API_URL: Optional[str] = None

    def is_production(self) -> bool:
        env = self.ENVIRONTMENT.lower()
        logging.info(f"[ENV] Environment: {env}")
        return env == "production" or env == "prod" or "--production" in sys.argv

    def is_development(self) -> bool:
        return not self.is_production()

    class Config:
        env_file = ".env"


settings = Settings()
