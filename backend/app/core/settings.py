from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
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
    AUTH_PROTECT_DOCS: bool = False
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    ADMIN_SEED_TOKEN: str = "CHANGE_ME_SEED_TOKEN"
    ALLOW_SEED_ADMIN: bool = False
    CORS_ALLOW_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:4173,http://127.0.0.1:4173"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "postgresql+psycopg2://ia_app:ia_app_pass@127.0.0.1:55432/ia_trabalhista"

    PLAN_BASIC_ACTIVE_CASES_LIMIT: int = Field(50, validation_alias=AliasChoices("PLAN_BASIC_ACTIVE_CASES_LIMIT", "PLAN_BASIC_CASES_PER_MONTH"))
    PLAN_BASIC_CASE_RECORDS_LIMIT: int = 200
    PLAN_BASIC_AI_ANALYSES_PER_MONTH: int = 20

    PLAN_PRO_ACTIVE_CASES_LIMIT: int = Field(200, validation_alias=AliasChoices("PLAN_PRO_ACTIVE_CASES_LIMIT", "PLAN_PRO_CASES_PER_MONTH"))
    PLAN_PRO_CASE_RECORDS_LIMIT: int = 1000
    PLAN_PRO_AI_ANALYSES_PER_MONTH: int = 100

    PLAN_OFFICE_ACTIVE_CASES_LIMIT: int = Field(1000, validation_alias=AliasChoices("PLAN_OFFICE_ACTIVE_CASES_LIMIT", "PLAN_OFFICE_CASES_PER_MONTH"))
    PLAN_OFFICE_CASE_RECORDS_LIMIT: int = 10000
    PLAN_OFFICE_AI_ANALYSES_PER_MONTH: int = 500

    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-5-mini"
    LLM_TIMEOUT_SECONDS: int = 90
    LLM_ANALYSIS_ENABLED: bool = False
    LLM_BASE_URL: str | None = None

    PAYMENT_PROVIDER: str = "manual"
    PAYMENT_CHECKOUT_BASE_URL: str = ""

    ASAAS_API_KEY: str = ""
    ASAAS_BASE_URL: str = "https://api-sandbox.asaas.com/v3"
    ASAAS_WEBHOOK_TOKEN: str = ""

settings = Settings()


def get_cors_allow_origins() -> list[str]:
    raw = settings.CORS_ALLOW_ORIGINS or ""
    return [item.strip() for item in raw.split(",") if item.strip()]


def is_production_env() -> bool:
    return settings.APP_ENV.strip().lower() in {"prod", "production", "staging"}


def validate_production_settings() -> None:
    if not is_production_env():
        return

    if settings.DATABASE_URL == "postgresql+psycopg2://ia_app:ia_app_pass@127.0.0.1:55432/ia_trabalhista":
        raise RuntimeError("DATABASE_URL default local is not allowed when APP_ENV is production-like")

    if settings.ALLOW_SEED_ADMIN and (
        not settings.ADMIN_SEED_TOKEN or settings.ADMIN_SEED_TOKEN == "CHANGE_ME_SEED_TOKEN"
    ):
        raise RuntimeError("ALLOW_SEED_ADMIN=true requires a real ADMIN_SEED_TOKEN in production-like env")

    if not settings.AUTH_PROTECT_DOCS:
        raise RuntimeError("AUTH_PROTECT_DOCS must be true in production-like env")


validate_production_settings()
