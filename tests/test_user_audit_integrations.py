from flask import url_for

from app.extensions import db
from app.models import AuditLog, User


# ========================
# URL Helper
# ========================
def get_url(app, endpoint, **values):
    with app.test_request_context():
        return url_for(
            endpoint,
            **values
        )


# ========================
# Login Helper
# ========================
def login(
    app,
    client,
    email,
    password,
):
    return client.post(
        get_url(
            app,
            "auth.login"
        ),
        data={
            "email": email,
            "password": password,
        },
    )


# ========================
# Find User Audit
# ========================
def find_user_audit(
    action,
    user_id,
):
    return db.session.scalar(
        db.select(AuditLog)
        .where(
            AuditLog.action == action,
            AuditLog.entity_type == "USER",
            AuditLog.entity_id == user_id,
        )
        .order_by(
            AuditLog.id.desc()
        )
    )


# ========================
# Add User Audit
# ========================
def test_add_user_creates_audit(
    app,
    client,
    db_session,
    admin_user,
):
    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.add_user",
        ),
        data={
            "full_name": "Pengguna Audit Baru",
            "email": "auditbaru@kpkt.gov.my",
            "identification_no": "900101101234",
            "role": "APPLICANT",
            "division_name": "Bahagian Audit",
            "unit_name": "Unit Ujian",
            "new_password": "TestPassword123!",
            "confirm_password": "TestPassword123!",
        },
    )

    assert response.status_code == 302

    new_user = db.session.scalar(
        db.select(User).where(
            User.email == "auditbaru@kpkt.gov.my"
        )
    )

    assert new_user is not None

    audit = find_user_audit(
        "CREATE",
        new_user.id,
    )

    assert audit is not None
    assert audit.actor_id == admin_user.id


# ========================
# Edit User Audit
# ========================
def test_edit_user_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
):
    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    old_name = applicant_user.full_name
    new_name = "Nama Pengguna Dikemaskini"

    response = client.post(
        get_url(
            app,
            "admin.edit_user",
            user_id=applicant_user.id,
        ),
        data={
            "full_name": new_name,
            "email": applicant_user.email,
            "role": applicant_user.role,
            "division_name": (
                applicant_user.division_name or ""
            ),
            "unit_name": (
                applicant_user.unit_name or ""
            ),
            "new_password": "",
            "confirm_password": "",
        },
    )

    assert response.status_code == 302

    audit = find_user_audit(
        "UPDATE",
        applicant_user.id,
    )

    assert audit is not None
    assert audit.actor_id == admin_user.id

    assert old_name in audit.description
    assert new_name in audit.description


# ========================
# Deactivate User Audit
# ========================
def test_deactivate_user_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
):
    applicant_user.is_active = True
    db_session.commit()

    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_user_status",
            user_id=applicant_user.id,
        )
    )

    assert response.status_code == 302

    db_session.refresh(
        applicant_user
    )

    assert applicant_user.is_active is False

    audit = find_user_audit(
        "DEACTIVATE",
        applicant_user.id,
    )

    assert audit is not None
    assert audit.actor_id == admin_user.id


# ========================
# Activate User Audit
# ========================
def test_activate_user_creates_audit(
    app,
    client,
    db_session,
    applicant_user,
    admin_user,
):
    applicant_user.is_active = False
    db_session.commit()

    login(
        app,
        client,
        admin_user.email,
        "AdminPassword123!",
    )

    response = client.post(
        get_url(
            app,
            "admin.toggle_user_status",
            user_id=applicant_user.id,
        )
    )

    assert response.status_code == 302

    db_session.refresh(
        applicant_user
    )

    assert applicant_user.is_active is True

    audit = find_user_audit(
        "ACTIVATE",
        applicant_user.id,
    )

    assert audit is not None
    assert audit.actor_id == admin_user.id