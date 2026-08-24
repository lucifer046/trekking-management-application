"""
Trek lifecycle logic. `transition_status()` is the *only* place
`Trek.status` is ever assigned outside a raw migration/seed script; every
route (admin edit, staff operational update) calls this instead of setting
`trek.status = ...` directly, so the legal-transition check and the side
effects below can never be bypassed.
"""
from datetime import datetime, timezone

from app.extensions import db
from app.models import Booking, BookingStatus, Location, Trek, TrekStatus
from app.services import activity_log_service, notification_service
from app.services.exceptions import ServiceError
from app.utils.slugify import unique_slug


def generate_slug(name):
    return unique_slug(name, lambda candidate: Trek.query.filter_by(slug=candidate).first() is not None)


def get_or_create_location(name, state_region=None):
    """Case-insensitive find-or-create; the trek form collects a location
    as free text (no separate "manage locations" admin page exists, since
    nothing in the spec asks for one), but the Location table stays
    normalized underneath so the homepage's Popular Locations section and
    the explore-page filter can group/count treks reliably."""
    name = (name or "").strip()
    existing = Location.query.filter(db.func.lower(Location.name) == name.lower()).first()
    if existing:
        return existing

    location = Location(
        name=name,
        state_region=(state_region or "").strip() or None,
        slug=unique_slug(name, lambda candidate: Location.query.filter_by(slug=candidate).first() is not None),
    )
    db.session.add(location)
    db.session.flush()
    return location


def apply_form_to_trek(trek, form):
    """Copies TrekForm fields onto a Trek instance (used for both create
    and edit); centralizing this mapping avoids the create/edit routes
    drifting out of sync with each other."""
    location = get_or_create_location(form.location_name.data, form.location_state.data)

    trek.name = form.name.data.strip()
    trek.location = location
    trek.difficulty = form.difficulty.data
    trek.duration_days = form.duration_days.data
    trek.start_date = form.start_date.data
    trek.end_date = form.end_date.data
    trek.price = form.price.data
    trek.meeting_point = (form.meeting_point.data or "").strip() or None
    trek.description = form.description.data.strip()
    trek.highlights = form.highlights.data
    trek.itinerary = form.itinerary.data
    trek.requirements = form.requirements.data
    trek.safety_info = form.safety_info.data
    trek.cancellation_policy = form.cancellation_policy.data
    trek.is_featured = form.is_featured.data

    new_capacity = form.capacity.data
    if trek.capacity is None:
        # brand new trek; every seat starts available
        trek.capacity = new_capacity
        trek.available_slots = new_capacity
    elif new_capacity != trek.capacity:
        # editing an existing trek's capacity; keep booked_slots
        # constant and shift available_slots by the delta, clamped so it
        # can never go negative even if capacity shrinks below what's
        # already booked.
        delta = new_capacity - trek.capacity
        trek.capacity = new_capacity
        trek.available_slots = max(0, min(new_capacity, trek.available_slots + delta))


def transition_status(trek, new_status, actor):
    """Moves `trek` to `new_status`, enforcing the legal-transition table
    on Trek.can_transition_to() and applying the side effects that must
    happen atomically with the status change. Raises ServiceError (and
    changes nothing) if the transition isn't legal. Commits on success."""
    if trek.status == new_status:
        return trek  # no-op, not an error; re-saving the same status is harmless

    if not trek.can_transition_to(new_status):
        raise ServiceError(f"Cannot move a trek from '{trek.status.value}' to '{new_status.value}'.")

    old_status = trek.status
    trek.status = new_status

    if new_status == TrekStatus.COMPLETED:
        _complete_active_bookings(trek)
    elif new_status == TrekStatus.CANCELLED:
        _cancel_active_bookings(trek, reason="Trek was cancelled by the operator.")
    elif new_status == TrekStatus.STARTED:
        _notify_active_bookers_trek_started(trek)

    activity_log_service.log(
        actor=actor,
        action="trek_status_changed",
        description=f"Trek '{trek.name}' moved from {old_status.value} to {new_status.value}.",
        target_type="trek",
        target_id=trek.id,
    )
    db.session.commit()
    return trek


def _complete_active_bookings(trek):
    active_bookings = Booking.query.filter_by(trek_id=trek.id, status=BookingStatus.BOOKED).all()
    for booking in active_bookings:
        booking.status = BookingStatus.COMPLETED
        notification_service.notify(
            booking.trekker,
            "trek_completed",
            "Trek completed",
            f"Hope you enjoyed {trek.name}! You can now leave a review.",
            link_url=f"/user/bookings/{booking.id}",
        )


def _notify_active_bookers_trek_started(trek):
    """Spec section 24 names 'Trek started' as a notification trigger.
    Unlike the completed/cancelled cases, no booking field changes here;
    this only pings the trekkers who are actually on the trip today."""
    active_bookings = Booking.query.filter_by(trek_id=trek.id, status=BookingStatus.BOOKED).all()
    for booking in active_bookings:
        notification_service.notify(
            booking.trekker,
            "trek_started",
            "Your trek has started",
            f"{trek.name} has officially started. Have a great trek!",
            link_url=f"/user/bookings/{booking.id}",
        )


def _cancel_active_bookings(trek, reason):
    active_bookings = Booking.query.filter_by(trek_id=trek.id, status=BookingStatus.BOOKED).all()
    for booking in active_bookings:
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = datetime.now(timezone.utc).replace(tzinfo=None)
        booking.cancellation_reason = reason
        notification_service.notify(
            booking.trekker,
            "trek_cancelled",
            "Trek cancelled",
            f"Unfortunately {trek.name} was cancelled. Your booking has been cancelled and no further action is needed.",
        )
