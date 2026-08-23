"""
Single choke point for every ActivityLog row — see spec section 27's
trigger list (staff approved, user blacklisted, trek created/edited,
staff assigned, booking created/cancelled, trek completed, ...).

Does NOT commit — see notification_service for the same rationale.
"""
from app.extensions import db
from app.models import ActivityLog


def log(actor, action, description, target_type=None, target_id=None):
    entry = ActivityLog(
        actor_id=actor.id if actor else None,
        actor_name_snapshot=actor.name if actor else "System",
        action=action,
        description=description,
        target_type=target_type,
        target_id=target_id,
    )
    db.session.add(entry)
    return entry
