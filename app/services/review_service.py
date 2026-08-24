"""Review eligibility + creation. A review is tied to one specific
completed Booking (see app.models.review.Review docstring); this is what
lets a single UNIQUE(booking_id) simultaneously enforce "completed treks
only" and "no duplicate reviews"."""
from app.extensions import db
from app.models import Booking, BookingStatus, Review
from app.services import activity_log_service
from app.services.exceptions import ServiceError


def reviewable_bookings(user, trek):
    """Completed bookings this user has for this trek that don't have a
    review yet; normally at most one, but a user could in principle have
    trekked the same trip more than once."""
    return [
        b
        for b in Booking.query.filter_by(user_id=user.id, trek_id=trek.id, status=BookingStatus.COMPLETED).all()
        if b.review is None
    ]


def create_review(booking, rating, title, body):
    if booking.status != BookingStatus.COMPLETED:
        raise ServiceError("You can only review a trek after it's completed.")
    if booking.review is not None:
        raise ServiceError("You've already reviewed this trip.")
    if rating is None or not (1 <= int(rating) <= 5):
        raise ServiceError("Rating must be between 1 and 5.")

    review = Review(
        trek_id=booking.trek_id,
        user_id=booking.user_id,
        booking_id=booking.id,
        rating=int(rating),
        title=(title or "").strip() or None,
        body=(body or "").strip() or None,
    )
    db.session.add(review)
    activity_log_service.log(
        actor=booking.trekker,
        action="review_created",
        description=f"{booking.trekker.name} left a {rating}-star review for {booking.trek.name}.",
        target_type="review",
        target_id=booking.id,
    )
    db.session.commit()
    return review
