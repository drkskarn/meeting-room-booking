from datetime import datetime

from app.booking import services


# ========================
# Booking Conflict
# ========================
def test_approved_booking_blocks_overlapping_slot(
    booking_factory,
    room,
):
    booking_factory(
        status="APPROVED",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    assert services.has_booking_conflict(
        room_id=room.id,
        start_datetime=datetime(2030, 1, 10, 9, 30),
        end_datetime=datetime(2030, 1, 10, 10, 30),
    ) is True


def test_pending_booking_does_not_block_slot(
    booking_factory,
    room,
):
    booking_factory(
        status="PENDING",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    assert services.has_booking_conflict(
        room_id=room.id,
        start_datetime=datetime(2030, 1, 10, 9, 30),
        end_datetime=datetime(2030, 1, 10, 10, 30),
    ) is False


def test_adjacent_booking_is_allowed(
    booking_factory,
    room,
):
    booking_factory(
        status="APPROVED",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    assert services.has_booking_conflict(
        room_id=room.id,
        start_datetime=datetime(2030, 1, 10, 10, 0),
        end_datetime=datetime(2030, 1, 10, 11, 0),
    ) is False


def test_excluded_booking_does_not_conflict_with_itself(
    booking_factory,
    room,
):
    booking = booking_factory(
        status="APPROVED",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    assert services.has_booking_conflict(
        room_id=room.id,
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
        exclude_booking_id=booking.id,
    ) is False


# ========================
# Booking Lifecycle
# ========================
def test_approved_past_booking_becomes_completed(
    monkeypatch,
    booking_factory,
):
    fixed_now = datetime(2030, 1, 10, 12, 0)
    monkeypatch.setattr(services, "get_malaysia_now", lambda: fixed_now)

    booking = booking_factory(
        status="APPROVED",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    updated = services.mark_completed_bookings()

    assert updated == 1
    assert booking.status == "COMPLETED"


def test_pending_past_booking_becomes_expired(
    monkeypatch,
    booking_factory,
):
    fixed_now = datetime(2030, 1, 10, 12, 0)
    monkeypatch.setattr(services, "get_malaysia_now", lambda: fixed_now)

    booking = booking_factory(
        status="PENDING",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    updated = services.mark_expired_bookings()

    assert updated == 1
    assert booking.status == "EXPIRED"


def test_future_bookings_are_not_closed_early(
    monkeypatch,
    booking_factory,
):
    fixed_now = datetime(2030, 1, 10, 8, 0)
    monkeypatch.setattr(services, "get_malaysia_now", lambda: fixed_now)

    approved = booking_factory(
        status="APPROVED",
        start_datetime=datetime(2030, 1, 10, 9, 0),
        end_datetime=datetime(2030, 1, 10, 10, 0),
    )

    pending = booking_factory(
        status="PENDING",
        start_datetime=datetime(2030, 1, 10, 10, 0),
        end_datetime=datetime(2030, 1, 10, 11, 0),
    )

    completed_count = services.mark_completed_bookings()
    expired_count = services.mark_expired_bookings()

    assert completed_count == 0
    assert expired_count == 0
    assert approved.status == "APPROVED"
    assert pending.status == "PENDING"
