import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    WEBHOOK_SECRET: str
    DATABASE_URL: str
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
