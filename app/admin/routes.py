from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from app.models import Booking, Room, User
from sqlalchemy import func
from datetime import datetime, timezone
from app.admin import admin_bp
# from app.admin.forms import RoomForm, ToggleRoomForm
from app.decorators import admin_required
from app.extensions import db

from app.booking.services import (
    has_booking_conflict,
    mark_completed_bookings,
)

from app.admin.forms import (
    AdminEditUserForm,
    BookingActionForm,
    CancelBookingForm,
    RejectBookingForm,
    RoomForm,
    ToggleRoomForm,
    UserStatusForm,
)

# =====================Route Bagi User Management====================
@admin_bp.route("/users")
@login_required
@admin_required
def users():
    users = db.session.scalars(
        db.select(User)
        .order_by(User.full_name)
    ).all()

    status_form = UserStatusForm()

    return render_template(
        "admin/users.html",
        users=users,
        status_form=status_form
    )

@admin_bp.route("/users/<int:user_id>")
@login_required
@admin_required
def user_detail(user_id):
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    return render_template(
        "admin/user_detail.html",
        user=user
    )

@admin_bp.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    form = AdminEditUserForm(obj=user)

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        existing_email = db.session.scalar(
            db.select(User).where(
                func.lower(User.email) == email,
                User.id != user.id
            )
        )

        if existing_email is not None:
            flash(
                "Alamat emel ini telah digunakan oleh akaun lain.",
                "danger"
            )

            return render_template(
                "admin/user_form.html",
                user=user,
                form=form
            )

        identification_no = (
            form.identification_no.data.strip()
            if form.identification_no.data
            else None
        )

        if identification_no:
            existing_id = db.session.scalar(
                db.select(User).where(
                    User.identification_no == identification_no,
                    User.id != user.id
                )
            )

            if existing_id is not None:
                flash(
                    "No Pengenalan ini telah digunakan oleh akaun lain.",
                    "danger"
                )

                return render_template(
                    "admin/user_form.html",
                    user=user,
                    form=form
                )

        # Admin tidak boleh menukar role dirinya sendiri
        if (
            user.id == current_user.id
            and form.role.data != "ADMIN"
        ):
            flash(
                "Anda tidak boleh menukar role akaun Pentadbir "
                "yang sedang digunakan.",
                "danger"
            )

            return render_template(
                "admin/user_form.html",
                user=user,
                form=form
            )

        user.email = email
        user.full_name = form.full_name.data.strip()
        user.identification_no = identification_no

        user.division_name = (
            form.division_name.data.strip()
            if form.division_name.data
            else None
        )

        user.unit_name = (
            form.unit_name.data.strip()
            if form.unit_name.data
            else None
        )

        user.role = form.role.data
        
        password_changed = False
        
        if form.new_password.data:
            user.set_password(form.new_password.data)
            password_changed = True
         
        db.session.commit()

        if password_changed:
            flash(
            "Maklumat pengguna dan kata laluan berjaya dikemaskini.",
            "success"
            )
        else:
            flash(
                "Maklumat pengguna berjaya dikemaskini.",
                "success"
            )

        return redirect(
            url_for(
                "admin.user_detail",
                user_id=user.id
            )
        )

    return render_template(
        "admin/user_form.html",
        user=user,
        form=form
    )
    
@admin_bp.route(
    "/users/<int:user_id>/toggle-status",
    methods=["POST"]
)
@login_required
@admin_required
def toggle_user_status(user_id):
    user = db.session.get(
        User,
        user_id
    )

    if user is None:
        abort(404)

    form = UserStatusForm()

    if not form.validate_on_submit():
        abort(400)

    # Pentadbir tidak boleh disable dirinya sendiri
    if user.id == current_user.id:
        flash(
            "Anda tidak boleh menyahaktifkan akaun "
            "yang sedang digunakan.",
            "danger"
        )

        return redirect(
            url_for("admin.users")
        )

    user.is_active = not user.is_active

    db.session.commit()

    if user.is_active:
        message = "Akaun pengguna telah diaktifkan."
    else:
        message = "Akaun pengguna telah dinyahaktifkan."

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("admin.users")
    )
    
    
# =====================Route Bagi Room===================
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
        if not form.validate_on_submit():
            abort(400)
            
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


# =====================Route Bagi Booking===================
@admin_bp.route("/bookings")
@login_required
@admin_required
def bookings():
    
    mark_completed_bookings()
    
    bookings = db.session.scalars(
        db.select(Booking)
        .order_by(
            Booking.created_at.desc()
        )
    ).all()

    action_form = BookingActionForm()

    return render_template("admin/bookings.html", bookings=bookings, action_form=action_form)

@admin_bp.route(
    "/bookings/<int:booking_id>/approve",
    methods=["POST"]
)
@login_required
@admin_required
def approve_booking(booking_id):
    
    mark_completed_bookings()
    
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

@admin_bp.route(
    "/bookings/<int:booking_id>/reject",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def reject_booking(booking_id):
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.status != "PENDING":
        flash(
            "Hanya permohonan berstatus PENDING boleh ditolak.",
            "warning"
        )
        return redirect(url_for("admin.bookings"))

    form = RejectBookingForm()

    if form.validate_on_submit():
        booking.status = "REJECTED"
        booking.rejected_by_id = current_user.id
        booking.rejected_at = datetime.now(timezone.utc)
        booking.rejection_reason = form.reason.data.strip()

        db.session.commit()

        flash(
            "Permohonan tempahan telah ditolak.",
            "success"
        )

        return redirect(url_for("admin.bookings"))

    return render_template(
        "admin/reject_booking.html",
        booking=booking,
        form=form
    )

@admin_bp.route(
    "/bookings/<int:booking_id>/cancel",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def cancel_booking(booking_id):
    
    mark_completed_bookings()
    
    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.status not in {
        "PENDING",
        "APPROVED"
    }:
        flash(
            "Tempahan ini tidak boleh dibatalkan.",
            "warning"
        )
        return redirect(url_for("admin.bookings"))

    form = CancelBookingForm()

    if form.validate_on_submit():
        booking.status = "CANCELLED"
        booking.cancelled_by_id = current_user.id
        booking.cancelled_at = datetime.now(timezone.utc)
        booking.cancellation_reason = form.reason.data.strip()

        db.session.commit()

        flash(
            "Tempahan telah dibatalkan.",
            "success"
        )

        return redirect(url_for("admin.bookings"))

    return render_template(
        "admin/cancel_booking.html",
        booking=booking,
        form=form
    )