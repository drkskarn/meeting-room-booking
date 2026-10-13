from app.extensions import db
from app.models import Booking

from datetime import datetime
from zoneinfo import ZoneInfo

def has_booking_conflict(
    room_id,
    start_datetime,
    end_datetime,
    exclude_booking_id=None
):
    statement = db.select(Booking).where(
        Booking.room_id == room_id,
        Booking.status == "APPROVED",
        Booking.start_datetime < end_datetime,
        Booking.end_datetime > start_datetime
    )

    if exclude_booking_id is not None:
        statement = statement.where(
            Booking.id != exclude_booking_id
        )

    conflict = db.session.scalar(
        statement.limit(1)
    )

    return conflict is not None

MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def get_malaysia_now():
    return datetime.now(
        MALAYSIA_TZ
    ).replace(tzinfo=None)


def mark_completed_bookings():
    now = get_malaysia_now()

    expired_bookings = db.session.scalars(
        db.select(Booking).where(
            Booking.status == "APPROVED",
            Booking.end_datetime <= now
        )
    ).all()

    if not expired_bookings:
        return 0

    for booking in expired_bookings:
        booking.status = "COMPLETED"

    db.session.commit()

    return len(expired_bookings)