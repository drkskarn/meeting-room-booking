import re
from datetime import datetime

from flask import url_for

from app.extensions import db
from app.models import Booking, Room, User


# ========================
# Helpers
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(
            endpoint,
            **values
        )


def create_user(
    *,
    email,
    full_name,
    identification_no,
    role,
    password,
):
    user = User(
        email=email,
        full_name=full_name,
        identification_no=identification_no,
        division_name="Bahagian Ujian",
        unit_name="Unit Ujian",
        role=role,
        is_active=True,
    )

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return user


def create_admin():
    return create_user(
        email="security.admin@kpkt.gov.my",
        full_name="Security Admin",
        identification_no="900101010010",
        role="ADMIN",
        password="AdminPassword123!",
    )


def create_applicant():
    return create_user(
        email="security.applicant@kpkt.gov.my",
        full_name="Security Applicant",
        identification_no="900101010011",
        role="APPLICANT",
        password="TestPassword123!",
    )


def create_room():
    room = Room(
        room_name="Bilik Security",
        location="Aras Security",
        capacity=10,
        is_active=True,
    )

    db.session.add(room)
    db.session.commit()

    return room


def create_booking(
    applicant,
    room,
    *,
    status="PENDING",
):
    booking = Booking(
        applicant_id=applicant.id,
        room_id=room.id,
        start_datetime=datetime(
            2030, 2, 10, 9, 0
        ),
        end_datetime=datetime(
            2030, 2, 10, 10, 0
        ),
        purpose="Mesyuarat Security Test",
        status=status,
    )

    db.session.add(booking)
    db.session.commit()

    return booking


def force_login(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def extract_csrf_token(response):
    match = re.search(
        rb'name="csrf_token"[^>]*value="([^"]+)"',
        response.data,
    )

    assert match is not None

    return match.group(1).decode()


# ========================
# Login CSRF
# ========================
def test_login_without_csrf_token_is_rejected(
    app_csrf,
    client_csrf,
):
    applicant = create_applicant()

    response = client_csrf.post(
        get_url(
            app_csrf,
            "auth.login",
        ),
        data={
            "email": applicant.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    dashboard_response = client_csrf.get(
        get_url(
            app_csrf,
            "auth.dashboard",
        )
    )

    assert dashboard_response.status_code == 302


# ========================
# Create Booking CSRF
# ========================
def test_create_booking_without_csrf_does_not_create_booking(
    app_csrf,
    client_csrf,
):
    applicant = create_applicant()
    room = create_room()

    force_login(
        client_csrf,
        applicant,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "booking.create_booking",
        ),
        data={
            "room_id": str(room.id),
            "start_date": "2030-02-10",
            "start_time": "09:00",
            "end_date": "2030-02-10",
            "end_time": "10:00",
            "purpose": "Booking Tanpa CSRF",
            "chairperson_name": "",
        },
    )

    count = db.session.scalar(
        db.select(
            db.func.count(Booking.id)
        )
    )

    assert response.status_code == 200
    assert count == 0


# ========================
# Approve Booking CSRF
# ========================
def test_approve_without_csrf_returns_400(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    applicant = create_applicant()
    room = create_room()

    booking = create_booking(
        applicant,
        room,
        status="PENDING",
    )

    force_login(
        client_csrf,
        admin,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.approve_booking",
            booking_id=booking.id,
        )
    )

    db.session.refresh(booking)

    assert response.status_code == 400
    assert booking.status == "PENDING"


def test_approve_with_valid_csrf_token_succeeds(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    applicant = create_applicant()
    room = create_room()

    booking = create_booking(
        applicant,
        room,
        status="PENDING",
    )

    force_login(
        client_csrf,
        admin,
    )

    page = client_csrf.get(
        get_url(
            app_csrf,
            "admin.bookings",
        )
    )

    csrf_token = extract_csrf_token(page)

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.approve_booking",
            booking_id=booking.id,
        ),
        data={
            "csrf_token": csrf_token,
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 302
    assert booking.status == "APPROVED"


# ========================
# Room CSRF
# ========================
def test_toggle_room_without_csrf_returns_400(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    room = create_room()

    force_login(
        client_csrf,
        admin,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.toggle_room",
            room_id=room.id,
        )
    )

    db.session.refresh(room)

    assert response.status_code == 400
    assert room.is_active is True


# ========================
# User CSRF
# ========================
def test_toggle_user_without_csrf_returns_400(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    applicant = create_applicant()

    force_login(
        client_csrf,
        admin,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.toggle_user_status",
            user_id=applicant.id,
        )
    )

    db.session.refresh(applicant)

    assert response.status_code == 400
    assert applicant.is_active is True


# ========================
# Reject Booking CSRF
# ========================
def test_reject_without_csrf_does_not_change_status(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    applicant = create_applicant()
    room = create_room()

    booking = create_booking(
        applicant,
        room,
        status="PENDING",
    )

    force_login(
        client_csrf,
        admin,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.reject_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Tidak diluluskan.",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 200
    assert booking.status == "PENDING"
    assert booking.rejection_reason is None


# ========================
# Admin Cancel CSRF
# ========================
def test_admin_cancel_without_csrf_does_not_change_status(
    app_csrf,
    client_csrf,
):
    admin = create_admin()
    applicant = create_applicant()
    room = create_room()

    booking = create_booking(
        applicant,
        room,
        status="APPROVED",
    )

    force_login(
        client_csrf,
        admin,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "admin.cancel_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Pembatalan tanpa CSRF",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 200
    assert booking.status == "APPROVED"
    assert booking.cancellation_reason is None


# ========================
# Applicant Cancel CSRF
# ========================
def test_applicant_cancel_without_csrf_does_not_change_status(
    app_csrf,
    client_csrf,
):
    applicant = create_applicant()
    room = create_room()

    booking = create_booking(
        applicant,
        room,
        status="PENDING",
    )

    force_login(
        client_csrf,
        applicant,
    )

    response = client_csrf.post(
        get_url(
            app_csrf,
            "booking.cancel_own_booking",
            booking_id=booking.id,
        ),
        data={
            "reason": "Pembatalan tanpa CSRF",
        },
    )

    db.session.refresh(booking)

    assert response.status_code == 200
    assert booking.status == "PENDING"
    assert booking.cancellation_reason is None