from pathlib import Path
from uuid import uuid4
from flask import (
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    )
from flask_login import current_user, login_required
from app.models import Booking, Room, User, AuditLog
from sqlalchemy import func, or_
from datetime import datetime, timezone, timedelta
from app.admin import admin_bp
from app.audit import log_audit
from app.decorators import admin_required
from app.extensions import db

from zoneinfo import ZoneInfo

from app.booking.services import (
    has_booking_conflict,
    mark_completed_bookings,
    mark_expired_bookings,
)

from app.admin.forms import (
    AdminEditUserForm,
    AdminAddUserForm,
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
# Add User
# ========================
@admin_bp.route(
    "/users/add",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def add_user():

    form = AdminAddUserForm()

    if form.validate_on_submit():

        email = form.email.data.strip().lower()

        # ========================
        # Duplicate Email Check
        # ========================
        existing_email = db.session.scalar(
            db.select(User).where(
                func.lower(User.email) == email
            )
        )

        if existing_email is not None:
            flash(
                "Alamat emel ini telah digunakan.",
                "danger"
            )

            return render_template(
                "admin/user_form.html",
                user=None,
                form=form,
                mode="add"
            )

        identification_no = (
            form.identification_no.data.strip()
            if form.identification_no.data
            else None
        )

        # ========================
        # Duplicate Identification Check
        # ========================
        if identification_no:

            existing_id = db.session.scalar(
                db.select(User).where(
                    User.identification_no == identification_no
                )
            )

            if existing_id is not None:
                flash(
                    "No Pengenalan ini telah digunakan.",
                    "danger"
                )

                return render_template(
                    "admin/user_form.html",
                    user=None,
                    form=form,
                    mode="add"
                )

        # ========================
        # Create User
        # ========================
        user = User(
            email=email,
            full_name=form.full_name.data.strip(),
            identification_no=identification_no,
            division_name=(
                form.division_name.data.strip()
                if form.division_name.data
                else None
            ),
            unit_name=(
                form.unit_name.data.strip()
                if form.unit_name.data
                else None
            ),
            role=form.role.data,
            is_active=True
        )

        user.set_password(
            form.new_password.data
        )

        db.session.add(user)
        db.session.flush()
        
        log_audit(
                    action="CREATE",
                    entity_type="USER",
                    entity_id=user.id,
                    description=(
                        "Akaun pengguna diwujudkan."
                        )
                )
        
        db.session.commit()

        flash(
            "Akaun pengguna berjaya ditambah.",
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
        user=None,
        form=form,
        mode="add"
    )
    
# ========================
# Edit User
# ========================
def get_changes(old_values, new_values):
    changes = {}

    for field, old_value in old_values.items():
        new_value = new_values.get(field)

        if old_value != new_value:
            changes[field] = {
                "old": old_value,
                "new": new_value,
            }

    return changes

@admin_bp.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@admin_required
def edit_user(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)
        
    old_values = {
            "name": user.full_name,
            "email": user.email,
            "role": user.role,
            "changed_password":False,
            "department": user.division_name,
            "unit": user.unit_name,
        }
    
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

        # Admin tidak boleh menukar role dirinya sendiri
        if (user.id == current_user.id and form.role.data != "ADMIN"):
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
        # user.identification_no = identification_no

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

        new_values = {
                "name": user.full_name,
                "email": user.email,
                "changed_password":password_changed,
                "role": user.role,
                "department": user.division_name,
                "unit": user.unit_name,
            }

        changes = get_changes(old_values, new_values)
        
        # ========================
        # Audit - Edit User
        # ========================
        if changes:

            field_labels = {
                "name": "Nama",
                "email": "Emel",
                "role": "Peranan",
                "department": "Bahagian",
                "unit": "Cawangan/Unit",
            }

            change_lines = []

            for field, values in changes.items():

                if field == "changed_password":
                    change_lines.append(
                        "Kata laluan telah ditukar."
                    )
                    continue

                label = field_labels.get(
                    field,
                    field
                )

                old_value = values["old"] or "-"
                new_value = values["new"] or "-"

                change_lines.append(
                    f"{label}: "
                    f"{old_value} -> {new_value}"
                )

            log_audit(
                action="UPDATE",
                entity_type="USER",
                entity_id=user.id,
                description="; ".join(change_lines)
            )
            
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

    if user.is_active:
        action = "ACTIVATE"
        description = "Akaun pengguna diaktifkan."
    else:
        action = "DEACTIVATE"
        description = "Akaun pengguna dinyahaktifkan."

    log_audit(
        action=action,
        entity_type="USER",
        entity_id=user.id,
        description=description,
    )
    
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
# Room Image Helpers
# ========================
def save_room_image(image_file):
    extension = (
        Path(image_file.filename)
        .suffix
        .lower()
    )

    filename = f"{uuid4().hex}{extension}"

    upload_folder = (
        Path(current_app.static_folder)
        / "images"
        / "rooms"
    )

    upload_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    image_path = upload_folder / filename

    image_file.save(image_path)

    return filename


def delete_room_image(filename):
    if not filename:
        return

    image_path = (
        Path(current_app.static_folder)
        / "images"
        / "rooms"
        / filename
    )

    if image_path.exists():
        image_path.unlink()

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
            flash("Nama bilik ini telah wujud.", "danger")

            return render_template(
                "admin/room_form.html",
                form=form,
                title="Tambah Bilik",
                room=None
            )

        image_filename = None

        if form.image.data:
            image_filename = save_room_image(
                form.image.data
            )

        room = Room(
            room_name=room_name,
            location=form.location.data.strip(),
            capacity=form.capacity.data,
            is_active=True,
            image_filename=image_filename
        )
        # ========================
        # Audit - Create Room
        # ========================
        db.session.add(room)
        db.session.flush()

        log_audit(
            action="CREATE",
            entity_type="ROOM",
            entity_id=room.id,
            description=(
                "Bilik mesyuarat diwujudkan."
                )
            )


        db.session.commit()

        flash("Bilik mesyuarat berjaya ditambah.", "success")

        return redirect(url_for("admin.rooms"))

    return render_template(
        "admin/room_form.html",
        form=form,
        title="Tambah Bilik",
        room=None
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
            flash("Nama bilik ini telah digunakan oleh bilik lain.", "danger")

            return render_template(
                "admin/room_form.html",
                form=form,
                title="Kemaskini Bilik",
                room=room
            )

        # ========================
        # Old Room Values
        # ========================
        old_values = {
            "room_name": room.room_name,
            "location": room.location,
            "capacity": room.capacity,
            "image_changed": False,
        }

        room.room_name = room_name
        room.location = form.location.data.strip()
        room.capacity = form.capacity.data

        old_image_filename = room.image_filename

        if form.image.data: 
            room.image_filename = save_room_image(form.image.data)

        # ========================
        # New Room Values
        # ========================
        new_values = {
            "room_name": room.room_name,
            "location": room.location,
            "capacity": room.capacity,
            "image_changed": bool(form.image.data),
        }

        changes = get_changes(
            old_values,
            new_values,
        )
        
        # ========================
        # Audit - Edit Room
        # ========================
        if changes:

            field_labels = {
                "room_name": "Nama Bilik",
                "location": "Lokasi",
                "capacity": "Kapasiti",
            }

            change_lines = []

            for field, values in changes.items():

                if field == "image_changed": 
                    change_lines.append("Gambar bilik telah ditukar.")
                    continue

                label = field_labels.get(
                    field,
                    field
                )

                change_lines.append(
                    f"{label}: "
                    f"{values['old']} -> "
                    f"{values['new']}"
                )

            log_audit(
                action="UPDATE",
                entity_type="ROOM",
                entity_id=room.id,
                description="; ".join(change_lines)
            )
        db.session.commit()


        # ========================
        # Delete Previous Image
        # ========================
        if (form.image.data and old_image_filename and old_image_filename != room.image_filename):
             delete_room_image(old_image_filename)
        
        flash("Maklumat bilik berjaya dikemaskini.","success")

        return redirect(url_for("admin.rooms"))

    return render_template(
        "admin/room_form.html",
        form=form,
        title="Kemaskini Bilik",
        room=room
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
            
    # ========================
    # Toggle Room Status
    # ========================
    room.is_active = not room.is_active

    if room.is_active:
        action = "ACTIVATE"
        description = "Bilik mesyuarat diaktifkan."
    else:
        action = "DEACTIVATE"
        description = "Bilik mesyuarat dinyahaktifkan."


    # ========================
    # Audit - Toggle Room
    # ========================
    log_audit(
        action=action,
        entity_type="ROOM",
        entity_id=room.id,
        description=description,
    )

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
# Tambah timedelta pada import datetime sedia ada:
# from datetime import datetime, timedelta, timezone


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
    # Search + Date Range
    # ========================
    search_query = request.args.get("q", "").strip()
    search_text = search_query.lower()

    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    date_from_dt = None
    date_to_dt = None
    date_to_exclusive = None
    invalid_period = False

    if date_from:
        try:
            date_from_dt = datetime.strptime(
                date_from,
                "%Y-%m-%d"
            )
        except ValueError:
            flash(
                "Tarikh 'Dari' tidak sah.",
                "warning"
            )
            date_from = ""

    if date_to:
        try:
            date_to_dt = datetime.strptime(
                date_to,
                "%Y-%m-%d"
            )
            date_to_exclusive = date_to_dt + timedelta(days=1)
        except ValueError:
            flash(
                "Tarikh 'Hingga' tidak sah.",
                "warning"
            )
            date_to = ""

    if (
        date_from_dt is not None
        and date_to_dt is not None
        and date_from_dt > date_to_dt
    ):
        flash(
            "Tarikh 'Dari' tidak boleh selepas tarikh 'Hingga'.",
            "warning"
        )
        invalid_period = True

    # Syarat yang dikongsi oleh senarai dan kiraan status.
    common_conditions = []

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

        common_conditions.append(
            or_(*search_conditions)
        )

    # Overlap tempoh:
    # booking.end > Dari
    # booking.start < hari selepas Hingga
    if date_from_dt is not None:
        common_conditions.append(
            Booking.end_datetime > date_from_dt
        )

    if date_to_exclusive is not None:
        common_conditions.append(
            Booking.start_datetime < date_to_exclusive
        )

    # Jika susunan tarikh tidak sah, sengaja pulangkan 0 rekod.
    if invalid_period:
        common_conditions.append(
            Booking.id == -1
        )

    # ========================
    # Booking List
    # ========================
    statement = db.select(Booking)

    if common_conditions:
        statement = statement.where(
            *common_conditions
        )

    if selected_status != "ALL":
        statement = statement.where(
            Booking.status == selected_status
        )

    bookings = db.session.scalars(
        statement.order_by(
            Booking.created_at.desc()
        )
    ).all()

    # ========================
    # Status Counts
    # Mengikut carian teks + tempoh,
    # tetapi tidak dikunci kepada selected_status.
    # ========================
    count_statement = db.select(
        Booking.status,
        func.count(Booking.id)
    )

    if common_conditions:
        count_statement = count_statement.where(
            *common_conditions
        )

    status_rows = db.session.execute(
        count_statement.group_by(Booking.status)
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
        date_from=date_from,
        date_to=date_to,
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

    # ========================
    # Audit - Approve Booking
    # ========================
    log_audit(
        action="APPROVE",
        entity_type="BOOKING",
        entity_id=booking.id,
        description=(
            "Permohonan tempahan diluluskan."
        )
    )

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

        # ========================
        # Audit - Approve Booking
        # ========================
        log_audit(
            action="REJECTED",
            entity_type="BOOKING",
            entity_id=booking.id,
            description=(
                "Permohonan tempahan tidak diluluskan."
            )
        )

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
        
        # ========================
        # Audit - Approve Booking
        # ========================
        log_audit(
            action="CANCELLED",
            entity_type="BOOKING",
            entity_id=booking.id,
            description=(
                "Permohonan tempahan dibatalkan."
            )
        )

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

# ========================
# Audit Log
# ========================
@admin_bp.route("/audit-logs")
@login_required
@admin_required
def audit_logs():

    # ========================
    # Filter Entity Type
    # ========================
    selected_entity = (
        request.args.get(
            "entity_type",
            "ALL"
        )
        .strip()
        .upper()
    )

    valid_entities = {
        "ALL",
        "USER",
        "ROOM",
        "BOOKING",
    }

    if selected_entity not in valid_entities:
        selected_entity = "ALL"

    # ========================
    # Filter Action
    # ========================
    selected_action = (
        request.args.get(
            "action",
            "ALL"
        )
        .strip()
        .upper()
    )

    valid_actions = {
        "ALL",
        "CREATE",
        "UPDATE",
        "ACTIVATE",
        "DEACTIVATE",
        "APPROVE",
        "REJECTED",
        "CANCELLED",
    }

    if selected_action not in valid_actions:
        selected_action = "ALL"
        
    # ========================
    # Search
    # ========================
    search_query = request.args.get(
        "q",
        ""
    ).strip()

    search_text = search_query.lower()
    
    # ========================
    # Filter Date Range
    # ========================
    date_from = request.args.get(
        "date_from",
        ""
    ).strip()

    date_to = request.args.get(
        "date_to",
        ""
    ).strip()

    malaysia_tz = ZoneInfo(
        "Asia/Kuala_Lumpur"
    )

    date_from_utc = None
    date_to_utc = None
    
    date_from_dt = None
    date_to_dt = None
    invalid_period = False
    
    # ========================
    # Convert Malaysia Date
    # To UTC
    # ========================
    if date_from:
        try:
            date_from_dt = datetime.strptime(
                date_from,
                "%Y-%m-%d"
            )

            local_from = date_from_dt.replace(
                tzinfo=malaysia_tz
            )

            date_from_utc = (
                local_from
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

        except ValueError:
            flash(
                "Tarikh 'Dari' tidak sah.",
                "warning"
            )

            date_from = ""
            date_from_dt = None


    if date_to:
        try:
            date_to_dt = datetime.strptime(
                date_to,
                "%Y-%m-%d"
            )

            local_to = (
                date_to_dt
                .replace(
                    tzinfo=malaysia_tz
                )
                + timedelta(days=1)
            )

            date_to_utc = (
                local_to
                .astimezone(timezone.utc)
                .replace(tzinfo=None)
            )

        except ValueError:
            flash(
                "Tarikh 'Hingga' tidak sah.",
                "warning"
            )

            date_to = ""
            date_to_dt = None
    
    # ========================
    # Validate Date Range
    # ========================
    if (
        date_from_dt is not None
        and date_to_dt is not None
        and date_from_dt > date_to_dt
    ):
        flash(
            "Tarikh 'Dari' tidak boleh selepas tarikh 'Hingga'.",
            "warning"
        )

        invalid_period = True
        
    statement = db.select(AuditLog)

    # ========================
    # Apply Search
    # ========================
    if search_text:
        search_pattern = f"%{search_text}%"

        search_conditions = [
            func.lower(AuditLog.action).like(
                search_pattern
            ),
            func.lower(AuditLog.entity_type).like(
                search_pattern
            ),
            func.lower(AuditLog.description).like(
                search_pattern
            ),
        ]

        if search_query.isdigit():
            search_number = int(search_query)

            search_conditions.extend([
                AuditLog.id == search_number,
                AuditLog.entity_id == search_number,
            ])

        statement = statement.where(
            or_(*search_conditions)
        )
        
    # ========================
    # Apply Filters
    # ========================
    if selected_entity != "ALL":
        statement = statement.where(
            AuditLog.entity_type
            == selected_entity
        )
        
    if selected_action != "ALL":
        statement = statement.where(
        AuditLog.action
        == selected_action
    )
        
    if date_from_utc is not None:
        statement = statement.where(
            AuditLog.created_at
            >= date_from_utc
        )

    if date_to_utc is not None:
        statement = statement.where(
            AuditLog.created_at
            < date_to_utc
        )

    if invalid_period:
        statement = statement.where(
        AuditLog.id == -1
    )
        
    audit_logs = db.session.scalars(
        statement.order_by(
            AuditLog.created_at.desc()
        )
    ).all()

    
    return render_template(
        "admin/audit_logs.html",
        audit_logs=audit_logs,
        selected_entity=selected_entity,
        date_from=date_from,
        date_to=date_to,
        search_query=search_query,
        selected_action=selected_action,
        malaysia_tz=malaysia_tz,
        utc_timezone=timezone,
    )