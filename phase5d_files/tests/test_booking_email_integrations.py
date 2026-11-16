from datetime import datetime, timedelta

from flask import url_for

import app.email as email_service

from app.extensions import db
from app.models import Booking, Room


# ========================
# URL Helper
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(endpoint, **values)


# ========================
# Login Helper
# ========================
def login(app, client, email, password):
    return client.post(
        get_url(app, "auth.login"),
        data={
            "email": email,
            "password": password,
        },
    )


# ========================
# Create Room Helper
# ========================
def create_room(db_session, room_name):
    room = Room(
        room_name=room_name,
        location="Aras Ujian Email",
        capacity=10,
        is_active=True,
    )

    db_session.add(room)
    db_session.commit()

    return room


# ========================
# Create Booking Helper
# ========================
def create_booking(db_session, applicant_user, room):
    start_datetime = datetime.now() + timedelta(days=2)

    booking = Booking(
        applicant_id=applicant_user.id,
        room_id=room.id,
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=1),
        purpose="Mesyuarat ujian notifikasi email",
        chairperson_name="Pengerusi Ujian",
        status="PENDING",
    )

    db_session.add(booking)
    db_session.commit()

    return booking


# ========================
# Capture Sent Emails
# ========================
def capture_sent_emails(monkeypatch):
    sent_messages = []

    def fake_send(message):
        sent_messages.append(message)

    monkeypatch.setattr(
        email_service.mail,
        "send",
        fake_send,
    )

    return sent_messages


