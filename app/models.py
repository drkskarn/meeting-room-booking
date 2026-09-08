from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db, login_manager

# untuk kegunaan extension flask login_manager
from flask_login import UserMixin

# untuk kegunaan password hashing
from werkzeug.security import generate_password_hash, check_password_hash

#*****************Model utk Users*************************
class User(UserMixin, db.Model):
    
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

    identification_no: Mapped[str | None] = mapped_column(
        String(12), #disimpan dalam string sbb bukan utk kegunaan pengiraan matematik
        unique=True,
        # nullable=False
        nullable=True
    )

    division_name: Mapped[str | None] = mapped_column(
        String(255),
        # nullable=False
        nullable=True
    )

    unit_name: Mapped[str | None] = mapped_column(
        String(255),
        # nullable=False
        nullable=True
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
    
    # utk hashing password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)


    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# *****************Model utk Rooms*************************
class Room (db.Model):
    __tablename__ = "rooms"
    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    room_name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
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