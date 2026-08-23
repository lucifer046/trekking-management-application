"""
Booking creation/cancellation — the highest-risk business logic in the
whole app, because every guard here has to move by `participant_count`
instead of a flat ±1, and getting it wrong means either silent overbooking
or slots that never come back. This module is the *only* place a Booking
is ever created or its status changed, and it's the thing
tests/test_booking_integrity.py exists to pin down.
"""
import secrets
from datetime import date, datetime, timezone

from app.extensions import db
from app.models import Booking, BookingStatus, Trek, TrekStatus
from app.services import activity_log_service, notification_service
from app.services.exceptions import ServiceError


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _generate_reference():
    for _ in range(10):
        candidate = "TMA-" + secrets.token_hex(3).upper()
        if not Booking.query.filter_by(booking_reference=candidate).first():
            return candidate
    # Astronomically unlikely fallthrough — widen the search space once.
    return "TMA-" + secrets.token_hex(5).upper()


def create_booking(user, trek, participant_count, special_requests=None):
    """Creates a Booking for `user` on `trek`, enforcing every guard the
    spec's booking-integrity requirements ask for, in order:

      1. account must be active & not blacklisted
      2. trek must be in the 'open' status (not draft/closed/completed/cancelled/...)
      3. trek must not have already started
      4. participant_count must be a positive integer
      5. no existing *active* booking by this user for this trek
      6. enough available_slots left for the requested party size

    Raises ServiceError with a user-facing message on any violation and
    changes nothing in the DB. Commits on success.
    """
    if not user.account_is_usable:
        raise ServiceError("Your account is not permitted to make bookings. Please contact support.")

    if trek.status != TrekStatus.OPEN:
        raise ServiceError("This trek is not currently open for bookings.")

    if trek.start_date <= date.today():
        raise ServiceError("This trek has already started and can no longer be booked.")

    if participant_count is None or participant_count < 1:
        raise ServiceError("Participant count must be at least 1.")

    existing_active = Booking.query.filter_by(
        user_id=user.id, trek_id=trek.id, status=BookingStatus.BOOKED
    ).first()
    if existing_active:
        raise ServiceError("You already have an active booking for this trek.")

    if trek.available_slots < participant_count:
        raise ServiceError(f"Only {trek.available_slots} slot(s) left on this trek.")

    booking = Booking(
        user_id=user.id,
        trek_id=trek.id,
        participant_count=participant_count,
        special_requests=(special_requests or "").strip() or None,
        status=BookingStatus.BOOKED,
        booking_reference=_generate_reference(),
    )
    trek.available_slots -= participant_count

    db.session.add(booking)
    db.session.flush()  # assigns booking.id before it's referenced below

    notification_service.notify(
        user,
        "booking_confirmed",
        "Booking confirmed",
        f"Your booking for {trek.name} ({participant_count} participant"
        f"{'s' if participant_count != 1 else ''}) is confirmed. Reference: {booking.booking_reference}.",
        link_url=f"/user/bookings/{booking.id}",
    )
    activity_log_service.log(
        actor=user,
        action="booking_created",
        description=f"{user.name} booked {trek.name} for {participant_count} participant(s).",
        target_type="booking",
        target_id=booking.id,
    )

    db.session.commit()
    return booking


def cancel_booking(booking, actor, reason=None):
    """Cancels an active booking and restores its slots to the trek.
    Callable by the owning trekker or by staff/admin removing a
    participant — `actor` is only used for the notification/audit trail,
    not for authorization (the calling route is responsible for the
    ownership/role check before calling this)."""
    if booking.status != BookingStatus.BOOKED:
        raise ServiceError("Only an active booking can be cancelled.")

    trek = booking.trek
    if trek.status in (TrekStatus.STARTED, TrekStatus.COMPLETED):
        raise ServiceError("This trek has already started or completed, so the booking can no longer be cancelled.")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = _utcnow()
    booking.cancellation_reason = (reason or "").strip() or None

    trek.available_slots = min(trek.capacity, trek.available_slots + booking.participant_count)

    notification_service.notify(
        booking.trekker,
        "booking_cancelled",
        "Booking cancelled",
        f"Your booking for {trek.name} (ref. {booking.booking_reference}) has been cancelled.",
    )
    activity_log_service.log(
        actor=actor,
        action="booking_cancelled",
        description=f"Booking {booking.booking_reference or booking.id} for {trek.name} was cancelled.",
        target_type="booking",
        target_id=booking.id,
    )

    db.session.commit()
    return booking
