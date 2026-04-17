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
    JWT_SECRET: str = Field(..., min_length=32)
    JWT_ALG: str = "HS256"
    JWT_EXPIRES_MIN: int = 60
    ADMIN_SEED_TOKEN: str = "CHANGE_ME_SEED_TOKEN"
    ALLOW_SEED_ADMIN: bool = False
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

settings = Settings()
