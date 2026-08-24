"""
Shared enumerations for status-like columns.

Each is a `str, Enum` subclass so values behave like plain strings in
Jinja templates, JSON responses, and equality checks (`trek.status ==
TrekStatus.OPEN` and `trek.status == "open"` both work), while still being
usable as a real Python Enum in code (`for s in TrekStatus: ...`).

Mapped via SQLAlchemy's `Enum(..., native_enum=False)` everywhere these are
used as a column type; SQLite has no native ENUM type, so this stores a
portable VARCHAR with a CHECK constraint instead of relying on dialect
auto-detection.
"""
from enum import Enum


def enum_values(enum_cls):
    """Pass as `values_callable=enum_values` on every `db.Enum(...)`
    column. Without it, SQLAlchemy stores/compares a stdlib Enum's
    `.name` (e.g. "BOOKED") by default, NOT `.value` ("booked"); which
    would silently break every lowercase-value comparison this codebase
    relies on (Jinja filters, URL query params, JSON, seed data, tests).
    """
    return [member.value for member in enum_cls]


class UserRole(str, Enum):
    ADMIN = "admin"
    STAFF = "staff"
    USER = "user"


class StaffStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Difficulty(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"


class TrekStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    OPEN = "open"
    CLOSED = "closed"
    STARTED = "started"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# Legal forward transitions for Trek.status. Enforced exclusively by
# Trek.can_transition_to() / trek_service.transition_status(): see
# app/models/trek.py and app/services/trek_service.py.
TREK_STATUS_TRANSITIONS = {
    TrekStatus.DRAFT: {TrekStatus.PENDING_APPROVAL, TrekStatus.APPROVED, TrekStatus.CANCELLED},
    TrekStatus.PENDING_APPROVAL: {TrekStatus.APPROVED, TrekStatus.CANCELLED},
    TrekStatus.APPROVED: {TrekStatus.OPEN, TrekStatus.CANCELLED},
    TrekStatus.OPEN: {TrekStatus.CLOSED, TrekStatus.STARTED, TrekStatus.CANCELLED},
    TrekStatus.CLOSED: {TrekStatus.OPEN, TrekStatus.STARTED, TrekStatus.CANCELLED},
    TrekStatus.STARTED: {TrekStatus.COMPLETED},
    TrekStatus.COMPLETED: set(),
    TrekStatus.CANCELLED: set(),
}

# Statuses under which a trek is visible/bookable to trekkers browsing the
# public site.
PUBLIC_TREK_STATUSES = {TrekStatus.OPEN, TrekStatus.CLOSED, TrekStatus.STARTED, TrekStatus.COMPLETED}
BOOKABLE_TREK_STATUSES = {TrekStatus.OPEN}


class BookingStatus(str, Enum):
    BOOKED = "booked"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
