"""Staff-to-trek assignment workflow."""
from app.models import StaffStatus
from app.services import staff_service
from app.services.exceptions import ServiceError

import pytest


def test_admin_can_assign_approved_staff(client, make_user, make_trek, login_as, db):
    admin = make_user(role="admin")
    staff = make_user(role="staff", staff_status=StaffStatus.APPROVED)
    trek = make_trek()
    login_as(admin)

    resp = client.post(f"/admin/treks/{trek.id}/assign", data={"staff_user_id": str(staff.id)}, follow_redirects=True)
    assert resp.status_code == 200

    db.session.refresh(trek)
    assert trek.assigned_staff_id == staff.id


def test_admin_can_reassign_staff(client, make_user, make_trek, login_as, db):
    admin = make_user(role="admin")
    staff_a = make_user(role="staff", email="a@example.com", staff_status=StaffStatus.APPROVED)
    staff_b = make_user(role="staff", email="b@example.com", staff_status=StaffStatus.APPROVED)
    trek = make_trek(assigned_staff_id=staff_a.id)
    login_as(admin)

    client.post(f"/admin/treks/{trek.id}/assign", data={"staff_user_id": str(staff_b.id)}, follow_redirects=True)
    db.session.refresh(trek)
    assert trek.assigned_staff_id == staff_b.id


def test_admin_can_unassign_staff(client, make_user, make_trek, login_as, db):
    admin = make_user(role="admin")
    staff = make_user(role="staff", staff_status=StaffStatus.APPROVED)
    trek = make_trek(assigned_staff_id=staff.id)
    login_as(admin)

    client.post(f"/admin/treks/{trek.id}/unassign", data={}, follow_redirects=True)
    db.session.refresh(trek)
    assert trek.assigned_staff_id is None


def test_cannot_assign_unapproved_staff(db, make_user, make_trek):
    """Service-layer guard: assigning a pending/rejected staff member is
    rejected regardless of what the admin UI happens to submit."""
    admin = make_user(role="admin")
    pending_staff = make_user(role="staff", staff_status=StaffStatus.PENDING)
    trek = make_trek()

    with pytest.raises(ServiceError):
        staff_service.assign_staff(trek, pending_staff, admin)

    db.session.refresh(trek)
    assert trek.assigned_staff_id is None
