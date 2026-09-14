from app.extensions import db
from app.models import Booking


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