from app.extensions import db
from app.models import User


def ensure_default_admin(app):
    email = app.config["ADMIN_EMAIL"].strip().lower()
    password = app.config.get("ADMIN_PASSWORD")
    full_name = app.config["ADMIN_FULL_NAME"]

    if not password:
        app.logger.warning(
            "ADMIN_PASSWORD is not configured. "
            "Default administrator was not created."
        )
        return

    admin = db.session.scalar(
        db.select(User).where(User.email == email)
    )

    if admin is not None:
        return

    admin = User(
        email=email,
        full_name=full_name,
        identification_no=None,
        division_name=None,
        unit_name=None,
        role="ADMIN",
        is_active=True
    )

    admin.set_password(password)

    db.session.add(admin)
    db.session.commit()

    app.logger.info(
        "Default administrator account created."
    )