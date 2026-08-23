from app.extensions import db


class Notification(db.Model):
    """
    An in-app notification for a user. Rows are written exclusively via
    app.services.notification_service.notify(...) — never insert one
    directly from a route, so every trigger point stays in one place.
    """

    __tablename__ = "notification"
    __table_args__ = (db.Index("ix_notification_user_unread", "user_id", "is_read"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(140), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    link_url = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False, index=True)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} user={self.user_id} type={self.type!r}>"
