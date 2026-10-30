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
# Password Hashing
# ========================
def test_password_is_not_stored_as_plaintext(
    applicant_user,
):
    plain_password = "TestPassword123!"

    assert (
        applicant_user.password_hash
        != plain_password
    )

    assert applicant_user.check_password(
        plain_password
    )


# ========================
# Account Enumeration
# ========================
def test_invalid_login_uses_generic_message(
    app,
    client,
    applicant_user,
):
    login_url = get_url(
        app,
        "auth.login"
    )

    wrong_password_response = client.post(
        login_url,
        data={
            "email": applicant_user.email,
            "password": "WrongPassword123!",
        },
    )

    unknown_email_response = client.post(
        login_url,
        data={
            "email": "unknown.user@kpkt.gov.my",
            "password": "WrongPassword123!",
        },
    )

    expected_message = (
        "Alamat emel atau kata laluan tidak sah."
    )

    assert expected_message in (
        wrong_password_response.get_data(
            as_text=True
        )
    )

    assert expected_message in (
        unknown_email_response.get_data(
            as_text=True
        )
    )


# ========================
# Production Secure Cookie
# ========================
def test_secure_cookie_when_enabled():
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "secure-cookie-test-key",
        "SQLALCHEMY_DATABASE_URI": "sqlite://",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,

        # Simulasi production HTTPS
        "SESSION_COOKIE_SECURE": True,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    })

    with app.app_context():
        db.create_all()

        user = User(
            email="secure.cookie@kpkt.gov.my",
            full_name="Secure Cookie Test",
            identification_no="900101010088",
            division_name="Bahagian Ujian",
            unit_name="Unit Security",
            role="APPLICANT",
            is_active=True,
        )

        user.set_password(
            "TempahanJPN123!"
        )

        db.session.add(user)
        db.session.commit()

        client = app.test_client()

        login_url = get_url(
            app,
            "auth.login"
        )

        response = client.post(
            login_url,
            data={
                "email": user.email,
                "password": "TempahanJPN123!",
            },
        )

        cookie = response.headers.get(
            "Set-Cookie"
        )

        assert cookie is not None
        assert "Secure" in cookie
        assert "HttpOnly" in cookie
        assert "SameSite=Lax" in cookie

        db.session.remove()
        db.drop_all()