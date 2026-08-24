from app.extensions import db
from app.models.enums import BookingStatus, enum_values
from app.models.mixins import TimestampMixin


class Booking(db.Model, TimestampMixin):
    """
    One booking attempt by a user for a trek.

    Deliberately does NOT carry a DB-level UNIQUE(user_id, trek_id) the way
    the original schema did. That constraint forced the old app to mutate
    a single row's status back and forth on cancel/rebook, which silently
    destroyed the historical record of the original booking + cancellation
    event. Instead, multiple rows per (user, trek) pair are allowed over
    time, and "no duplicate *active* booking" is enforced in
    app.services.booking_service at write time; the only place bookings
    are ever created. This preserves real history for booking history
    pages and the activity log while still preventing the business-rule
    violation that mattered.
    """

    __tablename__ = "booking"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("trek.id"), nullable=False, index=True)

    participant_count = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(
        db.Enum(BookingStatus, native_enum=False, length=16, values_callable=enum_values),
        nullable=False,
        default=BookingStatus.BOOKED,
        index=True,
    )
    booking_reference = db.Column(db.String(20), unique=True, nullable=True, index=True)
    special_requests = db.Column(db.Text, nullable=True)

    booked_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(255), nullable=True)

    __table_args__ = (db.CheckConstraint("participant_count > 0", name="ck_booking_participant_count_positive"),)

    trekker = db.relationship("User", back_populates="bookings", foreign_keys=[user_id])
    trek = db.relationship("Trek", back_populates="bookings")
    review = db.relationship("Review", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    @property
    def is_active(self):
        return self.status == BookingStatus.BOOKED

    @property
    def total_price(self):
        return (self.trek.price or 0) * self.participant_count if self.trek else 0

    @property
    def is_reviewable(self):
        return self.status == BookingStatus.COMPLETED and self.review is None

    def __repr__(self):
        return f"<Booking {self.id} user={self.user_id} trek={self.trek_id} status={self.status}>"
