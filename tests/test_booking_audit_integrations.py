from datetime import datetime, timedelta

from flask import url_for

from app.extensions import db
from app.models import AuditLog, Booking, Room


# ========================
# URL Helper
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(
            endpoint,
            **values
        )


# ========================
# Login Helper
# ========================
def login(
    app,
    client,
    email,
    password,
):
    return client.post(
        get_url(
            app,
            "auth.login"
        ),
        data={
            "email": email,
            "password": password,
        },
    )


# ========================
# Room Helper
# ========================
def create_room(db_session):
    room = Room(
        room_name="Bilik Audit",
        location="Aras Ujian",
        capacity=10,
        is_active=True,
    )

    db_session.add(room)
    db_session.commit()

    return room


# ========================
# Booking Helper
# ========================
def create_booking(
    db_session,
    applicant_user,
    room,
):
    start = (
        datetime.now()
        + timedelta(days=2)
    )

    booking = Booking(
        applicant_id=applicant_user.id,
        room_id=room.id,
        start_datetime=start,
        end_datetime=(
            start
            + timedelta(hours=1)
        ),
        purpose="Mesyuarat audit trail",
        status="PENDING",
    )

    db_session.add(booking)
    db_session.commit()

    return booking


# ========================
# Find Audit
# ========================
def find_audit(
    action,
    booking_id,
):
    return db.session.scalar(
        db.select(AuditLog).where(
            AuditLog.action == action,
            AuditLog.entity_type
            == "BOOKING",
            AuditLog.entity_id
            == booking_id,
        )
    )


# ========================
# Create Audit
# ========================
def test_create_booking_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
):
    room = create_room(
        db_session
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    start = (
        datetime.now()
        + timedelta(days=3)
    )

    response = client.post(
        get_url(
            app,
            "booking.create_booking"
        ),
        data={
            "room_id": room.id,
            "start_date": (
                start.strftime("%Y-%m-%d")
            ),
            "start_time": "10:00",
            "end_date": (
                start.strftime("%Y-%m-%d")
            ),
            "end_time": "11:00",
            "chairperson_name": (
                "Pengerusi Audit"
            ),
            "purpose": (
                "Mesyuarat ujian audit"
            ),
        },
    )

    assert response.status_code == 302

    booking = db.session.scalar(
        db.select(Booking).where(
            Booking.applicant_id
            == applicant_user.id
        )
        .order_by(
            Booking.id.desc()
        )
    )

    audit = find_audit(
        "CREATE",
        booking.id,
    )

    assert audit is not None
    assert audit.actor_id == (
        applicant_user.id
    )


# ========================
# Edit Audit
# ========================
def test_edit_booking_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
):
    room = create_room(
        db_session
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    start = (
        datetime.now()
        + timedelta(days=4)
    )

    response = client.post(
        get_url(
            app,
            "booking.edit_booking",
            booking_id=booking.id,
        ),
        data={
            "room_id": room.id,
            "start_date": (
                start.strftime("%Y-%m-%d")
            ),
            "start_time": "09:00",
            "end_date": (
                start.strftime("%Y-%m-%d")
            ),
            "end_time": "10:00",
            "chairperson_name": (
                "Pengerusi Baru"
            ),
            "purpose": (
                "Mesyuarat audit dikemaskini"
            ),
        },
    )

    assert response.status_code == 302

    audit = find_audit(
        "EDIT",
        booking.id,
    )

    assert audit is not None
    assert audit.actor_id == (
        applicant_user.id
    )


# ========================
# Approve Audit
# ========================
def test_approve_booking_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
):
    room = create_room(
        db_session
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.approve_booking",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 302

    audit = find_audit(
        "APPROVE",
        booking.id,
    )

    assert audit is not None
    assert audit.actor_id == (
        admin_user.id
    )


# ========================
# Reject Audit
# ========================
def test_reject_booking_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
):
    room = create_room(
        db_session
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.reject_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": (
                "Tidak dapat diluluskan."
            )
        },
    )

    assert response.status_code == 302

    audit = find_audit(
        "REJECTED",
        booking.id,
    )

    assert audit is not None
    assert audit.actor_id == (
        admin_user.id
    )


# ========================
# Applicant Cancel Audit
# ========================
def test_applicant_cancel_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
):
    room = create_room(
        db_session
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "booking.cancel_own_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": (
                "Mesyuarat dibatalkan."
            )
        },
    )

    assert response.status_code == 302

    audit = find_audit(
        "CANCELLED",
        booking.id,
    )

    assert audit is not None
    assert audit.actor_id == (
        applicant_user.id
    )