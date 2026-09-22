"""
RECRUIT.AI — Backend Configuration
Loads environment variables and exposes typed settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Environment ──
    ENVIRONMENT: str = "development"

    # Create tables directly from the models on startup.
    #
    # Off by default. create_all() only ever creates missing tables: it never
    # alters an existing one, so on a database that is already populated a
    # changed column is silently ignored and the code then runs against a
    # schema it does not match. Alembic owns the schema; this is a convenience
    # for a throwaway local database only.
    AUTO_CREATE_TABLES: bool = False

    # ── Database ──
    DATABASE_URL: str = "postgresql://recruit_user:recruit_pass@localhost:5432/recruit_ai"

    # ── JWT ──
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── AWS S3 / MinIO ──
    S3_BUCKET_NAME: str = "recruit-ai-uploads"
    S3_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str = ""

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Email (Resend) ──
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""
    RESEND_FROM_NAME: str = "RECRUIT.AI"
    SUPPORT_EMAIL: str = "support@shouryaparashar.in"

    # Public base URL used for logo and footer links inside emails. Mail
    # clients cannot resolve relative paths, so these must be absolute.
    APP_URL: str = "https://recruitai.shouryaparashar.in"
    EMAIL_LOGO_URL: str = ""

    # ── Password reset ──
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 60

    # ── Frontend URL ──
    FRONTEND_URL: str = "http://localhost:5173"

    # ── AI Service URL ──
    AI_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Ignore unrecognised variables rather than refusing to start. A
        # deployed .env almost always outlives the settings that read it — the
        # EmailJS keys this replaced being the immediate example — and a
        # retired setting should not take the service down on boot.
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
