from flask_wtf import FlaskForm

from wtforms import (
    DateField,
    SelectField,
    SubmitField,
    TextAreaField,
    TimeField,
)
from wtforms.validators import DataRequired, Length, ValidationError

# ===============Create Booking=======================
class BookingForm(FlaskForm):
    room_id = SelectField(
        "Bilik Mesyuarat",
        coerce=int,
        validators=[
            DataRequired()
        ]
    )

    start_date = DateField(
        "Tarikh Mula",
        validators=[
            DataRequired()
        ]
    )

    start_time = TimeField(
        "Masa Mula",
        validators=[
            DataRequired()
        ]
    )

    end_date = DateField(
        "Tarikh Tamat",
        validators=[
            DataRequired()
        ]
    )

    end_time = TimeField(
        "Masa Tamat",
        validators=[
            DataRequired()
        ]
    )

    purpose = TextAreaField(
        "Tujuan Penggunaan",
        validators=[
            DataRequired(),
            Length(
                min=5,
                max=1000
            )
        ]
    )

    submit = SubmitField(
        "Hantar Permohonan"
    )
    
# ===============Cancel Own Booking==============
class CancelOwnBookingForm(FlaskForm):
    reason = TextAreaField(
        "Sebab Pembatalan",
        validators=[
            DataRequired(),
            Length(max=1000)
        ]
    )

    submit = SubmitField(
        "Batalkan Tempahan"
    )
    
# =============Edit Own Booking================  
class EditBookingForm(BookingForm):
    submit = SubmitField("Kemaskini Tempahan")