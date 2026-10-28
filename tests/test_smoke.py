from app.extensions import db
from app.models import Booking, Room, User
from sqlalchemy import func


# ========================
# Smoke Tests
# ========================
def test_test_database_starts_empty(app):
    assert db.session.scalar(db.select(func.count(User.id))) == 0
    assert db.session.scalar(db.select(func.count(Room.id))) == 0
    assert db.session.scalar(db.select(func.count(Booking.id))) == 0


def test_user_password_hash_round_trip(applicant_user):
    assert applicant_user.check_password("TestPassword123!") is True
    assert applicant_user.check_password("WrongPassword") is False


def test_booking_factory_creates_booking(booking_factory):
    booking = booking_factory()

    assert booking.id is not None
    assert booking.status == "PENDING"
    assert booking.room is not None
    assert booking.applicant is not None
