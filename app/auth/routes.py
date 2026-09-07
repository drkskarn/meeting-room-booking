from flask import flash, redirect, render_template, url_for

from app.auth import auth_bp
from app.auth.forms import LoginForm, RegistrationForm
from app.auth.tokens import (generate_activation_token, verify_activation_token)
from app.extensions import db
from app.models import User

from flask_login import current_user, login_required, login_user, logout_user


# ===========Utk Registration======================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        user = User(
            email=form.email.data.strip().lower(),
            full_name=form.full_name.data.strip(),
            identification_no=form.identification_no.data.strip(),
            division_name=form.division_name.data.strip(),
            unit_name=form.unit_name.data.strip(),
            role="APPLICANT",
            is_active=False
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        token = generate_activation_token(user.email)

        activation_url = url_for(
            "auth.activate_account",
            token=token,
            _external=True )
        
        # hanya utk tujuan checking dev sahaja
        print(f"Activation URL: {activation_url}")
        
        flash(
            "Pendaftaran berjaya. Akaun anda menunggu pengaktifan.",
            "success"
        )

        return redirect(url_for("auth.register"))

        token = generate_activation_token(user.email)
        
        
    return render_template(
        "auth/register.html",
        form=form
    )

# ================Utk Login======================
@auth_bp.route("/login", methods=["GET", "POST"])
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

        login_user(user)

        return redirect(
            url_for("auth.dashboard")
        )

    return render_template(
        "auth/login.html",
        form=form
    )

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
    
# ================Utk Dashboard====================
@auth_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "auth/dashboard.html"
    )


# ============Utk Email Activation=================
@auth_bp.route("/activate/<token>")
def activate_account(token):
    email = verify_activation_token(token)

    if email is None:
        flash(
            "Pautan pengaktifan tidak sah atau telah tamat tempoh.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    user = db.session.scalar(
        db.select(User).where(
            User.email == email
        )
    )

    if user is None:
        flash(
            "Akaun pengguna tidak ditemui.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    if user.is_active:
        flash(
            "Akaun anda telah pun diaktifkan. Sila log masuk.",
            "info"
        )

        return redirect(url_for("auth.login"))

    user.is_active = True

    db.session.commit()

    flash(
        "Akaun anda telah berjaya diaktifkan. "
        "Sila log masuk.",
        "success"
    )

    return redirect(url_for("auth.login"))