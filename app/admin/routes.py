from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.models import Booking, Room, User
from sqlalchemy import func, or_
from datetime import datetime, timezone
from app.admin import admin_bp
# from app.admin.forms import RoomForm, ToggleRoomForm
from app.decorators import admin_required
from app.extensions import db

from app.booking.services import (
    has_booking_conflict,
    mark_completed_bookings,
    mark_expired_bookings,
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

# ========================
# User Management
# ========================
@admin_bp.route("/users")
@login_required
@admin_required
def users():

    # ========================
    # Filter Status
    # ========================
    selected_status = (
        request.args.get("status", "ALL")
        .strip()
        .upper()
    )

    valid_statuses = {
        "ALL",
        "ACTIVE",
        "INACTIVE",
    }

    if selected_status not in valid_statuses:
        selected_status = "ALL"

    # ========================
    # Filter Role
    # ========================
    selected_role = (
        request.args.get("role", "ALL")
        .strip()
        .upper()
    )

    valid_roles = {
        "ALL",
        "ADMIN",
        "APPLICANT",
    }

    if selected_role not in valid_roles:
        selected_role = "ALL"

    # ========================
    # Search
    # ========================
    search_query = request.args.get("q", "").strip()
    search_text = search_query.lower()

    statement = db.select(User)

    if selected_status == "ACTIVE":
        statement = statement.where(
            User.is_active.is_(True)
        )

    elif selected_status == "INACTIVE":
        statement = statement.where(
            User.is_active.is_(False)
        )

    if selected_role != "ALL":
        statement = statement.where(
            User.role == selected_role
        )

    if search_text:
        search_pattern = f"%{search_text}%"

        search_conditions = [
            func.lower(User.full_name).like(search_pattern),
            func.lower(User.email).like(search_pattern),
            func.lower(User.division_name).like(search_pattern),
            func.lower(User.unit_name).like(search_pattern),
            User.identification_no.like(search_pattern),
        ]

        if search_query.isdigit():
            search_conditions.append(
                User.id == int(search_query)
            )

        statement = statement.where(
            or_(*search_conditions)
        )

    users = db.session.scalars(
        statement.order_by(
            User.full_name.asc()
        )
    ).all()

    # ========================
    # Status Counts
    # ========================
    active_user_count = db.session.scalar(
        db.select(func.count(User.id)).where(
            User.is_active.is_(True)
        )
    ) or 0

    inactive_user_count = db.session.scalar(
        db.select(func.count(User.id)).where(
            User.is_active.is_(False)
        )
    ) or 0

    user_counts = {
        "ALL": active_user_count + inactive_user_count,
        "ACTIVE": active_user_count,
        "INACTIVE": inactive_user_count,
    }

    # ========================
    # Role Counts
    # ========================
    role_rows = db.session.execute(
        db.select(
            User.role,
            func.count(User.id)
        )
        .group_by(User.role)
    ).all()

    raw_role_counts = {
        role: count
        for role, count in role_rows
    }

    role_counts = {
        "ALL": sum(raw_role_counts.values()),
        "ADMIN": raw_role_counts.get("ADMIN", 0),
        "APPLICANT": raw_role_counts.get("APPLICANT", 0),
    }

    status_form = UserStatusForm()

    return render_template(
        "admin/users.html",
        users=users,
        status_form=status_form,
        selected_status=selected_status,
        selected_role=selected_role,
        search_query=search_query,
        user_counts=user_counts,
        role_counts=role_counts,
    )


# ========================
# User Detail
# ========================
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

    status_form = UserStatusForm()

    return render_template(
        "admin/user_detail.html",
        user=user,
        status_form=status_form
    )


# ========================
# Edit User
# ========================
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


# ========================
# Toggle User Status
# ========================
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


# ========================
# Room Management
# ========================
@admin_bp.route("/rooms")
@login_required
@admin_required
def rooms():

    # ========================
    # Filter Status
    # ========================
    selected_status = (
        request.args.get("status", "ALL")
        .strip()
        .upper()
    )

    valid_statuses = {
        "ALL",
        "ACTIVE",
        "INACTIVE",
    }

    if selected_status not in valid_statuses:
        selected_status = "ALL"

    # ========================
    # Search
    # ========================
    search_query = request.args.get("q", "").strip()
    search_text = search_query.lower()

    statement = db.select(Room)

    if selected_status == "ACTIVE":
        statement = statement.where(
            Room.is_active.is_(True)
        )

    elif selected_status == "INACTIVE":
        statement = statement.where(
            Room.is_active.is_(False)
        )

    if search_text:
        search_pattern = f"%{search_text}%"

        search_conditions = [
            func.lower(Room.room_name).like(search_pattern),
            func.lower(Room.location).like(search_pattern),
        ]

        if search_query.isdigit():
            search_number = int(search_query)

            search_conditions.extend([
                Room.id == search_number,
                Room.capacity == search_number,
            ])

        statement = statement.where(
            or_(*search_conditions)
        )

    rooms = db.session.scalars(
        statement.order_by(Room.room_name)
    ).all()

    # ========================
    # Status Counts
    # ========================
    active_room_count = db.session.scalar(
        db.select(func.count(Room.id)).where(
            Room.is_active.is_(True)
        )
    ) or 0

    inactive_room_count = db.session.scalar(
        db.select(func.count(Room.id)).where(
            Room.is_active.is_(False)
        )
    ) or 0

    room_counts = {
        "ALL": active_room_count + inactive_room_count,
        "ACTIVE": active_room_count,
        "INACTIVE": inactive_room_count,
    }

    toggle_form = ToggleRoomForm()

    return render_template(
        "admin/rooms.html",
        rooms=rooms,
        toggle_form=toggle_form,
        selected_status=selected_status,
        search_query=search_query,
        room_counts=room_counts,
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

    if not form.validate_on_submit():
        abort(400)
            
    room.is_active = not room.is_active

    db.session.commit()

    if room.is_active:
        message = "Bilik telah diaktifkan semula."
    else:
        message = "Bilik telah dinyahaktifkan."

    flash(message,"success")

    return redirect(
        url_for("admin.rooms")
    )


# ========================
# Booking Management
# ========================
@admin_bp.route("/bookings")
@login_required
@admin_required
def bookings():
    mark_completed_bookings()
    mark_expired_bookings()

    # ========================
    # Filter Status
    # ========================
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
        "EXPIRED",
    }

    if selected_status not in valid_statuses:
        selected_status = "ALL"

    # ========================
    # Search
    # ========================
    search_query = request.args.get("q", "").strip()
    search_text = search_query.lower()

    statement = db.select(Booking)

    if selected_status != "ALL":
        statement = statement.where(
            Booking.status == selected_status
        )

    if search_text:
        search_pattern = f"%{search_text}%"

        search_conditions = [
            func.lower(Booking.purpose).like(search_pattern),
            Booking.applicant.has(
                func.lower(User.full_name).like(search_pattern)
            ),
            Booking.applicant.has(
                func.lower(User.email).like(search_pattern)
            ),
            Booking.room.has(
                func.lower(Room.room_name).like(search_pattern)
            ),
            Booking.room.has(
                func.lower(Room.location).like(search_pattern)
            ),
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
            Booking.created_at.desc()
        )
    ).all()

    # ========================
    # Status Counts
    # ========================
    status_rows = db.session.execute(
        db.select(
            Booking.status,
            func.count(Booking.id)
        )
        .group_by(Booking.status)
    ).all()

    status_counts = {
        status: count
        for status, count in status_rows
    }

    booking_counts = {
        "ALL": sum(status_counts.values()),
        "PENDING": status_counts.get("PENDING", 0),
        "APPROVED": status_counts.get("APPROVED", 0),
        "COMPLETED": status_counts.get("COMPLETED", 0),
        "REJECTED": status_counts.get("REJECTED", 0),
        "CANCELLED": status_counts.get("CANCELLED", 0),
        "EXPIRED": status_counts.get("EXPIRED", 0),
    }

    action_form = BookingActionForm()

    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        action_form=action_form,
        selected_status=selected_status,
        search_query=search_query,
        booking_counts=booking_counts,
    )


