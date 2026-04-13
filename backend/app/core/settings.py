from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(ROOT_DIR / ".env"), env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Plataforma Jurídica Multiárea"
    APP_ENV: str = "dev"
    LOG_LEVEL: str = "INFO"
    AUDIT_EXCLUDE_PATHS: str = "/api/v1/health,/docs,/openapi.json"
    LOG_HTTP: bool = True
    AUTH_ENABLED: bool = True
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    ADMIN_SEED_TOKEN: str = "CHANGE_ME_SEED_TOKEN"
    ALLOW_SEED_ADMIN: bool = False
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://ia_app:ia_app_pass@127.0.0.1:55432/ia_trabalhista"

    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-5-mini"
    LLM_TIMEOUT_SECONDS: int = 90
    LLM_ANALYSIS_ENABLED: bool = False
    LLM_BASE_URL: str | None = None

settings = Settings()
