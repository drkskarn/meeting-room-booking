from datetime import datetime, timezone

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user, login_required

from sqlalchemy import func, or_

from app.booking import booking_bp
from app.booking.forms import (
    BookingForm, 
    CancelOwnBookingForm,
    EditBookingForm,
)

from app.extensions import db

from app.models import Booking, Room


from app.booking.services import (
    get_malaysia_now,
    get_room_statuses,
    has_booking_conflict,
    mark_completed_bookings,
    mark_expired_bookings,
)

# ========================
# Create Tempahan
# ========================
@booking_bp.route("/create", methods=["GET", "POST"])
@login_required
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
            
        if has_booking_conflict(
            room_id=room.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        ):
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
            chairperson_name=(
                form.chairperson_name.data or ""
            ).strip() or None,
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

# ========================
# Manage Own Booking
# ========================
@booking_bp.route("/my")
@login_required
def my_bookings():
    mark_completed_bookings()
    mark_expired_bookings()

    selected_status = (
        request.args.get("status", "ALL")
        .strip()
        .upper()
    )

    valid_statuses = {
        "ALL",
        "PENDING",
        "APPROVED",
        "COMPLETED",
        "REJECTED",
        "CANCELLED",
        "EXPIRED"
    }

    if selected_status not in valid_statuses:
        selected_status = "ALL"

    search_query = request.args.get("q", "").strip()
    search_text = search_query.lower()

    statement = db.select(Booking).where(
        Booking.applicant_id == current_user.id
    )

    if selected_status != "ALL":
        statement = statement.where(
            Booking.status == selected_status
        )

    if search_text:
        pattern = f"%{search_text}%"

        search_conditions = [
            func.lower(Booking.purpose).like(pattern),
            func.lower(Booking.chairperson_name).like(pattern),
            Booking.room.has(
                func.lower(Room.room_name).like(pattern)
            ),
            Booking.room.has(
                func.lower(Room.location).like(pattern)
            )
        ]

        if search_query.isdigit():
            search_conditions.append(
                Booking.id == int(search_query)
            )

        statement = statement.where(
            or_(*search_conditions)
        )

    bookings = db.session.scalars(
        statement.order_by(
            Booking.start_datetime.desc()
        )
    ).all()

    status_rows = db.session.execute(
        db.select(
            Booking.status,
            func.count(Booking.id)
        )
        .where(
            Booking.applicant_id == current_user.id
        )
        .group_by(Booking.status)
    ).all()

    booking_counts = {
        "ALL": sum(count for _, count in status_rows),
        "PENDING": 0,
        "APPROVED": 0,
        "COMPLETED": 0,
        "REJECTED": 0,
        "CANCELLED": 0,
        "EXPIRED": 0
    }

    for status, count in status_rows:
        if status in booking_counts:
            booking_counts[status] = count

    return render_template(
        "booking/my_bookings.html",
        bookings=bookings,
        selected_status=selected_status,
        search_query=search_query,
        booking_counts=booking_counts
    )

# ========================
# Booking Detail
# ========================
@booking_bp.route("/<int:booking_id>")
@login_required
def booking_detail(booking_id):
    
    mark_completed_bookings()
    mark_expired_bookings()
    
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


# ========================
# Edit Booking
# ========================
@booking_bp.route(
    "/<int:booking_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_booking(booking_id):
    
    mark_completed_bookings()
    mark_expired_bookings()
    
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
    
    #EXPIRED akan paparkan mesej yang jelas
    if booking.status == "EXPIRED":
    
        flash(
            "Tempahan ini telah tamat tempoh dan tidak boleh dikemaskini.",
            "warning"
        )

        return redirect(
            url_for(
                "booking.booking_detail",
                booking_id=booking.id
            )
        )

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
        booking.chairperson_name = (
            form.chairperson_name.data or ""
        ).strip() or None

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
        form.chairperson_name.data = booking.chairperson_name

    return render_template(
        "booking/edit.html",
        booking=booking,
        form=form
    )
    
# ========================
# Cancel Own Booking
# ========================
@booking_bp.route(
    "/<int:booking_id>/cancel",
    methods=["GET", "POST"]
)
@login_required
def cancel_own_booking(booking_id):
    
    mark_completed_bookings()
    mark_expired_bookings()
    
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.applicant_id != current_user.id:
        abort(403)

    if booking.status == "EXPIRED":
        flash(
            "Tempahan ini telah tamat tempoh dan tidak boleh dibatalkan.",
            "warning"
        )

        return redirect(
            url_for("booking.my_bookings")
        )
    
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
    
# ========================
# KETERSEDIAAN BILIK
# ========================

@booking_bp.route("/availability")
@login_required
def room_availability():

    # Pastikan lifecycle booking dikemaskini dahulu
    mark_completed_bookings()
    mark_expired_bookings()

    now = get_malaysia_now()

    room_statuses = get_room_statuses(now)

    # ========================
    # FILTER STATUS
    # ========================

    selected_status = (
        request.args.get(
            "status",
            "ALL"
        )
        .strip()
        .upper()
    )

    valid_statuses = {
        "ALL",
        "AVAILABLE",
        "IN_USE",
        "UPCOMING"
    }

    if selected_status not in valid_statuses:
        selected_status = "ALL"


    # ========================
    # SEARCH
    # ========================

    search_query = (
        request.args.get(
            "q",
            ""
        )
        .strip()
    )

    search_text = search_query.lower()


    # ========================
    # FILTER DATA
    # ========================

    filtered_rooms = room_statuses

    if selected_status == "AVAILABLE":
        filtered_rooms = [
            item
            for item in filtered_rooms
            if item["status"] == "AVAILABLE"
        ]

    elif selected_status == "IN_USE":
        filtered_rooms = [
            item
            for item in filtered_rooms
            if item["status"] == "IN_USE"
        ]

    elif selected_status == "UPCOMING":
        filtered_rooms = [
            item
            for item in filtered_rooms
            if item["upcoming_bookings"]
        ]

    if search_text:
        filtered_rooms = [
            item
            for item in filtered_rooms
            if (
                search_text in item["room"].room_name.lower()
                or (
                    item["room"].location
                    and search_text in item["room"].location.lower()
                )
            )
        ]


    # ========================
    # SUMMARY
    # ========================

    available_room_count = sum(
        1
        for item in room_statuses
        if item["status"] == "AVAILABLE"
    )

    in_use_room_count = sum(
        1
        for item in room_statuses
        if item["status"] == "IN_USE"
    )

    upcoming_room_count = sum(
        1
        for item in room_statuses
        if item["upcoming_bookings"]
    )


    return render_template(
        "booking/availability.html",

        room_statuses=filtered_rooms,

        selected_status=selected_status,
        search_query=search_query,

        available_room_count=available_room_count,
        in_use_room_count=in_use_room_count,
        upcoming_room_count=upcoming_room_count
    )