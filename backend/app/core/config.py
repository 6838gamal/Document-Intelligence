from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "Document Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.environ.get("SESSION_SECRET", "fallback-secret-key-for-dev-only")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://masih-almustanadat-api.onrender.com")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
