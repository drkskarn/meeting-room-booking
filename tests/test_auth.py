from flask import url_for

from app.extensions import db


# ========================
# Helpers
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(endpoint, **values)


def login(client, app, user, password):
    return client.post(
        get_url(app, "auth.login"),
        data={
            "email": user.email,
            "password": password,
        },
    )


# ========================
# Authentication Routes
# ========================
def test_login_page_can_be_opened(app, client):
    response = client.get(
        get_url(app, "auth.login")
    )

    assert response.status_code == 200


def test_dashboard_requires_login(app, client):
    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    login_url = get_url(
        app,
        "auth.login"
    )

    response = client.get(
        dashboard_url
    )

    assert response.status_code == 302
    assert login_url in response.headers["Location"]


def test_active_user_can_login(
    app,
    client,
    applicant_user,
):
    response = login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    assert response.status_code == 302
    assert dashboard_url in response.headers["Location"]


def test_wrong_password_is_rejected(
    app,
    client,
    applicant_user,
):
    response = login(
        client,
        app,
        applicant_user,
        "WrongPassword",
    )

    assert response.status_code == 200
    assert (
        b"Alamat emel atau kata laluan tidak sah."
        in response.data
    )


def test_unknown_email_is_rejected(
    app,
    client,
):
    response = client.post(
        get_url(app, "auth.login"),
        data={
            "email": "tidakwujud.test@kpkt.gov.my",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert (
        b"Alamat emel atau kata laluan tidak sah."
        in response.data
    )


def test_inactive_user_cannot_login(
    app,
    client,
    applicant_user,
):
    applicant_user.is_active = False
    db.session.commit()

    response = login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    assert response.status_code == 200
    assert (
        b"Akaun anda belum diaktifkan."
        in response.data
    )


def test_login_session_allows_dashboard_access(
    app,
    client,
    applicant_user,
):
    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.get(
        get_url(app, "auth.dashboard")
    )

    assert response.status_code == 200


def test_authenticated_user_is_redirected_from_login(
    app,
    client,
    applicant_user,
):
    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    response = client.get(
        get_url(app, "auth.login")
    )

    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    assert response.status_code == 302
    assert dashboard_url in response.headers["Location"]


def test_logout_clears_user_session(
    app,
    client,
    applicant_user,
):
    login(
        client,
        app,
        applicant_user,
        "TestPassword123!",
    )

    logout_response = client.get(
        get_url(app, "auth.logout")
    )

    login_url = get_url(
        app,
        "auth.login"
    )

    assert logout_response.status_code == 302
    assert login_url in logout_response.headers["Location"]

    dashboard_response = client.get(
        get_url(app, "auth.dashboard")
    )

    assert dashboard_response.status_code == 302
    assert login_url in dashboard_response.headers["Location"]