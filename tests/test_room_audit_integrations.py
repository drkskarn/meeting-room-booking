# ========================
# Imports
# ========================
from app.extensions import db
from app.models import (
    AuditLog,
    Room,
    User,
)


# ========================
# Helper - Create Admin
# ========================
def create_admin():
    admin = User(
        email="room-audit-admin@kpkt.gov.my",
        full_name="Room Audit Admin",
        role="ADMIN",
        is_active=True,
    )

    admin.set_password(
        "Password123!"
    )

    db.session.add(admin)
    db.session.commit()

    return admin


# ========================
# Helper - Login
# ========================
def login_as(client, user):
    with client.session_transaction() as session:
        session["_user_id"] = str(user.id)
        session["_fresh"] = True


# ========================
# Create Room Audit
# ========================
def test_add_room_creates_audit(client):

    admin = create_admin()

    login_as(
        client,
        admin,
    )

    response = client.post(
        "/admin/rooms/add",
        data={
            "room_name": "Bilik Audit Alpha",
            "location": "Aras 1",
            "capacity": 10,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    room = db.session.execute(
        db.select(Room).where(
            Room.room_name
            == "Bilik Audit Alpha"
        )
    ).scalar_one()

    audit = db.session.execute(
        db.select(AuditLog).where(
            AuditLog.entity_type == "ROOM",
            AuditLog.entity_id == room.id,
            AuditLog.action == "CREATE",
        )
    ).scalar_one()

    assert audit.actor_id == admin.id
    assert (
        audit.description
        == "Bilik mesyuarat diwujudkan."
    )


# ========================
# Edit Room Audit
# ========================
def test_edit_room_creates_audit(client):

    admin = create_admin()

    room = Room(
        room_name="Bilik Audit Beta",
        location="Aras 2",
        capacity=10,
        is_active=True,
    )

    db.session.add(room)
    db.session.commit()

    login_as(
        client,
        admin,
    )

    response = client.post(
        f"/admin/rooms/{room.id}/edit",
        data={
            "room_name": room.room_name,
            "location": room.location,
            "capacity": 20,
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    audit = db.session.execute(
        db.select(AuditLog).where(
            AuditLog.entity_type == "ROOM",
            AuditLog.entity_id == room.id,
            AuditLog.action == "UPDATE",
        )
    ).scalar_one()

    assert audit.actor_id == admin.id

    assert (
        "Kapasiti: 10 -> 20"
        in audit.description
    )


# ========================
# Deactivate Room Audit
# ========================
def test_deactivate_room_creates_audit(client):

    admin = create_admin()

    room = Room(
        room_name="Bilik Audit Gamma",
        location="Aras 3",
        capacity=15,
        is_active=True,
    )

    db.session.add(room)
    db.session.commit()

    login_as(
        client,
        admin,
    )

    response = client.post(
        f"/admin/rooms/{room.id}/toggle",
        follow_redirects=True,
    )

    assert response.status_code == 200

    db.session.refresh(room)

    assert room.is_active is False

    audit = db.session.execute(
        db.select(AuditLog).where(
            AuditLog.entity_type == "ROOM",
            AuditLog.entity_id == room.id,
            AuditLog.action == "DEACTIVATE",
        )
    ).scalar_one()

    assert audit.actor_id == admin.id

    assert (
        audit.description
        == "Bilik mesyuarat dinyahaktifkan."
    )


# ========================
# Activate Room Audit
# ========================
def test_activate_room_creates_audit(client):

    admin = create_admin()

    room = Room(
        room_name="Bilik Audit Delta",
        location="Aras 4",
        capacity=25,
        is_active=False,
    )

    db.session.add(room)
    db.session.commit()

    login_as(
        client,
        admin,
    )

    response = client.post(
        f"/admin/rooms/{room.id}/toggle",
        follow_redirects=True,
    )

    assert response.status_code == 200

    db.session.refresh(room)

    assert room.is_active is True

    audit = db.session.execute(
        db.select(AuditLog).where(
            AuditLog.entity_type == "ROOM",
            AuditLog.entity_id == room.id,
            AuditLog.action == "ACTIVATE",
        )
    ).scalar_one()

    assert audit.actor_id == admin.id

    assert (
        audit.description
        == "Bilik mesyuarat diaktifkan."
    )