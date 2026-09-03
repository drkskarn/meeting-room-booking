import os

from dotenv import load_dotenv


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