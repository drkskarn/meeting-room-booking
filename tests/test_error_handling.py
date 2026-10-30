from flask import abort


# ========================
# 403 Error
# ========================
def test_403_uses_safe_error_page(
    app,
    client,
):
    @app.route("/test-403")
    def trigger_403():
        abort(403)

    response = client.get(
        "/test-403"
    )

    assert response.status_code == 403

    assert (
        "Akses Tidak Dibenarkan"
        in response.get_data(as_text=True)
    )


# ========================
# 404 Error
# ========================
def test_404_uses_safe_error_page(
    client,
):
    response = client.get(
        "/route-yang-tidak-wujud"
    )

    assert response.status_code == 404

    assert (
        "Halaman Tidak Ditemui"
        in response.get_data(as_text=True)
    )


# ========================
# 429 Error
# ========================
def test_429_uses_safe_error_page(
    app,
    client,
):
    @app.route("/test-429")
    def trigger_429():
        abort(429)

    response = client.get(
        "/test-429"
    )

    assert response.status_code == 429

    assert (
        "Terlalu Banyak Percubaan"
        in response.get_data(as_text=True)
    )


# ========================
# 500 Error
# ========================
def test_500_does_not_expose_exception(
    app,
    client,
):
    app.config[
        "PROPAGATE_EXCEPTIONS"
    ] = False

    @app.route("/test-500")
    def trigger_500():
        raise RuntimeError(
            "SUPER-SECRET-INTERNAL-ERROR"
        )

    response = client.get(
        "/test-500"
    )

    body = response.get_data(
        as_text=True
    )

    assert response.status_code == 500

    assert (
        "Ralat Dalaman Pelayan"
        in body
    )

    assert (
        "SUPER-SECRET-INTERNAL-ERROR"
        not in body
    )

    assert (
        "RuntimeError"
        not in body
    )


# ========================
# Security Headers
# ========================
def test_error_response_keeps_security_headers(
    client,
):
    response = client.get(
        "/route-tidak-wujud-security-test"
    )

    assert response.status_code == 404

    assert (
        response.headers[
            "X-Content-Type-Options"
        ]
        == "nosniff"
    )

    assert (
        response.headers[
            "X-Frame-Options"
        ]
        == "SAMEORIGIN"
    )