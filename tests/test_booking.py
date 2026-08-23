"""Core booking flow: create, view confirmation, cancel."""
from app.models import Booking, BookingStatus, TrekStatus
from app.services import booking_service


def test_booking_decrements_available_slots_by_participant_count(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek(capacity=10, available_slots=10)

    booking = booking_service.create_booking(trekker, trek, participant_count=3)

    assert booking.participant_count == 3
    assert trek.available_slots == 7
    assert booking.booking_reference.startswith("TMA-")


def test_cancellation_restores_slots(db, make_user, make_trek):
    trekker = make_user(role="user")
    trek = make_trek(capacity=10, available_slots=10)
    booking = booking_service.create_booking(trekker, trek, participant_count=4)
    assert trek.available_slots == 6

    booking_service.cancel_booking(booking, trekker, reason="changed my mind")

    assert trek.available_slots == 10
    assert booking.status == BookingStatus.CANCELLED
    assert booking.cancelled_at is not None
    assert booking.cancellation_reason == "changed my mind"


def test_booking_confirmation_page_shows_correct_fields(client, make_user, make_trek, login_as):
    trekker = make_user(role="user")
    trek = make_trek()
    login_as(trekker)

    booking = booking_service.create_booking(trekker, trek, participant_count=2)
    resp = client.get(f"/user/bookings/{booking.id}")

    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert booking.booking_reference in body
    assert trek.name in body
    assert trek.location.name in body


def test_booking_route_end_to_end(client, make_user, make_trek, login_as, db):
    trekker = make_user(role="user")
    trek = make_trek(capacity=5, available_slots=5)
    login_as(trekker)

    resp = client.post(f"/user/treks/{trek.id}/book", data={"participant_count": "2", "special_requests": ""}, follow_redirects=True)
    assert resp.status_code == 200

    db.session.refresh(trek)
    assert trek.available_slots == 3
    booking = Booking.query.filter_by(user_id=trekker.id, trek_id=trek.id).first()
    assert booking is not None
    assert booking.participant_count == 2


def test_cancel_route_end_to_end(client, make_user, make_trek, login_as, db):
    trekker = make_user(role="user")
    trek = make_trek(capacity=5, available_slots=5)
    login_as(trekker)
    booking = booking_service.create_booking(trekker, trek, participant_count=1)

    resp = client.post(f"/user/bookings/{booking.id}/cancel", data={"reason": "test"}, follow_redirects=True)
    assert resp.status_code == 200

    db.session.refresh(booking)
    db.session.refresh(trek)
    assert booking.status == BookingStatus.CANCELLED
    assert trek.available_slots == 5