# ========================
# Approve Booking
# ========================
@admin_bp.route(
    "/bookings/<int:booking_id>/approve",
    methods=["POST"]
)
@login_required
@admin_required
def approve_booking(booking_id):
    mark_completed_bookings()
    mark_expired_bookings()

    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    form = BookingActionForm()

    if not form.validate_on_submit():
        abort(400)

    if booking.status == "EXPIRED":
        flash(
            "Permohonan ini telah tamat tempoh dan tidak boleh diluluskan.",
            "warning"
        )

        return redirect(
            url_for("admin.bookings")
        )

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
    booking.approved_at = datetime.now(timezone.utc)

    db.session.commit()

    flash(
        "Permohonan tempahan berjaya diluluskan.",
        "success"
    )

    return redirect(
        url_for("admin.bookings")
    )


# ========================
# Reject Booking
# ========================
@admin_bp.route(
    "/bookings/<int:booking_id>/reject",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def reject_booking(booking_id):
    mark_completed_bookings()
    mark_expired_bookings()

    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.status == "EXPIRED":
        flash(
            "Permohonan ini telah tamat tempoh dan tidak boleh ditolak.",
            "warning"
        )

        return redirect(
            url_for("admin.bookings")
        )

    if booking.status != "PENDING":
        flash(
            "Hanya permohonan berstatus PENDING boleh ditolak.",
            "warning"
        )

        return redirect(
            url_for("admin.bookings")
        )

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

        return redirect(
            url_for("admin.bookings")
        )

    return render_template(
        "admin/reject_booking.html",
        booking=booking,
        form=form
    )


# ========================
# Cancel Booking
# ========================
@admin_bp.route(
    "/bookings/<int:booking_id>/cancel",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def cancel_booking(booking_id):
    mark_completed_bookings()
    mark_expired_bookings()

    booking = db.session.get(
        Booking,
        booking_id
    )

    if booking is None:
        abort(404)

    if booking.status == "EXPIRED":
        flash(
            "Tempahan ini telah tamat tempoh dan tidak boleh dibatalkan.",
            "warning"
        )

        return redirect(
            url_for("admin.bookings")
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
            url_for("admin.bookings")
        )

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

        return redirect(
            url_for("admin.bookings")
        )

    return render_template(
        "admin/cancel_booking.html",
        booking=booking,
        form=form
    )
