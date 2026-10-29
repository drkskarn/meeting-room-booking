from wtforms.validators import ValidationError


# ========================
# Password Policy
# ========================
PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128


def validate_password_strength(form, field):
    password = field.data or ""

    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(
            "Kata laluan mestilah sekurang-kurangnya "
            f"{PASSWORD_MIN_LENGTH} aksara."
        )

    if len(password) > PASSWORD_MAX_LENGTH:
        raise ValidationError(
            "Kata laluan tidak boleh melebihi "
            f"{PASSWORD_MAX_LENGTH} aksara."
        )

    if not any(
        char.isupper()
        for char in password
    ):
        raise ValidationError(
            "Kata laluan mesti mempunyai "
            "sekurang-kurangnya satu huruf besar."
        )

    if not any(
        char.islower()
        for char in password
    ):
        raise ValidationError(
            "Kata laluan mesti mempunyai "
            "sekurang-kurangnya satu huruf kecil."
        )

    if not any(
        char.isdigit()
        for char in password
    ):
        raise ValidationError(
            "Kata laluan mesti mempunyai "
            "sekurang-kurangnya satu nombor."
        )

    if not any(
        not char.isalnum()
        and not char.isspace()
        for char in password
    ):
        raise ValidationError(
            "Kata laluan mesti mempunyai "
            "sekurang-kurangnya satu simbol."
        )