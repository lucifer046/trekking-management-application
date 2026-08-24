"""Review eligibility and creation."""
import pytest

from app.models import BookingStatus, TrekStatus
from app.services import review_service
from app.services.exceptions import ServiceError


def test_review_allowed_for_completed_booking(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.COMPLETED)
    booking = make_booking(trekker, trek, status=BookingStatus.COMPLETED)

    review = review_service.create_review(booking, rating=5, title="Great!", body="Loved it.")

    assert review.rating == 5
    assert review.trek_id == trek.id
    assert trek.average_rating == 5.0


def test_review_rejected_for_active_booking(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.OPEN)
    booking = make_booking(trekker, trek, status=BookingStatus.BOOKED)

    with pytest.raises(ServiceError, match="completed"):
        review_service.create_review(booking, rating=5, title="", body="")


def test_review_rejected_for_cancelled_booking(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek()
    booking = make_booking(trekker, trek, status=BookingStatus.CANCELLED)

    with pytest.raises(ServiceError):
        review_service.create_review(booking, rating=3, title="", body="")


def test_duplicate_review_on_same_booking_rejected(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.COMPLETED)
    booking = make_booking(trekker, trek, status=BookingStatus.COMPLETED)
    review_service.create_review(booking, rating=4, title="", body="")

    with pytest.raises(ServiceError, match="already"):
        review_service.create_review(booking, rating=2, title="", body="")


def test_rating_out_of_range_rejected(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.COMPLETED)
    booking = make_booking(trekker, trek, status=BookingStatus.COMPLETED)

    with pytest.raises(ServiceError):
        review_service.create_review(booking, rating=6, title="", body="")


def test_second_completed_trip_can_be_reviewed_independently(db, make_user, make_trek, make_booking):
    """A second, later booking of the same trek is a distinct review
    opportunity; tying Review to booking_id (not user+trek) is what
    makes this possible."""
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.COMPLETED)
    first_trip = make_booking(trekker, trek, status=BookingStatus.COMPLETED)
    second_trip = make_booking(trekker, trek, status=BookingStatus.COMPLETED)

    review_service.create_review(first_trip, rating=4, title="", body="")
    review_service.create_review(second_trip, rating=5, title="", body="")

    assert trek.review_count == 2
