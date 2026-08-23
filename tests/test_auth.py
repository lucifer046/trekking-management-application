"""Registration, login, logout."""
from app.models import Staff, StaffStatus, User, UserRole


def test_register_creates_trekker(client, db):
    resp = client.post(
        "/register",
        data={"name": "New Trekker", "email": "new@example.com", "phone": "",
              "role": "user", "experience": "", "password": "Passw0rd!", "confirm_password": "Passw0rd!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    user = User.query.filter_by(email="new@example.com").first()
    assert user is not None
    assert user.role == UserRole.USER
    assert user.check_password("Passw0rd!")


def test_register_staff_creates_pending_profile(client, db):
    client.post(
        "/register",
        data={"name": "New Guide", "email": "guide@example.com", "phone": "",
              "role": "staff", "experience": "5 years", "password": "Passw0rd!", "confirm_password": "Passw0rd!"},
        follow_redirects=True,
    )
    user = User.query.filter_by(email="guide@example.com").first()
    assert user.role == UserRole.STAFF
    assert user.staff_profile.staff_status == StaffStatus.PENDING


def test_register_rejects_duplicate_email(client, make_user):
    make_user(email="dup@example.com")
    resp = client.post(
        "/register",
        data={"name": "Someone", "email": "dup@example.com", "phone": "",
              "role": "user", "experience": "", "password": "Passw0rd!", "confirm_password": "Passw0rd!"},
    )
    assert resp.status_code == 200  # re-renders the form, doesn't redirect
    assert User.query.filter_by(email="dup@example.com").count() == 1


def test_register_rejects_mismatched_passwords(client, db):
    client.post(
        "/register",
        data={"name": "X", "email": "x@example.com", "phone": "",
              "role": "user", "experience": "", "password": "Passw0rd!", "confirm_password": "Different1!"},
    )
    assert User.query.filter_by(email="x@example.com").first() is None


def test_login_success_redirects_to_role_dashboard(client, make_user):
    user = make_user(role="user", email="trekker@example.com")
    resp = client.post("/login", data={"email": user.email, "password": "Passw0rd!"}, follow_redirects=True)
    assert resp.status_code == 200
    assert b"dashboard" in resp.request.path.encode()


def test_login_wrong_password_rejected(client, make_user):
    user = make_user(email="a@example.com")
    resp = client.post("/login", data={"email": user.email, "password": "WrongPassword!"})
    assert resp.status_code == 401


def test_login_blocked_account_rejected(client, make_user):
    user = make_user(email="blocked@example.com", is_blocked=True)
    resp = client.post("/login", data={"email": user.email, "password": "Passw0rd!"})
    assert resp.status_code == 403


def test_login_inactive_account_rejected(client, make_user):
    user = make_user(email="inactive@example.com", is_active=False)
    resp = client.post("/login", data={"email": user.email, "password": "Passw0rd!"})
    assert resp.status_code == 403


def test_login_unapproved_staff_can_authenticate_but_sees_pending_page(client, make_user):
    """Unlike the original app (which refused login outright for pending
    staff), the rebuilt flow lets them authenticate and see *why* they
    don't have dashboard access yet."""
    staff = make_user(role="staff", email="pending@example.com", staff_status=StaffStatus.PENDING)
    resp = client.post("/login", data={"email": staff.email, "password": "Passw0rd!"}, follow_redirects=True)
    assert resp.status_code == 200
    assert resp.request.path == "/staff/pending"


def test_logout_clears_session(client, make_user, login_as):
    user = make_user()
    login_as(user)
    resp = client.get("/user/dashboard")
    assert resp.status_code == 200

    client.post("/logout")
    resp = client.get("/user/dashboard", follow_redirects=True)
    assert resp.request.path == "/login"
