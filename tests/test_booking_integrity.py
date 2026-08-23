"""
Booking business-rule guards — the highest-risk logic in the whole
rebuild (see app/services/booking_service.py). Every guard gets its own
test so a regression here fails loudly and specifically.
"""
from datetime import date, timedelta

import pytest

from app.models import BookingStatus, TrekStatus
from app.services import booking_service
from app.services.exceptions import ServiceError


def test_overbooking_rejected(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek(capacity=5, available_slots=2)

    with pytest.raises(ServiceError, match="slot"):
        booking_service.create_booking(trekker, trek, participant_count=3)

    assert trek.available_slots == 2  # unchanged


def test_exact_remaining_capacity_is_bookable(db, make_user, make_trek):
    """Boundary case: booking exactly the remaining slots should succeed,
    not be off-by-one rejected."""
    trekker = make_user(role="user")
    trek = make_trek(capacity=5, available_slots=2)

    booking = booking_service.create_booking(trekker, trek, participant_count=2)
    assert booking is not None
    assert trek.available_slots == 0


def test_duplicate_active_booking_rejected(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek(capacity=10, available_slots=10)
    booking_service.create_booking(trekker, trek, participant_count=1)

    with pytest.raises(ServiceError, match="already"):
        booking_service.create_booking(trekker, trek, participant_count=1)

    assert trek.available_slots == 9  # only the first booking took effect


def test_rebooking_after_cancellation_is_allowed(db, make_user, make_trek):
    """This is the behavior the dropped DB-level UNIQUE(user_id, trek_id)
    used to provide via row-reuse — now provided by the service-layer
    active-only check instead, while preserving the original booking's
    history as its own row."""
    trekker = make_user(role="user")
    trek = make_trek(capacity=10, available_slots=10)
    first = booking_service.create_booking(trekker, trek, participant_count=1)
    booking_service.cancel_booking(first, trekker)

    second = booking_service.create_booking(trekker, trek, participant_count=1)

    assert second.id != first.id
    assert first.status == BookingStatus.CANCELLED
    assert second.status == BookingStatus.BOOKED
    from app.models import Booking
    assert Booking.query.filter_by(user_id=trekker.id, trek_id=trek.id).count() == 2


@pytest.mark.parametrize("status", [TrekStatus.DRAFT, TrekStatus.CLOSED, TrekStatus.STARTED, TrekStatus.COMPLETED, TrekStatus.CANCELLED])
def test_booking_non_open_trek_rejected(db, make_user, make_trek, status):
    trekker = make_user(role="user")
    trek = make_trek(status=status, capacity=10, available_slots=10)

    with pytest.raises(ServiceError):
        booking_service.create_booking(trekker, trek, participant_count=1)


def test_booking_after_trek_start_date_rejected(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.OPEN, start_date=date.today() - timedelta(days=1),
                      end_date=date.today() + timedelta(days=3))

    with pytest.raises(ServiceError, match="already started"):
        booking_service.create_booking(trekker, trek, participant_count=1)


def test_booking_by_blacklisted_user_rejected(db, make_user, make_trek):
    trekker = make_user(role="user", is_blocked=True)
    trek = make_trek()

    with pytest.raises(ServiceError):
        booking_service.create_booking(trekker, trek, participant_count=1)


def test_booking_by_inactive_user_rejected(db, make_user, make_trek):
    trekker = make_user(role="user", is_active=False)
    trek = make_trek()

    with pytest.raises(ServiceError):
        booking_service.create_booking(trekker, trek, participant_count=1)


def test_zero_or_negative_participant_count_rejected(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek()

    with pytest.raises(ServiceError):
        booking_service.create_booking(trekker, trek, participant_count=0)


def test_cancelling_already_cancelled_booking_rejected(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek()
    booking = booking_service.create_booking(trekker, trek, participant_count=1)
    booking_service.cancel_booking(booking, trekker)

    with pytest.raises(ServiceError):
        booking_service.cancel_booking(booking, trekker)


def test_cancelling_booking_on_started_trek_rejected(db, make_user, make_trek, make_booking):
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.STARTED)
    booking = make_booking(trekker, trek, status=BookingStatus.BOOKED)

    with pytest.raises(ServiceError):
        booking_service.cancel_booking(booking, trekker)


def test_cancellation_never_pushes_available_slots_above_capacity(db, make_user, make_trek, make_booking):
    """Defense-in-depth: even if available_slots was already at capacity
    for some reason, cancelling a booking must clamp instead of
    overshooting (the CHECK constraint would also catch this at the DB
    level, but the service should never even attempt it)."""
    trekker = make_user(role="user")
    trek = make_trek(capacity=5, available_slots=5)
    booking = make_booking(trekker, trek, participant_count=2, status=BookingStatus.BOOKED)

    booking_service.cancel_booking(booking, trekker)

    assert trek.available_slots == 5  # clamped, not 7
