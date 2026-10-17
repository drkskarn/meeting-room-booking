from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text
)

from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    
#  *****************Model utk Booking*************************
class Booking(db.Model):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    applicant_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        nullable=False
    )

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    end_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    purpose: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    chairperson_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="PENDING"
    )

    approved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    cancelled_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
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

    rejected_by_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_bookings_rejected_by_id_users"
        ),
        
        nullable=True
    )
    
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )
    
    applicant: Mapped["User"] = relationship(
        foreign_keys=[applicant_id]
    )

    room: Mapped["Room"] = relationship()

    approved_by: Mapped["User | None"] = relationship(
        foreign_keys=[approved_by_id]
    )

    cancelled_by: Mapped["User | None"] = relationship(
        foreign_keys=[cancelled_by_id]
    )
    
    rejected_by: Mapped["User | None"] = relationship(
    foreign_keys=[rejected_by_id]
    )