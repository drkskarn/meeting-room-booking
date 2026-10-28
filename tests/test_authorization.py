from flask import url_for


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
# Admin Authorization
# ========================
def test_applicant_cannot_access_admin_bookings(
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
        get_url(
            app,
            "admin.bookings"
        )
    )

    assert response.status_code == 403


def test_admin_can_access_admin_bookings(
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

    response = client.get(
        get_url(
            app,
            "admin.bookings"
        )
    )

    assert response.status_code == 200


# ========================
# Booking Authorization
# ========================
def test_applicant_cannot_view_other_users_booking(
    app,
    client,
    applicant_user,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        applicant_id=admin_user.id,
        status="PENDING",
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
            "booking.booking_detail",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 403


def test_applicant_cannot_edit_other_users_booking(
    app,
    client,
    applicant_user,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        applicant_id=admin_user.id,
        status="PENDING",
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
            "booking.edit_booking",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 403


def test_applicant_cannot_cancel_other_users_booking(
    app,
    client,
    applicant_user,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        applicant_id=admin_user.id,
        status="PENDING",
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
            "booking.cancel_own_booking",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 403


def test_admin_can_view_applicant_booking(
    app,
    client,
    admin_user,
    booking_factory,
):
    booking = booking_factory(
        status="PENDING"
    )

    login(
        client,
        app,
        admin_user,
        "AdminPassword123!",
    )

    response = client.get(
        get_url(
            app,
            "booking.booking_detail",
            booking_id=booking.id,
        )
    )

    assert response.status_code == 200


def test_missing_booking_returns_404(
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
        get_url(
            app,
            "booking.booking_detail",
            booking_id=999999,
        )
    )

    assert response.status_code == 404