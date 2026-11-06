from app.extensions import db
from app.models import AuditLog


# ========================
# Audit Log Model
# ========================
def test_audit_log_can_be_created(
    db_session,
    applicant_user,
):
    audit_log = AuditLog(
        actor_id=applicant_user.id,
        action="CREATE",
        entity_type="BOOKING",
        entity_id=100,
        description=(
            "Tempahan ujian dicipta."
        ),
    )

    db_session.add(audit_log)
    db_session.commit()

    saved_log = db.session.get(
        AuditLog,
        audit_log.id
    )

    assert saved_log is not None
    assert saved_log.actor_id == (
        applicant_user.id
    )
    assert saved_log.action == "CREATE"
    assert saved_log.entity_type == "BOOKING"
    assert saved_log.entity_id == 100
    assert saved_log.created_at is not None