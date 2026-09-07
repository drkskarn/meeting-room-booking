from flask import current_app
from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)


def generate_activation_token(email):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        email,
        salt="email-activation"
    )


def verify_activation_token(token, max_age=60):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        email = serializer.loads(
            token,
            salt="email-activation",
            # max_age=86400 seconds ni tarik dari function. utk testing 60 seconds
            max_age=max_age
        )

        return email

    except SignatureExpired:
        return None

    except BadSignature:
        return None