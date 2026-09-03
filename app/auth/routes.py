from flask import flash, redirect, render_template, url_for

from app.auth import auth_bp
from app.auth.forms import RegistrationForm
from app.extensions import db
from app.models import User


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

        flash(
            "Pendaftaran berjaya. Akaun anda menunggu pengaktifan.",
            "success"
        )

        return redirect(url_for("auth.register"))

    return render_template(
        "auth/register.html",
        form=form
    )