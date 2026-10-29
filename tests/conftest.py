from datetime import datetime, timedelta

import pytest
from app import create_app
from app.extensions import db
from app.models import Booking, Room, User


# ========================
# Test Application
# ========================
@pytest.fixture
def app():
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret-key-only",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
    })
    
    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()

# ========================
# Test Fake Browser
# ========================
@pytest.fixture
def client(app):
    return app.test_client()

# ========================
# Database Session
# ========================
@pytest.fixture
def db_session(app):
    """Expose the active SQLAlchemy session inside the test app context."""
    return db.session


# ========================
# Users
# ========================
@pytest.fixture
def applicant_user(db_session):
    user = User(
        email="applicant.test@kpkt.gov.my",
        full_name="Applicant Test",
        identification_no="900101010001",
        division_name="Bahagian Ujian",
        unit_name="Unit Ujian",
        role="APPLICANT",
        is_active=True,
    )
    user.set_password("TestPassword123!")

    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture
def admin_user(db_session):
    user = User(
        email="admin.test@kpkt.gov.my",
        full_name="Admin Test",
        identification_no="900101010002",
        division_name="Bahagian Ujian",
        unit_name="Unit Pentadbir",
        role="ADMIN",
        is_active=True,
    )
    user.set_password("AdminPassword123!")

    db_session.add(user)
    db_session.commit()

    return user


# ========================
# Room
# ========================
@pytest.fixture
def room(db_session):
    meeting_room = Room(
        room_name="Bilik Ujian",
        location="Aras Ujian",
        capacity=12,
        is_active=True,
    )

    db_session.add(meeting_room)
    db_session.commit()

    return meeting_room


# ========================
# Booking Factory
# ========================
@pytest.fixture
def booking_factory(db_session, applicant_user, room):
    def _create_booking(
        *,
        status="PENDING",
        start_datetime=None,
        end_datetime=None,
        purpose="Mesyuarat Ujian",
        applicant_id=None,
        room_id=None,
    ):
        if start_datetime is None:
            start_datetime = datetime(2030, 1, 10, 9, 0)

        if end_datetime is None:
            end_datetime = start_datetime + timedelta(hours=1)

        booking = Booking(
            applicant_id=applicant_id or applicant_user.id,
            room_id=room_id or room.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            purpose=purpose,
            status=status,
        )

        db_session.add(booking)
        db_session.commit()

        return booking

    return _create_booking

# ========================
# CSRF Test Application
# ========================
@pytest.fixture
def app_csrf():
    test_app = create_app({
        "TESTING": True,
        "SECRET_KEY": "csrf-test-secret-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": True,
        "RATELIMIT_ENABLED": False,
    })

    with test_app.app_context():
        db.create_all()

        yield test_app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client_csrf(app_csrf):
    return app_csrf.test_client()