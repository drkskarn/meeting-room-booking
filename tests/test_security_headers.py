from flask import url_for


# ========================
# Security Headers
# ========================
def test_security_headers_are_present(app, client):
    with app.test_request_context():
        login_url = url_for("auth.login")

    response = client.get(login_url)

    assert response.status_code == 200

    assert (
        response.headers["X-Content-Type-Options"]
        == "nosniff"
    )

    assert (
        response.headers["X-Frame-Options"]
        == "SAMEORIGIN"
    )

    assert (
        response.headers["Referrer-Policy"]
        == "strict-origin-when-cross-origin"
    )

    assert (
        response.headers["Permissions-Policy"]
        == "camera=(), microphone=(), geolocation=()"
    )