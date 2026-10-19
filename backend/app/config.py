"""
RECRUIT.AI — Backend Configuration
Loads environment variables and exposes typed settings.
"""

import logging
from functools import lru_cache
from urllib.parse import urlparse

from pydantic import model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Placeholders published in this repository. Anyone can sign a token with
# them, so they are only acceptable where nothing real is at stake.
KNOWN_PLACEHOLDER_SECRETS = frozenset({
    "change-me-to-a-random-secret-key-in-production",
    "change-me-generate-with-openssl-rand-hex-32",
})
MIN_SECRET_KEY_LENGTH = 32

LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "::1"})


def _is_loopback(url: str) -> bool:
    host = (urlparse(url.strip()).hostname or "").lower()
    return host in LOOPBACK_HOSTS or host.endswith(".localhost")


class Settings(BaseSettings):
    # ── Environment ──
    ENVIRONMENT: str = "development"

    # ── Database (MongoDB) ──
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB: str = "recruit_ai"
    # Kept short so an unreachable database surfaces as a fast error rather
    # than a request that hangs for the driver's 30s default.
    MONGODB_TIMEOUT_MS: int = 5000

    # ── JWT ──
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Session cookie ──
    # The session JWT travels in an httpOnly cookie so no script on the page
    # can read it. The browser reaches the API through the frontend's own
    # origin (a rewrite in next.config.mjs), which keeps the cookie
    # first-party; set on the API's own domain it would be a third-party
    # cookie, and Safari would drop it.
    SESSION_COOKIE_NAME: str = "recruit_session"
    # Unset means "production only", so plain-http local development works.
    SESSION_COOKIE_SECURE: bool | None = None

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.strip().lower() == "production"

    @property
    def session_cookie_secure(self) -> bool:
        if self.SESSION_COOKIE_SECURE is not None:
            return self.SESSION_COOKIE_SECURE
        return self.is_production

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

    # ── Interview links ──
    # Interview tokens used to be valid forever. A link that leaks or is
    # forwarded should stop working at some point.
    INTERVIEW_TOKEN_TTL_DAYS: int = 14

    # ── Email outbox ──
    # Retry loop for queued mail. Disable to send inline only.
    OUTBOX_SWEEPER_ENABLED: bool = True
    OUTBOX_SWEEP_INTERVAL_SECONDS: int = 60
    # Grace period before a pending row is retried, so the inline attempt that
    # just queued it is not immediately duplicated by the sweeper.
    OUTBOX_RETRY_DELAY_SECONDS: int = 120

    # ── Error tracking ──
    # Empty disables Sentry entirely; nothing is sent and the SDK is not even
    # imported, so local development needs no account.
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    # ── Logging ──
    LOG_LEVEL: str = "INFO"

    # ── Rate limiting ──
    RATE_LIMIT_ENABLED: bool = True
    # Honour X-Forwarded-For when deployed behind a proxy that sets it.
    # Leave off otherwise: the header is trivially forged, and trusting it
    # without a proxy in front lets a caller bypass every limit.
    TRUST_PROXY_HEADERS: bool = False

    # ── CORS ──
    # Comma-separated list of allowed browser origins. "*" cannot be combined
    # with credentialed requests, so it is rejected at startup.
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    # ── Password reset ──
    PASSWORD_RESET_TOKEN_TTL_MINUTES: int = 60
    # Invitations get longer than an ordinary reset: one may sit unread for a
    # day or two, and expiry means re-inviting.
    INVITE_TOKEN_TTL_MINUTES: int = 60 * 24 * 7

    # ── Frontend URL ──
    # Used to build every link emailed to a candidate (apply, task,
    # submission, interview, password reset). Must match where the Next.js
    # app is actually served.
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Sign in with Google / GitHub (optional) ──
    # Each provider is offered only when both its values are set. The
    # callback is FRONTEND_URL/api/auth/oauth/<provider>/callback, which must
    # be registered with the provider exactly. It goes through the frontend's
    # /api rewrite so the session cookie is first-party, like every other one.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # ── AI Service URL ──
    AI_SERVICE_URL: str = "http://localhost:8001"

    @model_validator(mode="after")
    def _refuse_a_weak_signing_key_in_production(self):
        """
        Same pattern as the CORS wildcard check: refuse to boot rather than
        run with a setting that silently makes every session forgeable.
        """
        if self.ENVIRONMENT.strip().lower() != "production":
            return self
        if self.SECRET_KEY in KNOWN_PLACEHOLDER_SECRETS:
            raise ValueError(
                "SECRET_KEY is a published placeholder, so anyone could sign a "
                "valid token. Set a random value: openssl rand -hex 32"
            )
        if len(self.SECRET_KEY) < MIN_SECRET_KEY_LENGTH:
            raise ValueError(
                f"SECRET_KEY must be at least {MIN_SECRET_KEY_LENGTH} characters "
                "in production. Generate one with: openssl rand -hex 32"
            )
        return self

    @model_validator(mode="after")
    def _keep_emailed_links_off_localhost_in_production(self):
        """
        FRONTEND_URL defaults to localhost for development. A deployment that
        never sets it would email candidates links to their own machine, so
        fall back to APP_URL, the public site, and refuse to boot only if
        that is local too.
        """
        if self.ENVIRONMENT.strip().lower() != "production":
            return self
        if _is_loopback(self.APP_URL):
            raise ValueError(
                "APP_URL points at localhost in production. Set it to the "
                "public site, e.g. https://recruitai.shouryaparashar.in"
            )
        if not self.FRONTEND_URL.strip() or _is_loopback(self.FRONTEND_URL):
            logger.warning(
                "FRONTEND_URL is unset or local in production; emailed links "
                "will use APP_URL (%s) instead",
                self.APP_URL,
            )
            self.FRONTEND_URL = self.APP_URL.strip().rstrip("/")
        return self

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
