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
from app.booking.forms import (
    BookingForm, 
    CancelOwnBookingForm,
    EditBookingForm,
)

from app.extensions import db

from app.models import Booking, Room

from app.decorators import applicant_required

from app.booking.services import (
    has_booking_conflict,
    mark_completed_bookings,
)

@booking_bp.route("/create", methods=["GET", "POST"])
@login_required
# @applicant_required

# ================Create Tempahan==========================
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

# ====================Manage Own Booking==================
@booking_bp.route("/my")
@login_required
# @applicant_required
def my_bookings():
    
    mark_completed_bookings()
    
    bookings = db.session.scalars(
        db.select(Booking)
        .where(
            Booking.applicant_id == current_user.id
        )
        .order_by(
            Booking.start_datetime.desc()
        )
    ).all()

    return render_template("booking/my_bookings.html", bookings=bookings)

# ========================Edit Own Booking=========================
@booking_bp.route("/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    
    mark_completed_bookings()
    
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if (
        current_user.role != "ADMIN"
        and booking.applicant_id != current_user.id
    ):
        abort(403)

    return render_template("booking/detail.html", booking=booking)

@booking_bp.route(
    "/<int:booking_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_booking(booking_id):
    
    mark_completed_bookings()
    
    booking = db.session.get(
        Booking,
        booking_id
    )

    # Booking ID tidak wujud
    if booking is None:
        abort(404)

    # User biasa hanya boleh akses booking sendiri
    if (
        current_user.role != "ADMIN"
        and booking.applicant_id != current_user.id
    ):
        abort(403)

    # REJECTED / CANCELLED / COMPLETED tidak boleh diedit
    if booking.status not in {
        "PENDING",
        "APPROVED"
    }:
        flash(
            "Tempahan ini tidak boleh dikemaskini.",
            "warning"
        )

        return redirect(
            url_for(
                "booking.booking_detail",
                booking_id=booking.id
            )
        )

    # Applicant hanya boleh edit booking PENDING
    if (
        current_user.role != "ADMIN"
        and booking.status != "PENDING"
    ):
        flash(
            "Tempahan yang telah diluluskan tidak boleh "
            "dikemaskini oleh pemohon. "
            "Sila hubungi Pentadbir jika perubahan diperlukan.",
            "warning"
        )

        return redirect(
            url_for(
                "booking.booking_detail",
                booking_id=booking.id
            )
        )

    form = EditBookingForm()

    # Hanya bilik aktif dipaparkan
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

        # Masa tamat mesti selepas masa mula
        if end_datetime <= start_datetime:
            flash(
                "Tarikh dan masa tamat mestilah selepas "
                "tarikh dan masa mula.",
                "danger"
            )

            return render_template(
                "booking/edit.html",
                booking=booking,
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
                "booking/edit.html",
                booking=booking,
                form=form
            )

        # Check conflict untuk PENDING dan APPROVED
        if has_booking_conflict(
            room_id=room.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            exclude_booking_id=booking.id
        ):
            flash(
                "Perubahan tidak boleh disimpan kerana "
                "bilik telah ditempah pada waktu tersebut.",
                "danger"
            )

            return render_template(
                "booking/edit.html",
                booking=booking,
                form=form
            )

        booking.room_id = room.id
        booking.start_datetime = start_datetime
        booking.end_datetime = end_datetime
        booking.purpose = form.purpose.data.strip()

        db.session.commit()

        flash(
            "Tempahan berjaya dikemaskini.",
            "success"
        )

        return redirect(
            url_for(
                "booking.booking_detail",
                booking_id=booking.id
            )
        )

    # Isi form dengan data booking sedia ada
    if not form.is_submitted():
        form.room_id.data = booking.room_id
        form.start_date.data = booking.start_datetime.date()
        form.start_time.data = booking.start_datetime.time()
        form.end_date.data = booking.end_datetime.date()
        form.end_time.data = booking.end_datetime.time()
        form.purpose.data = booking.purpose

    return render_template(
        "booking/edit.html",
        booking=booking,
        form=form
    )
    
# ====================Cancel Own Booking====================
@booking_bp.route(
    "/<int:booking_id>/cancel",
    methods=["GET", "POST"]
)
@login_required
def cancel_own_booking(booking_id):
    
    mark_completed_bookings()
    
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