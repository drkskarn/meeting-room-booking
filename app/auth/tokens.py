from flask import current_app
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)


# ========================
# Activation Token Config
# ========================
ACTIVATION_TOKEN_SALT = "email-activation"
ACTIVATION_TOKEN_MAX_AGE = 3600


# ========================
# Generate Activation Token
# ========================
def generate_activation_token(email):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        email,
        salt=ACTIVATION_TOKEN_SALT
    )


# ========================
# Verify Activation Token
# ========================
def verify_activation_token(
    token,
    max_age=ACTIVATION_TOKEN_MAX_AGE
):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        return serializer.loads(
            token,
            salt=ACTIVATION_TOKEN_SALT,
            max_age=max_age
        )

    except (
        SignatureExpired,
        BadSignature
    ):
        return None