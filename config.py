import os

from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///meeting_room.db"
    )

    ADMIN_EMAIL = os.getenv(
        "ADMIN_EMAIL",
        "hafidz@kpkt.gov.my"
    )

    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

    ADMIN_FULL_NAME = os.getenv(
        "ADMIN_FULL_NAME",
        "System Administrator"
    )

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))

    MAIL_USE_TLS = (
        os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    )

    MAIL_USE_SSL = (
        os.getenv("MAIL_USE_SSL", "false").lower() == "true"
    )

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "noreply@kpkt.gov.my"
    )
    
    # ========================
    # Session Security
    # ========================
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = (
        os.getenv(
            "SESSION_COOKIE_SECURE",
            "false"
        ).lower()
        == "true"
    )

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # ========================
    # Rate Limiting
    # ========================
    RATELIMIT_STORAGE_URI = os.getenv(
        "RATELIMIT_STORAGE_URI",
        "memory://"
    )