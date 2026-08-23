"""Trek.status state machine — legal/illegal transitions and their side effects."""
import pytest

from app.models import BookingStatus, TrekStatus
from app.services import trek_service
from app.services.exceptions import ServiceError

LEGAL_TRANSITIONS = [
    (TrekStatus.DRAFT, TrekStatus.PENDING_APPROVAL),
    (TrekStatus.DRAFT, TrekStatus.APPROVED),
    (TrekStatus.DRAFT, TrekStatus.CANCELLED),
    (TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED),
    (TrekStatus.PENDING_APPROVAL, TrekStatus.CANCELLED),
    (TrekStatus.APPROVED, TrekStatus.OPEN),
    (TrekStatus.APPROVED, TrekStatus.CANCELLED),
    (TrekStatus.OPEN, TrekStatus.CLOSED),
    (TrekStatus.OPEN, TrekStatus.STARTED),
    (TrekStatus.OPEN, TrekStatus.CANCELLED),
    (TrekStatus.CLOSED, TrekStatus.OPEN),
    (TrekStatus.CLOSED, TrekStatus.STARTED),
    (TrekStatus.CLOSED, TrekStatus.CANCELLED),
    (TrekStatus.STARTED, TrekStatus.COMPLETED),
]

ILLEGAL_TRANSITIONS = [
    (TrekStatus.COMPLETED, TrekStatus.OPEN),
    (TrekStatus.CANCELLED, TrekStatus.OPEN),
    (TrekStatus.CANCELLED, TrekStatus.DRAFT),
    (TrekStatus.DRAFT, TrekStatus.OPEN),  # can't skip approval
    (TrekStatus.DRAFT, TrekStatus.STARTED),
    (TrekStatus.APPROVED, TrekStatus.STARTED),  # must open first
    (TrekStatus.STARTED, TrekStatus.OPEN),  # can't go back once started
    (TrekStatus.STARTED, TrekStatus.CANCELLED),
    (TrekStatus.COMPLETED, TrekStatus.CANCELLED),
]


@pytest.mark.parametrize("from_status,to_status", LEGAL_TRANSITIONS)
def test_legal_transition_succeeds(db, make_user, make_trek, from_status, to_status):
    admin = make_user(role="admin")
    trek = make_trek(status=from_status)
    trek_service.transition_status(trek, to_status, admin)
    assert trek.status == to_status


@pytest.mark.parametrize("from_status,to_status", ILLEGAL_TRANSITIONS)
def test_illegal_transition_rejected(db, make_user, make_trek, from_status, to_status):
    admin = make_user(role="admin")
    trek = make_trek(status=from_status)
    with pytest.raises(ServiceError):
        trek_service.transition_status(trek, to_status, admin)
    assert trek.status == from_status  # unchanged


def test_completing_trek_marks_active_bookings_completed(db, make_user, make_trek, make_booking):
    admin = make_user(role="admin")
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.STARTED)
    booking = make_booking(trekker, trek, status=BookingStatus.BOOKED)

    trek_service.transition_status(trek, TrekStatus.COMPLETED, admin)

    db.session.refresh(booking)
    assert booking.status == BookingStatus.COMPLETED


def test_cancelling_trek_cascades_to_cancel_active_bookings(db, make_user, make_trek, make_booking):
    admin = make_user(role="admin")
    trekker = make_user(role="user")
    trek = make_trek(status=TrekStatus.OPEN)
    booking = make_booking(trekker, trek, status=BookingStatus.BOOKED)

    trek_service.transition_status(trek, TrekStatus.CANCELLED, admin)

    db.session.refresh(booking)
    assert booking.status == BookingStatus.CANCELLED
    assert booking.cancelled_at is not None


def test_same_status_transition_is_a_harmless_noop(db, make_user, make_trek):
    admin = make_user(role="admin")
    trek = make_trek(status=TrekStatus.OPEN)
    trek_service.transition_status(trek, TrekStatus.OPEN, admin)
    assert trek.status == TrekStatus.OPEN
