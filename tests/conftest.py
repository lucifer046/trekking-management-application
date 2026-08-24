"""
Shared pytest fixtures.

Uses a real temp-file SQLite database (not `sqlite://` in-memory) created
fresh for every test function, then dropped. In-memory SQLite has a
well-known footgun with Flask-SQLAlchemy: each new DBAPI connection gets
its own isolated in-memory database unless the engine is forced onto a
single shared connection (StaticPool). A real temp file sidesteps that
entirely, costs nothing meaningful at this schema size, and is trivially
debuggable; you can open the file directly if a test ever misbehaves.
"""
import os
import tempfile
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import (
    Booking, BookingStatus, Difficulty, Location, Staff, StaffStatus, Trek, TrekStatus, User, UserRole,
)
from app.services.trek_service import generate_slug


@pytest.fixture()
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".sqlite")
    flask_app = create_app("testing")
    flask_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_path

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def make_user(db):
    """Factory: make_user(role='user', **overrides) -> User (committed)."""

    def _make(role="user", password="Passw0rd!", name=None, email=None, **overrides):
        role_enum = UserRole(role) if not isinstance(role, UserRole) else role
        idx = User.query.count() + 1
        user = User(
            name=name or f"Test User {idx}",
            email=email or f"user{idx}@example.com",
            role=role_enum,
            is_active=overrides.pop("is_active", True),
            is_blocked=overrides.pop("is_blocked", False),
            phone=overrides.pop("phone", None),
            date_of_birth=overrides.pop("date_of_birth", None),
            gender=overrides.pop("gender", None),
            city=overrides.pop("city", None),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role_enum == UserRole.STAFF:
            staff_status = overrides.pop("staff_status", StaffStatus.APPROVED)
            staff = Staff(
                user_id=user.id,
                contact=user.phone,
                staff_status=StaffStatus(staff_status) if not isinstance(staff_status, StaffStatus) else staff_status,
            )
            db.session.add(staff)

        db.session.commit()
        user._plain_password = password  # convenience for login_as()
        return user

    return _make


@pytest.fixture()
def make_location(db):
    def _make(name="Test Region"):
        existing = Location.query.filter_by(name=name).first()
        if existing:
            return existing
        loc = Location(name=name, state_region="Test State", slug=generate_slug(name))
        db.session.add(loc)
        db.session.commit()
        return loc

    return _make


@pytest.fixture()
def make_trek(db, make_location):
    """Factory: make_trek(**overrides) -> Trek (committed). Defaults to an
    'open' trek starting 10 days from now with 10 slots, ready to book."""

    def _make(**overrides):
        location = overrides.pop("location", None) or make_location()
        start_date = overrides.pop("start_date", date.today() + timedelta(days=10))
        capacity = overrides.pop("capacity", 10)
        idx = Trek.query.count() + 1
        name = overrides.pop("name", f"Test Trek {idx}")
        trek = Trek(
            name=name,
            slug=overrides.pop("slug", None) or generate_slug(name),
            location_id=location.id,
            difficulty=overrides.pop("difficulty", Difficulty.MODERATE),
            duration_days=overrides.pop("duration_days", 5),
            start_date=start_date,
            end_date=overrides.pop("end_date", start_date + timedelta(days=5)),
            capacity=capacity,
            available_slots=overrides.pop("available_slots", capacity),
            price=overrides.pop("price", Decimal("5000.00")),
            description=overrides.pop("description", "A test trek."),
            status=overrides.pop("status", TrekStatus.OPEN),
            assigned_staff_id=overrides.pop("assigned_staff_id", None),
        )
        for key, value in overrides.items():
            setattr(trek, key, value)
        db.session.add(trek)
        db.session.commit()
        return trek

    return _make


@pytest.fixture()
def make_booking(db):
    def _make(user, trek, participant_count=1, status=BookingStatus.BOOKED, **overrides):
        booking = Booking(
            user_id=user.id, trek_id=trek.id, participant_count=participant_count,
            status=BookingStatus(status) if not isinstance(status, BookingStatus) else status,
            booking_reference=overrides.pop("booking_reference", f"TMA-TEST{Booking.query.count() + 1:04d}"),
        )
        db.session.add(booking)
        db.session.commit()
        return booking

    return _make


@pytest.fixture()
def login_as(client):
    """login_as(client, user); logs in via the real HTTP form (exercises
    the actual login view, not a session shortcut)."""

    def _login(user, password=None):
        return client.post(
            "/login",
            data={"email": user.email, "password": password or getattr(user, "_plain_password", "Passw0rd!")},
            follow_redirects=True,
        )

    return _login
