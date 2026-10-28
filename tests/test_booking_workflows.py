from datetime import datetime

from flask import url_for

from app.extensions import db
from app.models import Booking


# ========================
# Helpers
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(
            endpoint,
            **values
        )


def login(client, app, user, password):
    return client.post(
        get_url(app, "auth.login"),
        data={
            "email": user.email,
            "password": password,
        },
    )


def booking_form_data(room, *, start_date="2030-01-10", start_time="09:00",
    end_date="2030-01-10",
    end_time="10:00",
    purpose="Mesyuarat Ujian Automatik",
    chairperson_name="Pengerusi Ujian",
):
    return {
        "room_id": str(room.id),
        "start_date": start_date,
        "start_time": start_time,
        "end_date": end_date,
        "end_time": end_time,
        "purpose": purpose,
        "chairperson_name": chairperson_name,
    }


# ========================
# Create Booking
# ========================
def test_applicant_can_create_pending_booking(
    app,
    client,
    applicant_user,
    room,
):
    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(app, "booking.create_booking"),
        data=booking_form_data(room),
    )

    booking = db.session.scalar(
        db.select(Booking).where(
            Booking.applicant_id
            == applicant_user.id
        )
    )

    assert response.status_code == 302
    assert booking is not None
    assert booking.status == "PENDING"
    assert booking.room_id == room.id
    assert booking.purpose == "Mesyuarat Ujian Automatik"
    assert booking.chairperson_name == "Pengerusi Ujian"


def test_create_booking_rejects_approved_conflict(
    app,
    client,
    applicant_user,
    room,
    booking_factory,
):
    booking_factory(
        status="APPROVED",
        start_datetime=datetime(
            2030, 1, 10, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 10, 10, 0
        ),
    )

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(app, "booking.create_booking"),
        data=booking_form_data(
            room,
            start_time="09:30",
            end_time="10:30",
        ),
    )

    bookings = db.session.scalars(
        db.select(Booking)
    ).all()

    assert response.status_code == 200
    assert len(bookings) == 1
    assert (
        b"Bilik ini telah ditempah"
        in response.data
    )


def test_adjacent_approved_booking_can_be_created(
    app,
    client,
    applicant_user,
    room,
    booking_factory,
):
    booking_factory(
        status="APPROVED",
        start_datetime=datetime(
            2030, 1, 10, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 10, 10, 0
        ),
    )

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(app, "booking.create_booking"),
        data=booking_form_data(
            room,
            start_time="10:00",
            end_time="11:00",
        ),
    )

    bookings = db.session.scalars(
        db.select(Booking).order_by(
            Booking.id
        )
    ).all()

    assert response.status_code == 302
    assert len(bookings) == 2
    assert bookings[-1].status == "PENDING"


# ========================
# Edit Booking
# ========================
def test_applicant_can_edit_own_pending_booking(
    app,
    client,
    applicant_user,
    room,
    booking_factory,
):
    booking = booking_factory(
        status="PENDING",
        start_datetime=datetime(
            2030, 1, 10, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 10, 10, 0
        ),
    )

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "booking.edit_booking",
            booking_id=booking.id,
        ),
        data=booking_form_data(
            room,
            start_time="11:00",
            end_time="12:00",
            purpose="Mesyuarat Dikemaskini",
            chairperson_name="Pengerusi Baru",
        ),
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.start_datetime == datetime(
        2030, 1, 10, 11, 0
    )
    assert booking.end_datetime == datetime(
        2030, 1, 10, 12, 0
    )
    assert booking.purpose == "Mesyuarat Dikemaskini"
    assert booking.chairperson_name == "Pengerusi Baru"


def test_applicant_cannot_edit_approved_booking(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking = booking_factory(
        status="APPROVED"
    )

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "booking.edit_booking",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 302
    assert booking.status == "APPROVED"


# ========================
# Cancel Own Booking
# ========================
def test_applicant_can_cancel_own_pending_booking(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking = booking_factory(
        status="PENDING"
    )

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "booking.cancel_own_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Mesyuarat dibatalkan.",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.status == "CANCELLED"
    assert booking.cancelled_by_id == applicant_user.id
    assert (
        booking.cancellation_reason
        == "Mesyuarat dibatalkan."
    )


# ========================
# Admin Approve
# ========================
def test_admin_can_approve_pending_booking(
    app,
    client,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        status="PENDING"
    )

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.approve_booking",
            booking_id=booking.id,
        )
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.status == "APPROVED"
    assert booking.approved_by_id == admin_user.id
    assert booking.approved_at is not None


def test_admin_cannot_approve_conflicting_booking(
    app,
    client,
    admin_user,
    room,
    booking_factory,
):
    booking_factory(
        status="APPROVED",
        start_datetime=datetime(
            2030, 1, 10, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 10, 10, 0
        ),
    )

    pending_booking = booking_factory(
        status="PENDING",
        start_datetime=datetime(
            2030, 1, 10, 9, 30
        ),
        end_datetime=datetime(
            2030, 1, 10, 10, 30
        ),
    )

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.approve_booking",
            booking_id=pending_booking.id,
        )
    )

    db.session.refresh(pending_booking)

    assert response.status_code == 302
    assert pending_booking.status == "PENDING"
    assert pending_booking.approved_by_id is None


# ========================
# Admin Reject
# ========================
def test_admin_can_reject_pending_booking(
    app,
    client,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        status="PENDING"
    )

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.reject_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Permohonan tidak dapat diluluskan.",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.status == "REJECTED"
    assert booking.rejected_by_id == admin_user.id
    assert (
        booking.rejection_reason
        == "Permohonan tidak dapat diluluskan."
    )


# ========================
# Admin Cancel
# ========================
def test_admin_can_cancel_approved_booking(
    app,
    client,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        status="APPROVED"
    )

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.cancel_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Tempahan dibatalkan oleh Pentadbir.",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.status == "CANCELLED"
    assert booking.cancelled_by_id == admin_user.id
    assert (
        booking.cancellation_reason
        == "Tempahan dibatalkan oleh Pentadbir."
    )
