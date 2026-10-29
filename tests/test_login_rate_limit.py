from flask import url_for

from app import create_app
from app.extensions import db
from app.models import User


# ========================
# Helpers
# ========================
def get_url(app, endpoint):
    with app.test_request_context():
        return url_for(endpoint)


# ========================
# Rate Limit
# ========================
def test_login_is_rate_limited():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "rate-limit-test-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": True,
        "RATELIMIT_STORAGE_URI": "memory://",
    })

    with app.app_context():
        db.create_all()

        user = User(
            email="rate.test@kpkt.gov.my",
            full_name="Rate Limit Test",
            identification_no="900101010099",
            division_name="Bahagian Ujian",
            unit_name="Unit Security",
            role="APPLICANT",
            is_active=True,
        )

        user.set_password(
            "CorrectPassword123!"
        )

        db.session.add(user)
        db.session.commit()

        client = app.test_client()

        login_url = get_url(
            app,
            "auth.login"
        )

        # ========================
        # First Five Attempts
        # ========================
        for _ in range(5):
            response = client.post(
                login_url,
                data={
                    "email": user.email,
                    "password": "WrongPassword!",
                },
                environ_base={
                    "REMOTE_ADDR": "10.10.10.10"
                },
            )

            assert response.status_code == 200

        # ========================
        # Sixth Attempt
        # ========================
        response = client.post(
            login_url,
            data={
                "email": user.email,
                "password": "WrongPassword!",
            },
            environ_base={
                "REMOTE_ADDR": "10.10.10.10"
            },
        )

        assert response.status_code == 429

        db.session.remove()
        db.drop_all()