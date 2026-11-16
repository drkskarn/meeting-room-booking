from datetime import datetime
from types import SimpleNamespace

import app.email as email_service


# ========================
# Test Data Helpers
# ========================
def make_user():
    return SimpleNamespace(
        email="pemohon@kpkt.gov.my",
        full_name="Ahmad Audit",
    )


def make_room():
    return SimpleNamespace(
        room_name="Bilik Mesyuarat Utama",
        location="Aras 5",
    )


def make_booking(
    *,
    status="PENDING",
    rejection_reason=None,
    cancellation_reason=None,
):
    return SimpleNamespace(
        id=25,
        applicant=make_user(),
        room=make_room(),
        start_datetime=datetime(
            2026,
            11,
            12,
            9,
            0,
        ),
        end_datetime=datetime(
            2026,
            11,
            12,
            10,
            30,
        ),
        purpose="Mesyuarat penyelarasan projek",
        status=status,
        rejection_reason=rejection_reason,
        cancellation_reason=cancellation_reason,
    )


def capture_mail_send(monkeypatch):
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
# Activation Email
# ========================
def test_send_activation_email(
    app,
    monkeypatch,
):
    user = make_user()

    activation_url = (
        "http://localhost/"
        "activate/test-token"
    )

    sent_messages = capture_mail_send(
        monkeypatch
    )

    with app.app_context():
        email_service.send_activation_email(
            user,
            activation_url,
        )

    assert len(sent_messages) == 1

    message = sent_messages[0]

    assert message.subject == (
        "Pengaktifan Akaun Sistem "
        "Tempahan Bilik Mesyuarat"
    )

    assert message.recipients == [
        user.email
    ]

    assert user.full_name in message.body
    assert activation_url in message.body
    assert "1 jam" in message.body


# ========================
# Booking Created Message
# ========================
def test_build_booking_created_message(app):
    booking = make_booking(
        status="PENDING"
    )

    with app.app_context():
        message = (
            email_service
            .build_booking_created_message(
                booking
            )
        )

    assert "#25" in message.subject
    assert "Diterima" in message.subject
    assert message.recipients == [
        booking.applicant.email
    ]
    assert booking.applicant.full_name in message.body
    assert booking.room.room_name in message.body
    assert booking.room.location in message.body
    assert "12/11/2026 09:00" in message.body
    assert "12/11/2026 10:30" in message.body
    assert booking.purpose in message.body
    assert "PENDING" in message.body


# ========================
# Booking Created Send
# ========================
def test_send_booking_created_email(
    app,
    monkeypatch,
):
    booking = make_booking(
        status="PENDING"
    )

    sent_messages = capture_mail_send(
        monkeypatch
    )

    with app.app_context():
        email_service.send_booking_created_email(
            booking
        )

    assert len(sent_messages) == 1
    message = sent_messages[0]

    assert message.recipients == [
        booking.applicant.email
    ]
    assert "#25" in message.subject
    assert "Diterima" in message.subject


# ========================
# Booking Approved Message
# ========================
def test_build_booking_approved_message(app):
    booking = make_booking(
        status="APPROVED"
    )

    with app.app_context():
        message = (
            email_service
            .build_booking_approved_message(
                booking
            )
        )

    assert "#25" in message.subject
    assert "Diluluskan" in message.subject
    assert message.recipients == [
        booking.applicant.email
    ]
    assert booking.applicant.full_name in message.body
    assert booking.room.room_name in message.body
    assert "12/11/2026 09:00" in message.body
    assert "12/11/2026 10:30" in message.body
    assert booking.purpose in message.body
    assert "APPROVED" in message.body


# ========================
# Booking Approved Send
# ========================
def test_send_booking_approved_email(
    app,
    monkeypatch,
):
    booking = make_booking(
        status="APPROVED"
    )

    sent_messages = capture_mail_send(
        monkeypatch
    )

    with app.app_context():
        email_service.send_booking_approved_email(
            booking
        )

    assert len(sent_messages) == 1
    message = sent_messages[0]

    assert message.recipients == [
        booking.applicant.email
    ]
    assert "#25" in message.subject
    assert "Diluluskan" in message.subject


# ========================
# Booking Rejected Message
# ========================
def test_build_booking_rejected_message(app):
    booking = make_booking(
        status="REJECTED",
        rejection_reason=(
            "Bilik diperlukan untuk program rasmi."
        ),
    )

    with app.app_context():
        message = (
            email_service
            .build_booking_rejected_message(
                booking
            )
        )

    assert "#25" in message.subject
    assert "Ditolak" in message.subject
    assert message.recipients == [
        booking.applicant.email
    ]
    assert booking.applicant.full_name in message.body
    assert booking.room.room_name in message.body
    assert "REJECTED" in message.body
    assert booking.rejection_reason in message.body


# ========================
# Booking Rejected Send
# ========================
def test_send_booking_rejected_email(
    app,
    monkeypatch,
):
    booking = make_booking(
        status="REJECTED",
        rejection_reason="Sebab ujian.",
    )

    sent_messages = capture_mail_send(
        monkeypatch
    )

    with app.app_context():
        email_service.send_booking_rejected_email(
            booking
        )

    assert len(sent_messages) == 1
    message = sent_messages[0]

    assert message.recipients == [
        booking.applicant.email
    ]
    assert "#25" in message.subject
    assert "Ditolak" in message.subject


# ========================
# Booking Cancelled Message
# ========================
def test_build_booking_cancelled_message(app):
    booking = make_booking(
        status="CANCELLED",
        cancellation_reason=(
            "Mesyuarat telah ditangguhkan."
        ),
    )

    with app.app_context():
        message = (
            email_service
            .build_booking_cancelled_message(
                booking
            )
        )

    assert "#25" in message.subject
    assert "Dibatalkan" in message.subject
    assert message.recipients == [
        booking.applicant.email
    ]
    assert booking.applicant.full_name in message.body
    assert booking.room.room_name in message.body
    assert "CANCELLED" in message.body
    assert booking.cancellation_reason in message.body


# ========================
# Booking Cancelled Send
# ========================
def test_send_booking_cancelled_email(
    app,
    monkeypatch,
):
    booking = make_booking(
        status="CANCELLED",
        cancellation_reason="Sebab ujian.",
    )

    sent_messages = capture_mail_send(
        monkeypatch
    )

    with app.app_context():
        email_service.send_booking_cancelled_email(
            booking
        )

    assert len(sent_messages) == 1
    message = sent_messages[0]

    assert message.recipients == [
        booking.applicant.email
    ]
    assert "#25" in message.subject
    assert "Dibatalkan" in message.subject
