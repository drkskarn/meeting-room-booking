from flask import (
    flash,
    redirect,
    render_template,
    url_for,
    request,
    session,
)

from urllib.parse import urljoin, urlsplit
from datetime import timedelta
import smtplib

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.admin.forms import BookingActionForm

from app.auth.tokens import (
    generate_activation_token,
    verify_activation_token
    )
from app.extensions import db, limiter

from app.models import (
    User,
    Booking,
)
from app.email import send_activation_email
from flask_limiter.util import get_remote_address
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from sqlalchemy import func

from app.booking.services import (
    mark_completed_bookings,
    get_malaysia_now,
    mark_expired_bookings,
    get_room_statuses,
)

# ==========================================================
# Utk Login/Registration
# ==========================================================

# ===========Utk Registration======================
# ========================
# Registration
# ========================
@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            email=(
                form.email.data
                .strip()
                .lower()
            ),
            full_name=(
                form.full_name.data
                .strip()
            ),
            identification_no=(
                form.identification_no.data
                .strip()
            ),
            division_name=(
                form.division_name.data
                .strip()
            ),
            unit_name=(
                form.unit_name.data
                .strip()
            ),
            role="APPLICANT",
            is_active=False
        )

        user.set_password(
            form.password.data
        )


        # ========================
        # Add User To Transaction
        # ========================
        db.session.add(user)

        try:
            # ========================
            # Validate Database Insert
            # ========================
            db.session.flush()


            # ========================
            # Generate Activation Link
            # ========================
            token = generate_activation_token(
                user.email
            )

            activation_url = url_for(
                "auth.activate_account",
                token=token,
                _external=True
            )


            # ========================
            # Send Activation Email
            # ========================
            send_activation_email(
                user,
                activation_url
            )


            # ========================
            # Commit Registration
            # ========================
            db.session.commit()


        except (
            ConnectionRefusedError,
            smtplib.SMTPException,
            OSError,
        ):
            db.session.rollback()

            flash(
                "Pendaftaran tidak dapat diselesaikan "
                "kerana emel pengaktifan gagal dihantar. "
                "Sila cuba semula.",
                "danger"
            )

            return render_template(
                "auth/register.html",
                form=form
            )


        # ========================
        # Registration Success
        # ========================
        flash(
            "Pendaftaran berjaya. "
            "Sila semak emel anda untuk "
            "link pengaktifan.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )


    return render_template(
        "auth/register.html",
        form=form
    )

# ========================
# Account Activation
# ========================
@auth_bp.route("/activate/<token>")
def activate_account(token):
    email = verify_activation_token(
        token
    )

    # ========================
    # Invalid / Expired Token
    # ========================
    if email is None:
        flash(
            "Pautan pengaktifan tidak sah "
            "atau telah tamat tempoh.",
            "danger"
        )

        return redirect(
            url_for("auth.login")
        )


    # ========================
    # Find User
    # ========================
    user = db.session.scalar(
        db.select(User).where(
            User.email == email
        )
    )

    if user is None:
        flash(
            "Akaun tidak ditemui.",
            "danger"
        )

        return redirect(
            url_for("auth.register")
        )


    # ========================
    # Already Activated
    # ========================
    if user.is_active:
        flash(
            "Akaun ini telah diaktifkan. "
            "Sila log masuk.",
            "info"
        )

        return redirect(
            url_for("auth.login")
        )


    # ========================
    # Activate Account
    # ========================
    user.is_active = True

    db.session.commit()

    flash(
        "Akaun anda berjaya diaktifkan. "
        "Sila log masuk.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )
    
# ========================
# Safe Redirect - Helper
# ========================
def is_safe_redirect_target(target):
    if not target:
        return False

    host_url = urlsplit(
        request.host_url
    )

    redirect_url = urlsplit(
        urljoin(
            request.host_url,
            target
        )
    )

    return (redirect_url.scheme == host_url.scheme and redirect_url.netloc == host_url.netloc)

# ========================
# Login Rate Limit Key - Helper
# ========================
def login_rate_limit_key():
    email = (
        request.form.get("email")
        or ""
    ).strip().lower()

    return (f"{get_remote_address()}:"f"{email or 'unknown'}")
    
# ================Utk Login======================
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit( "5 per minute",
    key_func=login_rate_limit_key,
    methods=["POST"],
    error_message=(
        "Terlalu banyak percubaan log masuk. "
        "Sila cuba semula sebentar lagi."
    ),
)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        user = db.session.scalar(
            db.select(User).where(
                User.email == email
            )
        )

        if user is None or not user.check_password(form.password.data):
            flash(
                "Alamat emel atau kata laluan tidak sah.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        if not user.is_active:
            flash(
                "Akaun anda belum diaktifkan. "
                "Sila aktifkan akaun melalui emel terlebih dahulu.",
                "warning"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        # ========================
        # Reset Session
        # ========================
        session.clear()

        login_user(user)

        session.permanent = True


        # ========================
        # Safe Next Redirect
        # ========================
        next_url = request.args.get("next")

        if (next_url and is_safe_redirect_target(next_url)):
            return redirect(next_url)

        return redirect(url_for("auth.dashboard"))


    return render_template("auth/login.html", form=form)

# ================Utk Logout======================
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()

    flash(
        "Anda telah log keluar.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


# ==========================================================
# Utk Dashboard
# ==========================================================

@auth_bp.route("/dashboard")
@login_required
def dashboard():

     # Pastikan booking yang sudah tamat ditukar
    # daripada APPROVED kepada COMPLETED.
    mark_completed_bookings()
    
    # Pastikan booking yang pending approval ditukar kepada expired
    mark_expired_bookings()

    now = get_malaysia_now()

    # =====================================================
    # JULAT MASA HARI INI
    # =====================================================

    start_of_today = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    start_of_tomorrow = (
        start_of_today
        + timedelta(days=1)
    )


    # =====================================================
    # STATUS BILIK HARI INI
    # =====================================================
    room_statuses = get_room_statuses(now)


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


    room_status_preview = room_statuses[:6]
    
    # =====================================================
    # DASHBOARD PEMOHON / TEMPAHAN SENDIRI
    # =====================================================

    pending_count = db.session.scalar(
        db.select(func.count())
        .select_from(Booking)
        .where(
            Booking.applicant_id == current_user.id,
            Booking.status == "PENDING"
        )
    ) or 0


    approved_count = db.session.scalar(
        db.select(func.count())
        .select_from(Booking)
        .where(
            Booking.applicant_id == current_user.id,
            Booking.status == "APPROVED"
        )
    ) or 0


    completed_count = db.session.scalar(
        db.select(func.count())
        .select_from(Booking)
        .where(
            Booking.applicant_id == current_user.id,
            Booking.status == "COMPLETED"
        )
    ) or 0


    upcoming_bookings = db.session.scalars(
        db.select(Booking)
        .where(
            Booking.applicant_id == current_user.id,
            Booking.status.in_(
                [
                    "PENDING",
                    "APPROVED"
                ]
            ),
            Booking.end_datetime > now
        )
        .order_by(
            Booking.start_datetime.asc()
        )
        .limit(3)
    ).all()


    # =====================================================
    # NILAI DEFAULT ADMIN
    # =====================================================

    admin_pending_count = 0
    today_booking_count = 0
    ongoing_booking_count = 0
    active_room_count = 0

    pending_bookings = []


    # =====================================================
    # DASHBOARD ADMIN
    # =====================================================

    if current_user.role == "ADMIN":

        # Semua permohonan PENDING
        admin_pending_count = db.session.scalar(
            db.select(func.count())
            .select_from(Booking)
            .where(
                Booking.status == "PENDING"
            )
        ) or 0


        # Tempahan APPROVED untuk hari ini
        today_booking_count = db.session.scalar(
            db.select(func.count())
            .select_from(Booking)
            .where(
                Booking.status == "APPROVED",
                Booking.start_datetime < start_of_tomorrow,
                Booking.end_datetime > start_of_today
            )
        ) or 0


        # Booking yang sedang berlangsung sekarang
        ongoing_booking_count = db.session.scalar(
            db.select(func.count())
            .select_from(Booking)
            .where(
                Booking.status == "APPROVED",
                Booking.start_datetime <= now,
                Booking.end_datetime > now
            )
        ) or 0


        # Jumlah bilik aktif
        active_room_count = len(room_statuses)


        # Maksimum 5 permohonan untuk tindakan Admin
        pending_bookings = db.session.scalars(
            db.select(Booking)
            .where(
                Booking.status == "PENDING"
            )
            .order_by(
                Booking.start_datetime.asc()
            )
            .limit(5)
        ).all()

    # ========================
    # Dashboard Booking Action Form
    # ========================
    action_form = BookingActionForm()

    return render_template(
    "auth/dashboard.html",

    pending_count=pending_count,
    approved_count=approved_count,
    completed_count=completed_count,
    upcoming_bookings=upcoming_bookings,

    room_status_preview=room_status_preview,
    available_room_count=available_room_count,
    in_use_room_count=in_use_room_count,
    upcoming_room_count=upcoming_room_count,

    admin_pending_count=admin_pending_count,
    today_booking_count=today_booking_count,
    ongoing_booking_count=ongoing_booking_count,
    active_room_count=active_room_count,
    pending_bookings=pending_bookings,
    action_form=action_form
    )