"""Staff application approval/rejection workflow."""
from app.models import Staff, StaffStatus
from app.services import staff_service


def test_admin_can_approve_pending_staff(client, make_user, login_as, db):
    admin = make_user(role="admin")
    staff = make_user(role="staff", email="pending@example.com", staff_status=StaffStatus.PENDING)

    login_as(admin)
    resp = client.post(f"/admin/staff/{staff.staff_profile.id}/approve", data={}, follow_redirects=True)
    assert resp.status_code == 200

    db.session.refresh(staff.staff_profile)
    assert staff.staff_profile.staff_status == StaffStatus.APPROVED
    assert staff.staff_profile.reviewed_by_id == admin.id


def test_admin_can_reject_pending_staff(client, make_user, login_as, db):
    admin = make_user(role="admin")
    staff = make_user(role="staff", email="pending2@example.com", staff_status=StaffStatus.PENDING)

    login_as(admin)
    client.post(f"/admin/staff/{staff.staff_profile.id}/reject", data={}, follow_redirects=True)

    db.session.refresh(staff.staff_profile)
    assert staff.staff_profile.staff_status == StaffStatus.REJECTED


def test_pending_staff_blocked_from_dashboard(client, make_user, login_as):
    staff = make_user(role="staff", staff_status=StaffStatus.PENDING)
    login_as(staff)
    resp = client.get("/staff/dashboard", follow_redirects=True)
    assert resp.request.path == "/staff/pending"


def test_rejected_staff_blocked_from_dashboard(client, make_user, login_as):
    staff = make_user(role="staff", staff_status=StaffStatus.REJECTED)
    login_as(staff)
    resp = client.get("/staff/dashboard", follow_redirects=True)
    assert resp.request.path == "/staff/pending"


def test_approved_staff_reaches_dashboard(client, make_user, login_as):
    staff = make_user(role="staff", staff_status=StaffStatus.APPROVED)
    login_as(staff)
    resp = client.get("/staff/dashboard")
    assert resp.status_code == 200


def test_revoking_approval_mid_session_blocks_next_dashboard_request(client, make_user, login_as, db):
    """The spec's 'de-approve an already-approved staff member' gap: no
    forced logout needed — approved_staff_required re-checks live status
    on every dashboard-guarded request, so access is lost immediately."""
    staff = make_user(role="staff", staff_status=StaffStatus.APPROVED)
    login_as(staff)
    assert client.get("/staff/dashboard").status_code == 200

    staff.staff_profile.staff_status = StaffStatus.PENDING
    db.session.commit()

    resp = client.get("/staff/dashboard", follow_redirects=True)
    assert resp.request.path == "/staff/pending"
    # Still logged in (not force-logged-out) — can still reach their profile.
    assert client.get("/staff/profile").status_code == 200
