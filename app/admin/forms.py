from flask_wtf import FlaskForm
# from wtforms import IntegerField, StringField, SubmitField
# from wtforms.validators import DataRequired, Length, NumberRange

from flask_wtf import FlaskForm
from wtforms import (
    IntegerField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
)

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