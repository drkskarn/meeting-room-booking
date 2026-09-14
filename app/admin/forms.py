from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


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