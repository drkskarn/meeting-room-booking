import pytest

from wtforms.validators import ValidationError

from app.auth.past import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_password_strength,
)


# ========================
# Helper
# ========================
class DummyField:
    def __init__(self, value):
        self.data = value


def validate(password):
    field = DummyField(password)

    validate_password_strength(
        None,
        field,
    )


# ========================
# Strong Password
# ========================
def test_strong_password_is_accepted():
    validate(
        "SecurePass123!"
    )


# ========================
# Minimum Length
# ========================
def test_short_password_is_rejected():
    with pytest.raises(
        ValidationError
    ):
        validate(
            "Short1!"
        )


# ========================
# Uppercase
# ========================
def test_password_without_uppercase_is_rejected():
    with pytest.raises(
        ValidationError
    ):
        validate(
            "securepass123!"
        )


# ========================
# Lowercase
# ========================
def test_password_without_lowercase_is_rejected():
    with pytest.raises(
        ValidationError
    ):
        validate(
            "SECUREPASS123!"
        )


# ========================
# Number
# ========================
def test_password_without_number_is_rejected():
    with pytest.raises(
        ValidationError
    ):
        validate(
            "SecurePassword!"
        )


# ========================
# Symbol
# ========================
def test_password_without_symbol_is_rejected():
    with pytest.raises(
        ValidationError
    ):
        validate(
            "SecurePass123"
        )


# ========================
# Maximum Length
# ========================
def test_password_over_max_length_is_rejected():
    password = (
        "Aa1!"
        + ("x" * PASSWORD_MAX_LENGTH)
    )

    with pytest.raises(
        ValidationError
    ):
        validate(password)


# ========================
# Policy Configuration
# ========================
def test_password_minimum_length_is_12():
    assert PASSWORD_MIN_LENGTH == 12