"""Registration's new profile fields, self-service profile editing,
password management, and admin profile management; per the "TMA
Authentication and Profile System Complete Redesign" spec, sections
56-58. Email immutability in particular is tested against a *manually
constructed* request carrying an `email` field the real form doesn't
expose, not just "the UI never shows a way to do it" — the backend has
to reject/ignore the field on its own.
"""
from datetime import date, timedelta

from app.extensions import db
from app.models import Gender, User

# -------------------------------------------------------------- registration


def test_register_new_trekker_with_profile_fields(client):
    resp = client.post(
        "/register",
        data={
            "name": "New Trekker",
            "phone": "+91 9876543210",
            "email": "new.trekker@example.com",
            "date_of_birth": "1998-06-15",
            "gender": "female",
            "city": "Pune",
            "role": "user",
            "password": "Passw0rd!",
            "confirm_password": "Passw0rd!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    user = User.query.filter_by(email="new.trekker@example.com").first()
    assert user is not None
    assert user.date_of_birth == date(1998, 6, 15)
    assert user.gender == Gender.FEMALE
    assert user.city == "Pune"


def test_register_new_staff_application(client):
    resp = client.post(
        "/register",
        data={
            "name": "New Guide",
            "email": "new.guide@example.com",
            "date_of_birth": "1990-01-01",
            "gender": "male",
            "city": "Dehradun",
            "role": "staff",
            "experience": "5 years guiding.",
            "password": "Passw0rd!",
            "confirm_password": "Passw0rd!",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    user = User.query.filter_by(email="new.guide@example.com").first()
    assert user.role.value == "staff"
    assert user.staff_profile.staff_status.value == "pending"


def test_register_duplicate_email_rejected(client, make_user):
    make_user(email="existing@example.com")
    resp = client.post(
        "/register",
        data={
            "name": "Someone Else", "email": "existing@example.com", "role": "user",
            "password": "Passw0rd!", "confirm_password": "Passw0rd!",
        },
    )
    assert resp.status_code == 200  # re-renders the form, not a redirect
    assert User.query.filter_by(email="existing@example.com").count() == 1


def test_register_invalid_email_rejected(client):
    resp = client.post(
        "/register",
        data={"name": "Bad Email", "email": "not-an-email", "role": "user", "password": "Passw0rd!", "confirm_password": "Passw0rd!"},
    )
    assert resp.status_code == 200
    assert User.query.filter_by(name="Bad Email").first() is None


def test_register_password_mismatch_rejected(client):
    resp = client.post(
        "/register",
        data={
            "name": "Mismatch", "email": "mismatch@example.com", "role": "user",
            "password": "Passw0rd!", "confirm_password": "SomethingElse!",
        },
    )
    assert resp.status_code == 200
    assert User.query.filter_by(email="mismatch@example.com").first() is None


def test_register_future_dob_rejected(client):
    future = (date.today() + timedelta(days=30)).isoformat()
    resp = client.post(
        "/register",
        data={
            "name": "Time Traveler", "email": "future@example.com", "role": "user",
            "date_of_birth": future, "password": "Passw0rd!", "confirm_password": "Passw0rd!",
        },
    )
    assert resp.status_code == 200
    assert User.query.filter_by(email="future@example.com").first() is None


def test_register_invalid_gender_rejected(client):
    resp = client.post(
        "/register",
        data={
            "name": "Bad Gender", "email": "badgender@example.com", "role": "user",
            "gender": "attack-helicopter", "password": "Passw0rd!", "confirm_password": "Passw0rd!",
        },
    )
    assert resp.status_code == 200
    assert User.query.filter_by(email="badgender@example.com").first() is None


def test_register_missing_required_fields_rejected(client):
    resp = client.post("/register", data={"email": "incomplete@example.com"})
    assert resp.status_code == 200
    assert User.query.filter_by(email="incomplete@example.com").first() is None


# ---------------------------------------------------------------- user profile


def test_user_can_update_permitted_fields(client, make_user, login_as):
    user = make_user(role="user", name="Old Name")
    login_as(user)
    resp = client.post(
        "/user/profile/edit",
        data={"name": "New Name", "phone": "+91 9000000000", "date_of_birth": "1995-03-20", "gender": "non_binary", "city": "Chennai"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(user)
    assert user.name == "New Name"
    assert user.phone == "+91 9000000000"
    assert user.date_of_birth == date(1995, 3, 20)
    assert user.gender == Gender.NON_BINARY
    assert user.city == "Chennai"


def test_user_cannot_change_email_via_crafted_request(client, make_user, login_as):
    """Regression test (spec section 57): even a manually constructed
    request carrying `email`, a field the real form doesn't expose,
    must not change it."""
    user = make_user(role="user", email="locked@example.com")
    old_email = user.email
    login_as(user)

    resp = client.post(
        "/user/profile/edit",
        data={"name": user.name, "email": "attacker@example.com"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(user)
    assert user.email == old_email
    assert User.query.filter_by(email="attacker@example.com").first() is None


def test_user_cannot_modify_role_or_status_via_profile_edit(client, make_user, login_as):
    user = make_user(role="user")
    login_as(user)
    client.post(
        "/user/profile/edit",
        data={"name": user.name, "role": "admin", "is_blocked": "y"},
        follow_redirects=True,
    )
    db.session.refresh(user)
    assert user.role.value == "user"
    assert user.is_blocked is False


# --------------------------------------------------------------- staff profile


def test_staff_can_update_permitted_fields(client, make_user, login_as):
    staff = make_user(role="staff")
    login_as(staff)
    resp = client.post(
        "/staff/profile/edit",
        data={"name": "Updated Guide", "city": "Manali", "experience": "10 years."},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(staff)
    assert staff.name == "Updated Guide"
    assert staff.city == "Manali"
    assert staff.staff_profile.experience == "10 years."


def test_staff_cannot_change_email(client, make_user, login_as):
    staff = make_user(role="staff", email="staff.locked@example.com")
    old_email = staff.email
    login_as(staff)
    client.post("/staff/profile/edit", data={"name": staff.name, "email": "sneaky@example.com"}, follow_redirects=True)
    db.session.refresh(staff)
    assert staff.email == old_email


def test_staff_cannot_modify_approval_state_via_self_service(client, make_user, login_as):
    from app.models import StaffStatus

    staff = make_user(role="staff", staff_status=StaffStatus.PENDING)
    login_as(staff)
    client.post(
        "/staff/profile/edit",
        data={"name": staff.name, "staff_status": "approved"},
        follow_redirects=True,
    )
    db.session.refresh(staff.staff_profile)
    assert staff.staff_profile.staff_status == StaffStatus.PENDING


# ------------------------------------------------------------- password change


def test_user_must_provide_current_password_to_change_it(client, make_user, login_as):
    user = make_user(role="user", password="OldPassw0rd!")
    login_as(user, password="OldPassw0rd!")
    resp = client.post(
        "/user/profile/password",
        data={"current_password": "WrongPassword!", "new_password": "NewPassw0rd!", "confirm_new_password": "NewPassw0rd!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(user)
    assert user.check_password("OldPassw0rd!") is True
    assert user.check_password("NewPassw0rd!") is False


def test_user_can_change_password_with_correct_current_password(client, make_user, login_as):
    user = make_user(role="user", password="OldPassw0rd!")
    login_as(user, password="OldPassw0rd!")
    resp = client.post(
        "/user/profile/password",
        data={"current_password": "OldPassw0rd!", "new_password": "NewPassw0rd!", "confirm_new_password": "NewPassw0rd!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(user)
    assert user.check_password("NewPassw0rd!") is True
    assert user.password_hash != "NewPassw0rd!"  # never stored in plaintext


def test_password_hash_never_rendered_on_profile_page(client, make_user, login_as):
    user = make_user(role="user")
    login_as(user)
    resp = client.get("/user/profile")
    assert user.password_hash not in resp.get_data(as_text=True)


# --------------------------------------------------------------- admin profile


def test_admin_can_edit_user(client, make_user, login_as):
    admin = make_user(role="admin")
    target = make_user(role="user", name="Before Edit")
    login_as(admin)
    resp = client.post(
        f"/admin/users/{target.id}/edit",
        data={"name": "After Edit", "city": "Jaipur"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(target)
    assert target.name == "After Edit"
    assert target.city == "Jaipur"


def test_admin_can_edit_staff(client, make_user, login_as):
    admin = make_user(role="admin")
    staff = make_user(role="staff", name="Before Edit")
    login_as(admin)
    resp = client.post(
        f"/admin/staff/{staff.staff_profile.id}/edit",
        data={"name": "After Edit", "city": "Leh", "staff_status": "approved"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    db.session.refresh(staff)
    assert staff.name == "After Edit"


def test_admin_cannot_change_user_email_via_crafted_request(client, make_user, login_as):
    admin = make_user(role="admin")
    target = make_user(role="user", email="untouchable@example.com")
    login_as(admin)
    client.post(
        f"/admin/users/{target.id}/edit",
        data={"name": target.name, "email": "changed-by-admin@example.com"},
        follow_redirects=True,
    )
    db.session.refresh(target)
    assert target.email == "untouchable@example.com"


def test_admin_password_reset_creates_new_hash_without_exposing_old_one(client, make_user, login_as):
    admin = make_user(role="admin")
    target = make_user(role="user", password="OriginalPassw0rd!")
    old_hash = target.password_hash
    login_as(admin)

    resp = client.post(
        f"/admin/users/{target.id}/reset-password",
        data={"new_password": "AdminSetThis!", "confirm_new_password": "AdminSetThis!"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert old_hash not in resp.get_data(as_text=True)  # old hash never exposed

    db.session.refresh(target)
    assert target.password_hash != old_hash
    assert target.check_password("AdminSetThis!") is True
    assert target.check_password("OriginalPassw0rd!") is False


def test_non_admin_cannot_reach_admin_profile_management(client, make_user, login_as):
    trekker = make_user(role="user")
    other = make_user(role="user", email="other@example.com")
    login_as(trekker)

    assert client.get(f"/admin/users/{other.id}").status_code == 403
    assert client.get(f"/admin/users/{other.id}/edit").status_code == 403
    assert client.post(f"/admin/users/{other.id}/reset-password", data={}).status_code == 403