# ========================
# Create Booking Sends Email
# ========================
def test_create_booking_sends_email(
    app,
    client,
    db_session,
    applicant_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Create Booking Email",
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    start_datetime = datetime.now() + timedelta(days=3)

    response = client.post(
        get_url(app, "booking.create_booking"),
        data={
            "room_id": room.id,
            "start_date": start_datetime.strftime("%Y-%m-%d"),
            "start_time": "09:00",
            "end_date": start_datetime.strftime("%Y-%m-%d"),
            "end_time": "10:00",
            "chairperson_name": "Pengerusi Email",
            "purpose": "Mesyuarat ujian email tempahan baharu",
        },
    )

    assert response.status_code == 302

    booking = db.session.scalar(
        db.select(Booking)
        .where(
            Booking.applicant_id == applicant_user.id
        )
        .order_by(
            Booking.id.desc()
        )
    )

    assert booking is not None
    assert booking.status == "PENDING"
    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message.recipients == [applicant_user.email]
    assert f"#{booking.id}" in message.subject
    assert "Diterima" in message.subject
    assert applicant_user.full_name in message.body
    assert room.room_name in message.body
    assert booking.purpose in message.body
    assert "PENDING" in message.body


# ========================
# Approve Booking Sends Email
# ========================
def test_approve_booking_sends_email(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Approve Booking Email",
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
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

    db_session.refresh(booking)

    assert booking.status == "APPROVED"
    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message.recipients == [applicant_user.email]
    assert f"#{booking.id}" in message.subject
    assert "Diluluskan" in message.subject
    assert applicant_user.full_name in message.body
    assert room.room_name in message.body
    assert booking.purpose in message.body
    assert "APPROVED" in message.body


# ========================
# Reject Booking Sends Email
# ========================
def test_reject_booking_sends_email(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Reject Booking Email",
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
    )

    rejection_reason = (
        "Bilik diperlukan untuk program rasmi jabatan."
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
            "reason": rejection_reason,
        },
    )

    assert response.status_code == 302

    db_session.refresh(booking)

    assert booking.status == "REJECTED"
    assert booking.rejection_reason == rejection_reason
    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message.recipients == [applicant_user.email]
    assert f"#{booking.id}" in message.subject
    assert "Ditolak" in message.subject
    assert applicant_user.full_name in message.body
    assert room.room_name in message.body
    assert rejection_reason in message.body
    assert "REJECTED" in message.body


# ========================
# Admin Cancel Sends Email
# ========================
def test_admin_cancel_sends_email(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Admin Cancel Email",
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
    )

    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    cancellation_reason = (
        "Tempahan dibatalkan oleh Pentadbir Sistem."
    )

    response = client.post(
        get_url(
            app,
            "admin.cancel_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": cancellation_reason,
        },
    )

    assert response.status_code == 302

    db_session.refresh(booking)

    assert booking.status == "CANCELLED"
    assert booking.cancellation_reason == cancellation_reason
    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message.recipients == [applicant_user.email]
    assert f"#{booking.id}" in message.subject
    assert "Dibatalkan" in message.subject
    assert applicant_user.full_name in message.body
    assert room.room_name in message.body
    assert booking.cancellation_reason in message.body


# ========================
# Applicant Cancel No Email
# ========================
def test_applicant_cancel_does_not_send_email(
    app,
    client,
    db_session,
    applicant_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Applicant Cancel Email",
    )

    booking = create_booking(
        db_session,
        applicant_user,
        room,
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    cancellation_reason = (
        "Mesyuarat dibatalkan oleh pemohon."
    )

    response = client.post(
        get_url(
            app,
            "booking.cancel_own_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": cancellation_reason,
        },
    )

    assert response.status_code == 302

    db_session.refresh(booking)

    assert booking.status == "CANCELLED"
    assert booking.cancellation_reason == cancellation_reason
    assert sent_messages == []


# ========================
# Notifications Disabled
# ========================
def test_create_booking_does_not_send_email_when_disabled(
    app,
    client,
    db_session,
    applicant_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Email Disabled",
    )

    sent_messages = capture_sent_emails(monkeypatch)

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        False,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    start_datetime = datetime.now() + timedelta(days=4)

    response = client.post(
        get_url(app, "booking.create_booking"),
        data={
            "room_id": room.id,
            "start_date": start_datetime.strftime("%Y-%m-%d"),
            "start_time": "11:00",
            "end_date": start_datetime.strftime("%Y-%m-%d"),
            "end_time": "12:00",
            "chairperson_name": "Pengerusi Email Disabled",
            "purpose": "Ujian notifikasi email yang dimatikan",
        },
    )

    assert response.status_code == 302

    booking = db.session.scalar(
        db.select(Booking)
        .where(
            Booking.applicant_id == applicant_user.id
        )
        .order_by(
            Booking.id.desc()
        )
    )

    assert booking is not None
    assert booking.status == "PENDING"
    assert sent_messages == []


# ========================
# Email Failure Does Not
# Break Booking Creation
# ========================
def test_email_failure_does_not_break_booking_creation(
    app,
    client,
    db_session,
    applicant_user,
    monkeypatch,
):
    room = create_room(
        db_session,
        "Bilik Email Failure",
    )

    monkeypatch.setitem(
        app.config,
        "MAIL_NOTIFICATIONS_ENABLED",
        True,
    )

    def failing_send(message):
        raise RuntimeError(
            "Simulated SMTP failure"
        )

    monkeypatch.setattr(
        email_service.mail,
        "send",
        failing_send,
    )

    login(
        app,
        client,
        applicant_user.email,
        "TestPassword123!",
    )

    start_datetime = datetime.now() + timedelta(days=5)

    response = client.post(
        get_url(app, "booking.create_booking"),
        data={
            "room_id": room.id,
            "start_date": start_datetime.strftime("%Y-%m-%d"),
            "start_time": "14:00",
            "end_date": start_datetime.strftime("%Y-%m-%d"),
            "end_time": "15:00",
            "chairperson_name": "Pengerusi SMTP Failure",
            "purpose": "Ujian kegagalan SMTP",
        },
    )

    assert response.status_code == 302

    booking = db.session.scalar(
        db.select(Booking)
        .where(
            Booking.applicant_id == applicant_user.id,
            Booking.purpose == "Ujian kegagalan SMTP",
        )
    )

    assert booking is not None
    assert booking.status == "PENDING"
    assert booking.room_id == room.id
