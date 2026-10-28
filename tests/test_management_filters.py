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


# ========================
# User Management
# ========================
def test_admin_can_deactivate_applicant(
    app,
    client,
    admin_user,
    applicant_user,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_user_status",
            user_id=applicant_user.id,
        )
    )

    db.session.refresh(applicant_user)

    assert response.status_code == 302
    assert applicant_user.is_active is False


def test_admin_can_reactivate_applicant(
    app,
    client,
    admin_user,
    applicant_user,
):
    applicant_user.is_active = False
    db.session.commit()

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_user_status",
            user_id=applicant_user.id,
        )
    )

    db.session.refresh(applicant_user)

    assert response.status_code == 302
    assert applicant_user.is_active is True


def test_admin_cannot_disable_own_account(
    app,
    client,
    admin_user,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_user_status",
            user_id=admin_user.id,
        )
    )

    db.session.refresh(admin_user)

    assert response.status_code == 302
    assert admin_user.is_active is True


def test_admin_user_search_by_email(
    app,
    client,
    admin_user,
    applicant_user,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "admin.users",
            q="applicant.test@kpkt.gov.my",
        )
    )

    assert response.status_code == 200
    assert applicant_user.email.encode() in response.data
    assert admin_user.email.encode() not in response.data


def test_admin_user_role_filter(
    app,
    client,
    admin_user,
    applicant_user,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "admin.users",
            role="APPLICANT",
        )
    )

    assert response.status_code == 200
    assert applicant_user.email.encode() in response.data
    assert admin_user.email.encode() not in response.data


# ========================
# Room Management
# ========================
def test_admin_can_deactivate_room(
    app,
    client,
    admin_user,
    room,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_room",
            room_id=room.id,
        )
    )

    db.session.refresh(room)

    assert response.status_code == 302
    assert room.is_active is False


def test_admin_can_reactivate_room(
    app,
    client,
    admin_user,
    room,
):
    room.is_active = False
    db.session.commit()

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_room",
            room_id=room.id,
        )
    )

    db.session.refresh(room)

    assert response.status_code == 302
    assert room.is_active is True


def test_room_search_by_name(
    app,
    client,
    admin_user,
    room,
):
    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "admin.rooms",
            q="Bilik Ujian",
        )
    )

    assert response.status_code == 200
    assert b"Bilik Ujian" in response.data


def test_room_inactive_filter(
    app,
    client,
    admin_user,
    room,
):
    room.is_active = False
    db.session.commit()

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "admin.rooms",
            status="INACTIVE",
        )
    )

    assert response.status_code == 200
    assert room.room_name.encode() in response.data


# ========================
# Booking Search
# ========================
def test_my_bookings_search_by_purpose(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking_factory(
        purpose="Mesyuarat Projek Alpha",
    )

    booking_factory(
        purpose="Mesyuarat Projek Beta",
        start_datetime=datetime(
            2030, 1, 11, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 11, 10, 0
        ),
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
            "booking.my_bookings",
            q="Alpha",
        )
    )

    assert response.status_code == 200
    assert b"Mesyuarat Projek Alpha" in response.data
    assert b"Mesyuarat Projek Beta" not in response.data


def test_my_bookings_status_filter(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking_factory(
        status="PENDING",
        purpose="Booking Pending Ujian",
    )

    booking_factory(
        status="APPROVED",
        purpose="Booking Approved Ujian",
        start_datetime=datetime(
            2030, 1, 11, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 11, 10, 0
        ),
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
            "booking.my_bookings",
            status="APPROVED",
        )
    )

    assert response.status_code == 200
    assert b"Booking Approved Ujian" in response.data
    assert b"Booking Pending Ujian" not in response.data


# ========================
# Booking Date Range
# ========================
def test_my_bookings_date_filter_uses_overlap_rule(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking_factory(
        purpose="Booking Cross Midnight",
        start_datetime=datetime(
            2030, 1, 10, 23, 0
        ),
        end_datetime=datetime(
            2030, 1, 11, 1, 0
        ),
    )

    booking_factory(
        purpose="Booking Outside Range",
        start_datetime=datetime(
            2030, 1, 12, 9, 0
        ),
        end_datetime=datetime(
            2030, 1, 12, 10, 0
        ),
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
            "booking.my_bookings",
            date_from="2030-01-11",
            date_to="2030-01-11",
        )
    )

    assert response.status_code == 200
    assert b"Booking Cross Midnight" in response.data
    assert b"Booking Outside Range" not in response.data


def test_invalid_date_range_returns_no_bookings(
    app,
    client,
    applicant_user,
    booking_factory,
):
    booking_factory(
        purpose="Booking Tidak Sepatutnya Kelihatan",
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
            "booking.my_bookings",
            date_from="2030-01-20",
            date_to="2030-01-10",
        )
    )

    assert response.status_code == 200

    assert (
        b"Booking Tidak Sepatutnya Kelihatan"
        not in response.data
    )


# ========================
# Inactive Room Guard
# ========================
def test_inactive_room_cannot_receive_new_booking(
    app,
    client,
    applicant_user,
    room,
):
    room.is_active = False
    db.session.commit()

    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "booking.create_booking"
        ),
        data={
            "room_id": str(room.id),
            "start_date": "2030-01-10",
            "start_time": "09:00",
            "end_date": "2030-01-10",
            "end_time": "10:00",
            "purpose": "Booking Bilik Tidak Aktif",
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