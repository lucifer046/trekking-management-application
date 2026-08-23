from app.extensions import db
from app.models.enums import StaffStatus, enum_values
from app.models.mixins import TimestampMixin


class Staff(db.Model, TimestampMixin):
    """
    Extra profile data + approval workflow for users with role='staff'.
    One-to-one with User. Deleting the parent User cascades here (fixes a
    latent bug in the original schema, where Staff.user_id was a NOT NULL
    FK with no ON DELETE behavior, so deleting a staff User would raise an
    IntegrityError).
    """

    __tablename__ = "staff"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    contact = db.Column(db.String(20), nullable=True)
    experience = db.Column(db.Text, nullable=True)
    staff_status = db.Column(
        db.Enum(StaffStatus, native_enum=False, length=16, values_callable=enum_values),
        nullable=False,
        default=StaffStatus.PENDING,
        index=True,
    )
    applied_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    user = db.relationship("User", back_populates="staff_profile", foreign_keys=[user_id])
    reviewed_by = db.relationship("User", foreign_keys=[reviewed_by_id])

    def __repr__(self):
        return f"<Staff {self.id} user_id={self.user_id} status={self.staff_status}>"
