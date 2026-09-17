from flask_wtf import FlaskForm
# from wtforms import IntegerField, StringField, SubmitField
# from wtforms.validators import DataRequired, Length, NumberRange

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    SelectField,
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
    EqualTo,
)

# =================================Bagi pengurusan bilik mesyuarat========================
class RoomForm(FlaskForm):
    room_name = StringField(
        "Nama Bilik",
        validators=[
            DataRequired(),
            Length(min=2, max=255)
        ]
    )

    location = StringField(
        "Lokasi",
        validators=[
            DataRequired(),
            Length(min=2, max=255)
        ]
    )

    capacity = IntegerField(
        "Kapasiti",
        validators=[
            DataRequired(),
            NumberRange(
                min=1,
                message="Kapasiti mestilah sekurang-kurangnya 1."
            )
        ]
    )

    submit = SubmitField("Simpan")


class ToggleRoomForm(FlaskForm):
    submit = SubmitField("Kemaskini Status")
    
class BookingActionForm(FlaskForm):
    submit = SubmitField("Sahkan")
    
class RejectBookingForm(FlaskForm):
    reason = TextAreaField(
        "Sebab Penolakan",
        validators=[
            DataRequired(),
            Length(max=1000)
        ]
    )

    submit = SubmitField("Tolak Permohonan")


class CancelBookingForm(FlaskForm):
    reason = TextAreaField(
        "Sebab Pembatalan",
        validators=[
            DataRequired(),
            Length(max=1000)
        ]
    )

    submit = SubmitField("Batalkan Tempahan")

# =========================bagi pengurusan akaun pengguna===========================
class AdminEditUserForm(FlaskForm):
    email = StringField(
        "Alamat Emel",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    full_name = StringField(
        "Nama Penuh",
        validators=[
            DataRequired(),
            Length(min=3, max=255)
        ]
    )

    identification_no = StringField(
        "No Pengenalan",
        validators=[
            Optional(),
            Regexp(
                r"^\d{12}$",
                message="No Pengenalan mestilah tepat 12 digit nombor."
            )
        ]
    )
    
    new_password = PasswordField(
        "Kata Laluan Baru",
        validators=[
            Optional(),
            Length(
                min=8,
                message="Kata laluan mestilah sekurang-kurangnya 8 aksara."
            )
        ]
    )

    confirm_password = PasswordField(
        "Sahkan Kata Laluan Baru",
        validators=[
            Optional(),
            EqualTo(
                "new_password",
                message="Kata laluan baru tidak sepadan."
            )
        ]
    )
    
    division_name = StringField(
        "Nama Bahagian",
        validators=[
            Optional(),
            Length(max=255)
        ]
    )

    unit_name = StringField(
        "Nama Cawangan/Unit",
        validators=[
            Optional(),
            Length(max=255)
        ]
    )

    role = SelectField(
        "Peranan",
        choices=[
            ("APPLICANT", "Pemohon"),
            ("ADMIN", "Pentadbir Sistem"),
        ],
        validators=[
            DataRequired()
        ]
    )

    submit = SubmitField("Simpan Perubahan")

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
                "Alamat emel mestilah menggunakan domain @kpkt.gov.my."
            )


class UserStatusForm(FlaskForm):
    submit = SubmitField("Kemaskini Status")