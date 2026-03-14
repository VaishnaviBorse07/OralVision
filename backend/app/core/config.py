from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))


class Settings(BaseSettings):
    database_url: str = (
        "postgresql://oralvision:oralvision123@localhost:5432/oralvision"
    )
    jwt_secret: str = "oralvision-super-secret-jwt-key-2024"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    n8n_webhook_url: str = ""
    cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    )
    app_env: str = "development"
    google_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache()
def get_settings():
    return Settings()
