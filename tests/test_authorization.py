"""Role-based access control and IDOR (resource-ownership) checks."""
from app.models import BookingStatus


def test_anonymous_redirected_to_login(client):
    resp = client.get("/user/dashboard", follow_redirects=True)
    assert resp.request.path == "/login"


def test_trekker_cannot_access_admin_routes(client, make_user, login_as):
    trekker = make_user(role="user")
    login_as(trekker)
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 403


def test_trekker_cannot_access_staff_routes(client, make_user, login_as):
    trekker = make_user(role="user")
    login_as(trekker)
    resp = client.get("/staff/dashboard")
    assert resp.status_code == 403


def test_staff_cannot_access_admin_routes(client, make_user, login_as):
    staff = make_user(role="staff")
    login_as(staff)
    resp = client.get("/admin/dashboard")
    assert resp.status_code == 403


def test_admin_cannot_access_user_dashboard(client, make_user, login_as):
    admin = make_user(role="admin")
    login_as(admin)
    resp = client.get("/user/dashboard")
    assert resp.status_code == 403


def test_user_cannot_cancel_another_users_booking(client, make_user, make_trek, make_booking, login_as):
    owner = make_user(role="user", email="owner@example.com")
    intruder = make_user(role="user", email="intruder@example.com")
    trek = make_trek()
    booking = make_booking(owner, trek)

    login_as(intruder)
    resp = client.post(f"/user/bookings/{booking.id}/cancel", data={})
    assert resp.status_code == 403

    from app.extensions import db
    db.session.refresh(booking)
    assert booking.status == BookingStatus.BOOKED  # untouched


def test_user_cannot_view_another_users_booking_detail(client, make_user, make_trek, make_booking, login_as):
    owner = make_user(role="user", email="owner2@example.com")
    intruder = make_user(role="user", email="intruder2@example.com")
    booking = make_booking(owner, make_trek())

    login_as(intruder)
    resp = client.get(f"/user/bookings/{booking.id}")
    assert resp.status_code == 403


def test_staff_cannot_manage_unassigned_trek(client, make_user, make_trek, login_as):
    staff_a = make_user(role="staff", email="staff_a@example.com")
    staff_b = make_user(role="staff", email="staff_b@example.com")
    trek = make_trek(assigned_staff_id=staff_a.id)

    login_as(staff_b)
    resp = client.get(f"/staff/treks/{trek.id}")
    assert resp.status_code == 403

    resp = client.post(f"/staff/treks/{trek.id}/update", data={"available_slots": "0"})
    assert resp.status_code == 403


def test_staff_can_manage_own_assigned_trek(client, make_user, make_trek, login_as):
    staff = make_user(role="staff", email="staff_owner@example.com")
    trek = make_trek(assigned_staff_id=staff.id)

    login_as(staff)
    resp = client.get(f"/staff/treks/{trek.id}")
    assert resp.status_code == 200
