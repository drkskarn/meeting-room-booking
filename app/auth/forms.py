from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    ValidationError,
)

from app.extensions import db
from app.models import User
from app.auth.past import validate_password_strength

# Form untuk register
class RegistrationForm(FlaskForm):
    email = StringField(
        "Alamat Emel",
        validators=[
            DataRequired(),
            Email(),
        ],
    )

    full_name = StringField(
        "Nama Penuh",
        validators=[
            DataRequired(),
            Length(min=3, max=255),
        ],
    )

    identification_no = StringField(
        "No Pengenalan",
        validators=[
            DataRequired(),
            Regexp(
                r"^\d{12}$",
                message="No Pengenalan mestilah tepat 12 digit nombor.",
            ),
        ],
    )

    division_name = StringField(
        "Nama Bahagian",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )

    unit_name = StringField(
        "Nama Cawangan/Unit",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )

    password = PasswordField(
        "Kata Laluan",
        validators=[
            DataRequired(),
            validate_password_strength,
        ],
    )

    confirm_password = PasswordField(
        "Sahkan Kata Laluan",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Kata laluan tidak sepadan.",
            ),
        ],
    )

    submit = SubmitField("Daftar")

    def validate_email(self, field):
        email = field.data.strip().lower()

        try:
            domain = email.rsplit("@", 1)[1]
        except IndexError:
            raise ValidationError(
                "Alamat emel tidak sah."
            )

        if domain != "kpkt.gov.my":
            raise ValidationError(
                "Pendaftaran hanya dibenarkan menggunakan emel @kpkt.gov.my."
            )

        existing_user = db.session.scalar(
            db.select(User).where(
                User.email == email
            )
        )

        if existing_user is not None:
            raise ValidationError(
                "Alamat emel ini telah didaftarkan."
            )

    def validate_identification_no(self, field):
        existing_user = db.session.scalar(
            db.select(User).where(
                User.identification_no == field.data.strip()
            )
        )

        if existing_user is not None:
            raise ValidationError(
                "No Pengenalan ini telah didaftarkan."
            )
            
# Form untuk Login
class LoginForm(FlaskForm):
    email = StringField(
        "Alamat Emel",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Kata Laluan",
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField("Log Masuk")