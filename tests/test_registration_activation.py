from urllib.parse import urlsplit

from app.extensions import db
from app.models import User


# ========================
# Registration Data
# ========================
def registration_data():
    return {
        "email": "registration.test@kpkt.gov.my",
        "full_name": "Registration Test",
        "identification_no": "900101010099",
        "division_name": "Bahagian Ujian",
        "unit_name": "Unit Registration",
        "password": "TempahanJPN123!",
        "confirm_password": "TempahanJPN123!",
    }


# ========================
# Register Creates Inactive User
# ========================
def test_registration_creates_inactive_user(
    app,
    client,
    monkeypatch,
):
    sent_email = {}

    def fake_send_activation_email(
        user,
        activation_url,
    ):
        sent_email["email"] = user.email
        sent_email["activation_url"] = (
            activation_url
        )

    monkeypatch.setattr(
        "app.auth.routes.send_activation_email",
        fake_send_activation_email,
    )

    response = client.post(
        "/auth/register",
        data=registration_data(),
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/login"
    )

    user = db.session.scalar(
        db.select(User).where(
            User.email
            == "registration.test@kpkt.gov.my"
        )
    )

    assert user is not None
    assert user.is_active is False

    assert sent_email["email"] == (
        "registration.test@kpkt.gov.my"
    )

    assert "/auth/activate/" in (
        sent_email["activation_url"]
    )


# ========================
# Activation Enables Account
# ========================
def test_activation_enables_account(
    app,
    client,
    monkeypatch,
):
    sent_email = {}

    def fake_send_activation_email(
        user,
        activation_url,
    ):
        sent_email["activation_url"] = (
            activation_url
        )

    monkeypatch.setattr(
        "app.auth.routes.send_activation_email",
        fake_send_activation_email,
    )

    client.post(
        "/auth/register",
        data=registration_data(),
    )

    activation_path = urlsplit(
        sent_email["activation_url"]
    ).path

    response = client.get(
        activation_path,
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/login"
    )

    user = db.session.scalar(
        db.select(User).where(
            User.email
            == "registration.test@kpkt.gov.my"
        )
    )

    assert user is not None
    assert user.is_active is True


# ========================
# Invalid Activation Token
# ========================
def test_invalid_activation_token(
    client,
):
    response = client.get(
        "/auth/activate/invalid-token",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/login"
    )


# ========================
# Login After Activation
# ========================
def test_login_after_activation(
    app,
    client,
    monkeypatch,
):
    sent_email = {}

    def fake_send_activation_email(
        user,
        activation_url,
    ):
        sent_email["activation_url"] = (
            activation_url
        )

    monkeypatch.setattr(
        "app.auth.routes.send_activation_email",
        fake_send_activation_email,
    )

    client.post(
        "/auth/register",
        data=registration_data(),
    )

    activation_path = urlsplit(
        sent_email["activation_url"]
    ).path

    client.get(
        activation_path
    )

    response = client.post(
        "/auth/login",
        data={
            "email": (
                "registration.test@kpkt.gov.my"
            ),
            "password": "TempahanJPN123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/auth/dashboard"
    )