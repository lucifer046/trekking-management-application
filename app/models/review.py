from app.extensions import db
from app.models.mixins import TimestampMixin


class Review(db.Model, TimestampMixin):
    """
    A rating + optional write-up left by a trekker for a completed trek.

    Tied to a specific booking_id (UNIQUE, not just user_id+trek_id) so
    that a single constraint simultaneously guarantees both business rules
    the spec asks for: "only for treks the user completed" (checked via
    booking.status == completed in app.services.review_service) and "no
    duplicate reviews"; without incorrectly blocking a genuinely new
    review after a legitimate future rebooking of the same trek.
    """

    __tablename__ = "review"
    __table_args__ = (db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating_range"),)

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("trek.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    booking_id = db.Column(
        db.Integer, db.ForeignKey("booking.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(120), nullable=True)
    body = db.Column(db.Text, nullable=True)

    trek = db.relationship("Trek", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")
    booking = db.relationship("Booking", back_populates="review")

    def __repr__(self):
        return f"<Review {self.id} trek={self.trek_id} rating={self.rating}>"
