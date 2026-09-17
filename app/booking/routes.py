from datetime import datetime, timezone

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    url_for,
    )
from flask_login import current_user, login_required

from app.booking import booking_bp
from app.booking.forms import BookingForm, CancelOwnBookingForm
from app.extensions import db
from app.models import Booking, Room

from app.decorators import applicant_required

from app.booking.services import has_booking_conflict

@booking_bp.route("/create", methods=["GET", "POST"])
@login_required
# @applicant_required

# ================Cipta Tempahan==========================
def create_booking():
    form = BookingForm()

    active_rooms = db.session.scalars(
        db.select(Room)
        .where(Room.is_active.is_(True))
        .order_by(Room.room_name)
    ).all()

    form.room_id.choices = [
        (
            room.id,
            f"{room.room_name} - {room.location}"
        )
        for room in active_rooms
    ]

    if form.validate_on_submit():
        start_datetime = datetime.combine(
            form.start_date.data,
            form.start_time.data
        )

        end_datetime = datetime.combine(
            form.end_date.data,
            form.end_time.data
        )

        if end_datetime <= start_datetime:
            flash(
                "Tarikh dan masa tamat mestilah selepas "
                "tarikh dan masa mula.",
                "danger"
            )

            return render_template(
                "booking/create.html",
                form=form
            )

        room = db.session.get(
            Room,
            form.room_id.data
        )

        if room is None or not room.is_active:
            flash(
                "Bilik yang dipilih tidak tersedia.",
                "danger"
            )

            return render_template(
                "booking/create.html",
                form=form
            )
            
        if has_booking_conflict( room_id=room.id, start_datetime=start_datetime, end_datetime=end_datetime):
            flash(
                "Bilik ini telah ditempah pada tarikh dan masa "
                "yang dipilih. Sila pilih waktu atau bilik lain.",
                "danger"
            )

            return render_template(
                "booking/create.html",
                form=form
            )
            
        booking = Booking(
            applicant_id=current_user.id,
            room_id=room.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            purpose=form.purpose.data.strip(),
            status="PENDING"
        )

        db.session.add(booking)
        db.session.commit()

        flash(
            "Permohonan tempahan berjaya dihantar "
            "dan sedang menunggu kelulusan.",
            "success"
        )

        return redirect(
            url_for("booking.my_bookings")
        )

    return render_template(
        "booking/create.html",
        form=form
    )

# ====================Manage Tempahan Sendiri==================
@booking_bp.route("/my")
@login_required
# @applicant_required
def my_bookings():
    bookings = db.session.scalars(
        db.select(Booking)
        .where(
            Booking.applicant_id == current_user.id
        )
        .order_by(
            Booking.start_datetime.desc()
        )
    ).all()

    return render_template(
        "booking/my_bookings.html",
        bookings=bookings
    )
    
# ====================Cancel Own Booking====================
@booking_bp.route(
    "/<int:booking_id>/cancel",
    methods=["GET", "POST"]
)
@login_required
def cancel_own_booking(booking_id):
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.applicant_id != current_user.id:
        abort(403)

    if booking.status not in {
        "PENDING",
        "APPROVED"
    }:
        flash(
            "Tempahan ini tidak boleh dibatalkan.",
            "warning"
        )

        return redirect(
            url_for("booking.my_bookings")
        )

    form = CancelOwnBookingForm()

    if form.validate_on_submit():
        booking.status = "CANCELLED"
        booking.cancelled_by_id = current_user.id
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = form.reason.data.strip()

        db.session.commit()

        flash(
            "Tempahan anda telah dibatalkan.",
            "success"
        )

        return redirect(
            url_for("booking.my_bookings")
        )

    return render_template(
        "booking/cancel.html",
        booking=booking,
        form=form
    )