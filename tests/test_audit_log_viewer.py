from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import AuditLog, User


# ========================
# Helpers
# ========================
def create_user(
    *,
    email,
    full_name,
    role="APPLICANT",
    is_active=True,
):
    user = User(
        email=email,
        full_name=full_name,
        role=role,
        is_active=is_active,
    )

    user.set_password("Password123!")

    db.session.add(user)
    db.session.commit()

    return user


def login_as(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


def create_audit(
    *,
    actor_id=None,
    action="CREATE",
    entity_type="USER",
    entity_id=1,
    description="Audit test",
    created_at=None,
):
    audit = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )

    if created_at is not None:
        audit.created_at = created_at

    db.session.add(audit)
    db.session.commit()

    return audit


# ========================
# Admin Can View Audit Log
# ========================
def test_admin_can_view_audit_logs(client):
    admin = create_user(
        email="audit-admin-view@kpkt.gov.my",
        full_name="Audit Admin View",
        role="ADMIN",
    )

    login_as(client, admin)

    create_audit(
        actor_id=admin.id,
        action="CREATE",
        entity_type="ROOM",
        entity_id=101,
        description="Bilik ujian audit diwujudkan.",
    )

    response = client.get(
        "/admin/audit-logs"
    )

    assert response.status_code == 200
    assert b"Bilik ujian audit diwujudkan." in response.data
    assert b"CREATE" in response.data
    assert b"ROOM" in response.data


# ========================
# Non Admin Cannot View
# ========================
def test_applicant_cannot_view_audit_logs(client):
    applicant = create_user(
        email="audit-applicant@kpkt.gov.my",
        full_name="Audit Applicant",
        role="APPLICANT",
    )

    login_as(client, applicant)

    response = client.get(
        "/admin/audit-logs",
        follow_redirects=False,
    )

    assert response.status_code in {
        302,
        403,
    }


# ========================
# Search Audit Log
# ========================
def test_audit_log_search(client):
    admin = create_user(
        email="audit-admin-search@kpkt.gov.my",
        full_name="Audit Admin Search",
        role="ADMIN",
    )

    login_as(client, admin)

    create_audit(
        actor_id=admin.id,
        action="UPDATE",
        entity_type="USER",
        entity_id=201,
        description="Nama pengguna ditukar kepada Ahmad Audit.",
    )

    create_audit(
        actor_id=admin.id,
        action="CREATE",
        entity_type="ROOM",
        entity_id=202,
        description="Bilik Mesyuarat Melur diwujudkan.",
    )

    response = client.get(
        "/admin/audit-logs?q=Ahmad+Audit"
    )

    assert response.status_code == 200
    assert b"Ahmad Audit" in response.data
    assert b"Bilik Mesyuarat Melur" not in response.data


# ========================
# Entity + Action Filters
# ========================
def test_audit_log_entity_and_action_filters(client):
    admin = create_user(
        email="audit-admin-filter@kpkt.gov.my",
        full_name="Audit Admin Filter",
        role="ADMIN",
    )

    login_as(client, admin)

    create_audit(
        actor_id=admin.id,
        action="UPDATE",
        entity_type="USER",
        entity_id=301,
        description="USER UPDATE TARGET",
    )

    create_audit(
        actor_id=admin.id,
        action="CREATE",
        entity_type="USER",
        entity_id=302,
        description="USER CREATE OTHER",
    )

    create_audit(
        actor_id=admin.id,
        action="UPDATE",
        entity_type="ROOM",
        entity_id=303,
        description="ROOM UPDATE OTHER",
    )

    response = client.get(
        "/admin/audit-logs"
        "?entity_type=USER"
        "&action=UPDATE"
    )

    assert response.status_code == 200
    assert b"USER UPDATE TARGET" in response.data
    assert b"USER CREATE OTHER" not in response.data
    assert b"ROOM UPDATE OTHER" not in response.data


# ========================
# Date Range Filter
# ========================
def test_audit_log_date_range_filter(client):
    admin = create_user(
        email="audit-admin-date@kpkt.gov.my",
        full_name="Audit Admin Date",
        role="ADMIN",
    )

    login_as(client, admin)

    create_audit(
        actor_id=admin.id,
        action="CREATE",
        entity_type="BOOKING",
        entity_id=401,
        description="AUDIT INSIDE DATE RANGE",
        created_at=datetime(
            2026,
            11,
            5,
            4,
            0,
            tzinfo=timezone.utc,
        ),
    )

    create_audit(
        actor_id=admin.id,
        action="CREATE",
        entity_type="BOOKING",
        entity_id=402,
        description="AUDIT OUTSIDE DATE RANGE",
        created_at=datetime(
            2026,
            11,
            3,
            4,
            0,
            tzinfo=timezone.utc,
        ),
    )

    response = client.get(
        "/admin/audit-logs"
        "?date_from=2026-11-05"
        "&date_to=2026-11-05"
    )

    assert response.status_code == 200
    assert b"AUDIT INSIDE DATE RANGE" in response.data
    assert b"AUDIT OUTSIDE DATE RANGE" not in response.data


# ========================
# Pagination
# ========================
def test_audit_log_pagination(client):
    admin = create_user(
        email="audit-admin-pagination@kpkt.gov.my",
        full_name="Audit Admin Pagination",
        role="ADMIN",
    )

    login_as(client, admin)

    base_time = datetime.now(
        timezone.utc
    )

    for index in range(25):
        create_audit(
            actor_id=admin.id,
            action="CREATE",
            entity_type="USER",
            entity_id=500 + index,
            description=(
                f"PAGINATION AUDIT {index:02d}"
            ),
            created_at=(
                base_time
                + timedelta(minutes=index)
            ),
        )

    response_page_1 = client.get(
        "/admin/audit-logs"
        "?q=PAGINATION+AUDIT"
        "&page=1"
    )

    response_page_5 = client.get(
        "/admin/audit-logs"
        "?q=PAGINATION+AUDIT"
        "&page=5"
    )

    assert response_page_1.status_code == 200
    assert response_page_5.status_code == 200

    assert b"app-pagination" in response_page_1.data

    assert b"PAGINATION AUDIT 00" in response_page_5.data
