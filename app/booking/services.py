from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models import Booking, Room


# ========================
# Booking Conflict
# ========================
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


# ========================
# Malaysia Time
# ========================
MALAYSIA_TZ = ZoneInfo("Asia/Kuala_Lumpur")


def get_malaysia_now():
    return datetime.now(
        MALAYSIA_TZ
    ).replace(tzinfo=None)


# ========================
# Mark Completed Bookings
# ========================
def mark_completed_bookings():
    now = get_malaysia_now()

    completed_bookings = db.session.scalars(
        db.select(Booking).where(
            Booking.status == "APPROVED",
            Booking.end_datetime <= now
        )
    ).all()

    if not completed_bookings:
        return 0

    for booking in completed_bookings:
        booking.status = "COMPLETED"

    db.session.commit()

    return len(completed_bookings)


# ========================
# Mark Expired Bookings
# ========================
def mark_expired_bookings():
    now = get_malaysia_now()

    expired_bookings = db.session.scalars(
        db.select(Booking).where(
            Booking.status == "PENDING",
            Booking.end_datetime <= now
        )
    ).all()

    if not expired_bookings:
        return 0

    for booking in expired_bookings:
        booking.status = "EXPIRED"

    db.session.commit()

    return len(expired_bookings)


# ========================
# Room Status Today
# ========================
def get_room_statuses(now=None):
    if now is None:
        now = get_malaysia_now()

    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    start_of_tomorrow = (
        start_of_today
        + timedelta(days=1)
    )

    active_rooms = db.session.scalars(
        db.select(Room)
        .where(
            Room.is_active.is_(True)
        )
        .order_by(
            Room.room_name.asc()
        )
    ).all()

    # Hanya tempahan APPROVED yang bertindih dengan hari semasa.
    today_approved_bookings = db.session.scalars(
        db.select(Booking)
        .where(
            Booking.status == "APPROVED",
            Booking.start_datetime < start_of_tomorrow,
            Booking.end_datetime > start_of_today
        )
        .order_by(
            Booking.start_datetime.asc()
        )
    ).all()

    room_statuses = []

    for room in active_rooms:
        room_bookings = [
            booking
            for booking in today_approved_bookings
            if booking.room_id == room.id
        ]

        current_booking = next(
            (
                booking
                for booking in room_bookings
                if (
                    booking.start_datetime <= now
                    and booking.end_datetime > now
                )
            ),
            None
        )

        # ========================
        # Upcoming Bookings Hari Ini
        # ========================

        upcoming_bookings = [
            booking
            for booking in room_bookings
            if (
                booking.start_datetime > now
                and booking.start_datetime < start_of_tomorrow
            )
        ]

        next_booking = (
            upcoming_bookings[0]
            if upcoming_bookings
            else None
        )

        if current_booking is not None:
            room_status = "IN_USE"

        elif next_booking is not None:
            room_status = "UPCOMING"

        else:
            room_status = "AVAILABLE"

        room_statuses.append(
            {
                "room": room,
                "status": room_status,
                "current_booking": current_booking,
                "next_booking": next_booking,
                "upcoming_bookings": upcoming_bookings
            }
        )

    status_priority = {
        "IN_USE": 0,
        "UPCOMING": 1,
        "AVAILABLE": 2
    }

    room_statuses.sort(
        key=lambda item: (
            status_priority[item["status"]],
            item["room"].room_name.lower()
        )
    )

    return room_statuses
