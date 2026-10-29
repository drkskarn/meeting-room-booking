from flask import url_for


# ========================
# Helpers
# ========================
def get_url(app, endpoint):
    with app.test_request_context():
        return url_for(endpoint)


def login(
    app,
    client,
    user,
    password,
    next_url=None,
):
    login_url = get_url(
        app,
        "auth.login"
    )

    return client.post(
        login_url,
        query_string={
            "next": next_url
        } if next_url else None,
        data={
            "email": user.email,
            "password": password,
        },
    )


# ========================
# Session Fixation
# ========================
def test_login_clears_old_session_data(
    app,
    client,
    applicant_user,
):
    with client.session_transaction() as session:
        session["old_session_marker"] = (
            "should-be-removed"
        )

    response = login(
        app,
        client,
        applicant_user,
        "TestPassword123!",
    )

    assert response.status_code == 302

    with client.session_transaction() as session:
        assert (
            "old_session_marker"
            not in session
        )

        assert (
            session["_user_id"]
            == str(applicant_user.id)
        )

        assert session.permanent is True


# ========================
# Safe Redirect
# ========================
def test_internal_next_redirect_is_allowed(
    app,
    client,
    applicant_user,
):
    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    response = login(
        app,
        client,
        applicant_user,
        "TestPassword123!",
        next_url=dashboard_url,
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == dashboard_url
    )


def test_external_next_redirect_is_blocked(
    app,
    client,
    applicant_user,
):
    response = login(
        app,
        client,
        applicant_user,
        "TestPassword123!",
        next_url="https://evil.example",
    )

    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == dashboard_url
    )


def test_protocol_relative_redirect_is_blocked(
    app,
    client,
    applicant_user,
):
    response = login(
        app,
        client,
        applicant_user,
        "TestPassword123!",
        next_url="//evil.example",
    )

    dashboard_url = get_url(
        app,
        "auth.dashboard"
    )

    assert response.status_code == 302

    assert (
        response.headers["Location"]
        == dashboard_url
    )