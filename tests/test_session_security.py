from datetime import timedelta

from flask import url_for


# ========================
# Helpers
# ========================
def get_url(app, endpoint):
    with app.test_request_context():
        return url_for(endpoint)


# ========================
# Session Configuration
# ========================
def test_session_cookie_security_config(app):
    assert (
        app.config["SESSION_COOKIE_HTTPONLY"]
        is True
    )

    assert (
        app.config["SESSION_COOKIE_SAMESITE"]
        == "Lax"
    )

    assert (
        app.config["PERMANENT_SESSION_LIFETIME"]
        == timedelta(hours=8)
    )


# ========================
# Login Session
# ========================
def test_login_creates_permanent_session(
    app,
    client,
    applicant_user,
):
    response = client.post(
        get_url(
            app,
            "auth.login"
        ),
        data={
            "email": applicant_user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert session.permanent is True


# ========================
# Session Cookie Flags
# ========================
def test_login_cookie_has_security_flags(
    app,
    client,
    applicant_user,
):
    response = client.post(
        get_url(
            app,
            "auth.login"
        ),
        data={
            "email": applicant_user.email,
            "password": "TestPassword123!",
        },
    )

    cookie = response.headers.get(
        "Set-Cookie"
    )

    assert cookie is not None
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie