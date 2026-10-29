from itsdangerous import URLSafeTimedSerializer

from app.auth.tokens import (
    ACTIVATION_TOKEN_MAX_AGE,
    ACTIVATION_TOKEN_SALT,
    generate_activation_token,
    verify_activation_token,
)


# ========================
# Valid Token
# ========================
def test_activation_token_can_be_verified(app):
    email = "token.test@kpkt.gov.my"

    with app.app_context():
        token = generate_activation_token(
            email
        )

        result = verify_activation_token(
            token
        )

    assert result == email


# ========================
# Invalid Token
# ========================
def test_invalid_activation_token_is_rejected(app):
    with app.app_context():
        result = verify_activation_token(
            "invalid-token"
        )

    assert result is None


# ========================
# Wrong Salt
# ========================
def test_wrong_salt_token_is_rejected(app):
    email = "token.test@kpkt.gov.my"

    with app.app_context():
        serializer = URLSafeTimedSerializer(
            app.config["SECRET_KEY"]
        )

        token = serializer.dumps(
            email,
            salt="wrong-salt"
        )

        result = verify_activation_token(
            token
        )

    assert result is None


# ========================
# Wrong Secret
# ========================
def test_wrong_secret_token_is_rejected(app):
    email = "token.test@kpkt.gov.my"

    with app.app_context():
        serializer = URLSafeTimedSerializer(
            "wrong-secret-key"
        )

        token = serializer.dumps(
            email,
            salt=ACTIVATION_TOKEN_SALT
        )

        result = verify_activation_token(
            token
        )

    assert result is None


# ========================
# Expired Token
# ========================
def test_expired_activation_token_is_rejected(app):
    email = "token.test@kpkt.gov.my"

    with app.app_context():
        token = generate_activation_token(
            email
        )

        result = verify_activation_token(
            token,
            max_age=-1
        )

    assert result is None


# ========================
# Default Expiry
# ========================
def test_activation_token_default_expiry():
    assert ACTIVATION_TOKEN_MAX_AGE == 3600