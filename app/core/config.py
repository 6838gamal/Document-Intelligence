from pydantic_settings import BaseSettings
import os
import secrets
import pathlib


def _get_secret_key() -> str:
    if os.environ.get("SESSION_SECRET"):
        return os.environ["SESSION_SECRET"]
    key_file = pathlib.Path(".secret_key")
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_hex(32)
    key_file.write_text(key)
    return key


class Settings(BaseSettings):
    APP_NAME: str = "Document Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.environ.get("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = _get_secret_key()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    API_BASE_URL: str = os.environ.get("API_BASE_URL", "")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
