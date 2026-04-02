"""
RECRUIT.AI — Backend Configuration
Loads environment variables and exposes typed settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
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

    # ── EmailJS — Service 1 (Applied + Task) ──
    EMAILJS_SERVICE_1_ID: str = ""
    EMAILJS_SERVICE_1_PUBLIC_KEY: str = ""
    EMAILJS_SERVICE_1_PRIVATE_KEY: str = ""
    EMAILJS_TEMPLATE_APPLIED: str = "template_hqwiwda"
    EMAILJS_TEMPLATE_TASK: str = "template_n6wwvck"

    # ── EmailJS — Service 2 (Interview + Result) ──
    EMAILJS_SERVICE_2_ID: str = ""
    EMAILJS_SERVICE_2_PUBLIC_KEY: str = ""
    EMAILJS_SERVICE_2_PRIVATE_KEY: str = ""
    EMAILJS_TEMPLATE_INTERVIEW: str = "template_2ff11hc"
    EMAILJS_TEMPLATE_RESULT: str = "template_lvd2m7p"

    # ── Frontend URL ──
    FRONTEND_URL: str = "http://localhost:5173"

    # ── AI Service URL ──
    AI_SERVICE_URL: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
