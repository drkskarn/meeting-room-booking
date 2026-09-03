from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    identification_no: Mapped[str] = mapped_column(
        String(12), #disimpan dalam string sbb bukan utk kegunaan pengiraan matematik
        unique=True,
        nullable=False
    )

    division_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    unit_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="APPLICANT"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )