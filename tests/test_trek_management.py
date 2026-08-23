"""Admin trek creation/editing."""
from datetime import date, timedelta

from app.models import Trek, TrekStatus


def _valid_trek_form(**overrides):
    start = date.today() + timedelta(days=30)
    data = {
        "name": "Newly Created Trek",
        "location_name": "Test Region",
        "location_state": "Test State",
        "difficulty": "moderate",
        "duration_days": "5",
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=5)).isoformat(),
        "capacity": "10",
        "price": "5000",
        "meeting_point": "",
        "description": "A brand new trek.",
        "highlights": "",
        "itinerary": "",
        "requirements": "",
        "safety_info": "",
        "cancellation_policy": "",
    }
    data.update(overrides)
    return data


def test_admin_can_create_trek(client, make_user, login_as, db):
    admin = make_user(role="admin")
    login_as(admin)

    resp = client.post("/admin/treks/add", data=_valid_trek_form(), follow_redirects=True)
    assert resp.status_code == 200

    trek = Trek.query.filter_by(name="Newly Created Trek").first()
    assert trek is not None
    assert trek.status == TrekStatus.DRAFT  # new treks always start as draft
    assert trek.capacity == 10
    assert trek.available_slots == 10
    assert trek.slug  # auto-generated


def test_trek_creation_rejects_end_before_start(client, make_user, login_as, db):
    admin = make_user(role="admin")
    login_as(admin)
    start = date.today() + timedelta(days=30)

    client.post(
        "/admin/treks/add",
        data=_valid_trek_form(start_date=start.isoformat(), end_date=(start - timedelta(days=1)).isoformat()),
    )
    assert Trek.query.filter_by(name="Newly Created Trek").first() is None


def test_non_admin_cannot_create_trek(client, make_user, login_as, db):
    staff = make_user(role="staff")
    login_as(staff)
    resp = client.post("/admin/treks/add", data=_valid_trek_form())
    assert resp.status_code == 403
    assert Trek.query.filter_by(name="Newly Created Trek").first() is None


def test_admin_can_edit_trek(client, make_user, make_trek, login_as, db):
    admin = make_user(role="admin")
    trek = make_trek(status=TrekStatus.DRAFT)
    login_as(admin)

    resp = client.post(
        f"/admin/treks/{trek.id}/edit",
        data=_valid_trek_form(name="Updated Trek Name", capacity="20"),
        follow_redirects=True,
    )
    assert resp.status_code == 200

    db.session.refresh(trek)
    assert trek.name == "Updated Trek Name"
    assert trek.capacity == 20
    assert trek.available_slots == 20  # capacity grew with no bookings, so slots grew with it


def test_slug_unique_across_treks_with_same_name(client, make_user, login_as, db):
    admin = make_user(role="admin")
    login_as(admin)
    client.post("/admin/treks/add", data=_valid_trek_form(name="Duplicate Name Trek"))
    client.post("/admin/treks/add", data=_valid_trek_form(name="Duplicate Name Trek"))

    treks = Trek.query.filter_by(name="Duplicate Name Trek").all()
    assert len(treks) == 2
    assert treks[0].slug != treks[1].slug
