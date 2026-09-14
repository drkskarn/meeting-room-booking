from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.admin import admin_bp
from app.admin.forms import RoomForm, ToggleRoomForm
from app.decorators import admin_required
from app.extensions import db
from app.models import Room

from datetime import datetime, timezone

from app.admin.forms import (
    BookingActionForm,
    RoomForm,
    ToggleRoomForm,
)

from app.booking.services import has_booking_conflict
from app.models import Booking, Room

@admin_bp.route("/rooms")
@login_required
@admin_required
def rooms():
    rooms = db.session.scalars(
        db.select(Room).order_by(Room.room_name)
    ).all()

    toggle_form = ToggleRoomForm()

    return render_template(
        "admin/rooms.html",
        rooms=rooms,
        toggle_form=toggle_form
    )


@admin_bp.route("/rooms/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_room():
    form = RoomForm()

    if form.validate_on_submit():
        room_name = form.room_name.data.strip()

        existing_room = db.session.scalar(
            db.select(Room).where(
                func.lower(Room.room_name)
                == room_name.lower()
            )
        )

        if existing_room is not None:
            flash(
                "Nama bilik ini telah wujud.",
                "danger"
            )

            return render_template(
                "admin/room_form.html",
                form=form,
                title="Tambah Bilik"
            )

        room = Room(
            room_name=room_name,
            location=form.location.data.strip(),
            capacity=form.capacity.data,
            is_active=True
        )

        db.session.add(room)
        db.session.commit()

        flash(
            "Bilik mesyuarat berjaya ditambah.",
            "success"
        )

        return redirect(
            url_for("admin.rooms")
        )

    return render_template(
        "admin/room_form.html",
        form=form,
        title="Tambah Bilik"
    )

@admin_bp.route(
    "/rooms/<int:room_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def edit_room(room_id):
    room = db.session.get(Room, room_id)

    if room is None:
        abort(404)

    form = RoomForm(obj=room)

    if form.validate_on_submit():
        room_name = form.room_name.data.strip()

        existing_room = db.session.scalar(
            db.select(Room).where(
                func.lower(Room.room_name)
                == room_name.lower(),
                Room.id != room.id
            )
        )

        if existing_room is not None:
            flash(
                "Nama bilik ini telah digunakan oleh bilik lain.",
                "danger"
            )

            return render_template(
                "admin/room_form.html",
                form=form,
                title="Kemaskini Bilik"
            )

        room.room_name = room_name
        room.location = form.location.data.strip()
        room.capacity = form.capacity.data

        db.session.commit()

        flash(
            "Maklumat bilik berjaya dikemaskini.",
            "success"
        )

        return redirect(
            url_for("admin.rooms")
        )

    return render_template(
        "admin/room_form.html",
        form=form,
        title="Kemaskini Bilik"
    )


@admin_bp.route(
    "/rooms/<int:room_id>/toggle",
    methods=["POST"]
)
@login_required
@admin_required
def toggle_room(room_id):
    room = db.session.get(Room, room_id)

    if room is None:
        abort(404)

    form = ToggleRoomForm()

    if form.validate_on_submit():
        room.is_active = not room.is_active

        db.session.commit()

        if room.is_active:
            message = "Bilik telah diaktifkan semula."
        else:
            message = "Bilik telah dinyahaktifkan."

        flash(
            message,
            "success"
        )

    return redirect(
        url_for("admin.rooms")
    )

@admin_bp.route("/bookings")
@login_required
@admin_required
def bookings():
    bookings = db.session.scalars(
        db.select(Booking)
        .order_by(
            Booking.created_at.desc()
        )
    ).all()

    action_form = BookingActionForm()

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        action_form=action_form
    )

@admin_bp.route(
    "/bookings/<int:booking_id>/approve",
    methods=["POST"]
)
@login_required
@admin_required
def approve_booking(booking_id):
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    form = BookingActionForm()

    if not form.validate_on_submit():
        abort(400)

    if booking.status != "PENDING":
        flash(
            "Hanya permohonan berstatus PENDING "
            "boleh diluluskan.",
            "warning"
        )

        return redirect(
            url_for("admin.bookings")
        )

    room = booking.room

    if not room.is_active:
        flash(
            "Permohonan tidak boleh diluluskan kerana "
            "bilik ini tidak aktif.",
            "danger"
        )

        return redirect(
            url_for("admin.bookings")
        )

    if has_booking_conflict(
        room_id=booking.room_id,
        start_datetime=booking.start_datetime,
        end_datetime=booking.end_datetime,
        exclude_booking_id=booking.id
    ):
        flash(
            "Permohonan tidak boleh diluluskan kerana "
            "bilik telah ditempah pada waktu tersebut.",
            "danger"
        )

        return redirect(
            url_for("admin.bookings")
        )

    booking.status = "APPROVED"

    booking.approved_by_id = current_user.id

    booking.approved_at = datetime.now(
        timezone.utc
    )

    db.session.commit()

    flash(
        "Permohonan tempahan berjaya diluluskan.",
        "success"
    )

    return redirect(
        url_for("admin.bookings")
    )