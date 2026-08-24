from app.extensions import db


class ActivityLog(db.Model):
    """
    Append-only audit trail of significant platform events (staff
    approved, trek created, booking cancelled, etc.); written exclusively
    via app.services.activity_log_service.log(...).

    `target_type` / `target_id` deliberately form an *unconstrained*
    polymorphic reference (no real ForeignKey); the standard audit-log
    pattern. A real FK would either block deletion of the referenced row
    or null the reference out, both of which defeat the point of a
    historical log. `actor_name_snapshot` is a denormalized copy of the
    actor's name captured at write time, so log entries stay readable even
    if the actor's account is later deleted (actor_id then goes NULL).
    """

    __tablename__ = "activity_log"

    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_name_snapshot = db.Column(db.String(96), nullable=False)

    action = db.Column(db.String(60), nullable=False, index=True)
    target_type = db.Column(db.String(40), nullable=True)
    target_id = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False, index=True)

    actor = db.relationship("User", foreign_keys=[actor_id])

    def __repr__(self):
        return f"<ActivityLog {self.id} action={self.action!r}>"
