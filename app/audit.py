from flask import has_request_context
from flask_login import current_user

from app.extensions import db
from app.models import AuditLog


# ========================
# Create Audit Log
# ========================
def log_audit(
    action,
    entity_type,
    entity_id=None,
    description=None,
    actor_id=None,
):
    # ========================
    # Detect Current User
    # ========================
    if (
        actor_id is None
        and has_request_context()
        and current_user.is_authenticated
    ):
        actor_id = current_user.id


    # ========================
    # Create Audit Record
    # ========================
    audit_log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )

    db.session.add(
        audit_log
    )

    return audit_log