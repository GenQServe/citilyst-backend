from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str
    PYTHONUNBUFFERED: int
    ENVIRONTMENT: str
    REDIS_URL: str
    DATABASE_URL: str
    PGDATABASE: str
    PGHOST: str
    PGPORT: int
    PGUSER: str
    PGPASSWORD: str
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    JWT_SECRET: str
    MAIL_USER_NAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    ONESIGNAL_APP_ID: str
    ONESIGNAL_API_KEY: str
    ONESIGNAL_OTP_TEMPLATE_ID: str

    class Config:
        env_file = ".env"


settings = Settings()
