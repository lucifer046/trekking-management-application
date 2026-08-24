"""
Jinja filters/globals shared by every template. Centralizing status →
label/color mapping here replaces the scattered if/elif badge-coloring
chains that were copy-pasted into almost every template in the original
app (`{% if b.status == 'Booked' %}bg-success{% elif ... %}`).
"""
from datetime import date, datetime, timezone

from app.models.enums import BookingStatus, Difficulty, Gender, StaffStatus, TrekStatus

# status value -> (human label, tone). `tone` maps to a CSS class
# (`.badge-tone-<tone>`) defined once in components.css.
_STATUS_META = {
    TrekStatus.DRAFT: ("Draft", "neutral"),
    TrekStatus.PENDING_APPROVAL: ("Pending Approval", "warning"),
    TrekStatus.APPROVED: ("Approved", "info"),
    TrekStatus.OPEN: ("Open", "success"),
    TrekStatus.CLOSED: ("Closed", "warning"),
    TrekStatus.STARTED: ("Ongoing", "brand"),
    TrekStatus.COMPLETED: ("Completed", "neutral"),
    TrekStatus.CANCELLED: ("Cancelled", "danger"),
    BookingStatus.BOOKED: ("Booked", "success"),
    BookingStatus.CANCELLED: ("Cancelled", "danger"),
    BookingStatus.COMPLETED: ("Completed", "neutral"),
    StaffStatus.PENDING: ("Pending", "warning"),
    StaffStatus.APPROVED: ("Approved", "success"),
    StaffStatus.REJECTED: ("Rejected", "danger"),
    Difficulty.EASY: ("Easy", "success"),
    Difficulty.MODERATE: ("Moderate", "warning"),
    Difficulty.HARD: ("Hard", "danger"),
}


def status_meta(value):
    """Returns {'label': ..., 'tone': ...} for any status-like enum/string
    used across Trek/Booking/Staff/Difficulty. Unknown values degrade to a
    readable title-cased label with a neutral tone rather than raising, so
    a template never breaks on an unexpected value."""
    if value is None:
        return {"label": "N/A", "tone": "neutral"}
    key = value.value if hasattr(value, "value") else str(value)
    for enum_val, (label, tone) in _STATUS_META.items():
        if enum_val.value == key:
            return {"label": label, "tone": tone}
    return {"label": key.replace("_", " ").title(), "tone": "neutral"}


# ActivityLog.action value -> (human label, tone), same badge-tone
# palette as status_meta. Deliberately not tied to an enum (see
# ActivityLog's docstring: the action set is open-ended by design), so
# this is a plain string lookup with a readable fallback for anything
# not listed here — a future action code degrades to a title-cased
# label instead of ever showing a raw snake_case string in the UI.
_ACTION_META = {
    "platform_seeded": ("Platform seeded", "neutral"),
    "user_registered": ("Account registered", "info"),
    "user_blacklisted": ("User blacklisted", "danger"),
    "user_unblacklisted": ("User unblacklisted", "success"),
    "user_deleted": ("User deleted", "danger"),
    "staff_added": ("Staff added", "info"),
    "staff_approved": ("Staff approved", "success"),
    "staff_rejected": ("Staff rejected", "danger"),
    "staff_deleted": ("Staff deleted", "danger"),
    "staff_assigned": ("Staff assigned", "brand"),
    "staff_unassigned": ("Staff unassigned", "neutral"),
    "trek_created": ("Trek created", "info"),
    "trek_edited": ("Trek edited", "info"),
    "trek_deleted": ("Trek deleted", "danger"),
    "trek_slots_updated": ("Trek availability updated", "neutral"),
    "trek_status_changed": ("Trek status changed", "brand"),
    "booking_created": ("Booking created", "success"),
    "booking_cancelled": ("Booking cancelled", "danger"),
    "review_created": ("Review submitted", "info"),
    "password_changed": ("Password changed", "neutral"),
    "password_reset_by_admin": ("Password reset by admin", "warning"),
    "profile_updated_by_admin": ("Profile updated by admin", "info"),
}


def action_meta(value):
    """Returns {'label': ..., 'tone': ...} for an ActivityLog.action code."""
    if not value:
        return {"label": "N/A", "tone": "neutral"}
    if value in _ACTION_META:
        label, tone = _ACTION_META[value]
        return {"label": label, "tone": tone}
    return {"label": value.replace("_", " ").capitalize(), "tone": "neutral"}


_GENDER_LABELS = {
    Gender.MALE: "Male",
    Gender.FEMALE: "Female",
    Gender.NON_BINARY: "Non-binary",
    Gender.PREFER_NOT_TO_SAY: "Prefer not to say",
}


def gender_label(value):
    """Plain human label for a Gender enum/value; not a status, so no
    badge tone, just the display string profile pages need."""
    if not value:
        return "Not set"
    key = value.value if hasattr(value, "value") else str(value)
    for enum_val, label in _GENDER_LABELS.items():
        if enum_val.value == key:
            return label
    return key.replace("_", " ").title()


def format_date(value, fmt="%d %b %Y"):
    if not value:
        return "N/A"
    return value.strftime(fmt)


def format_datetime(value, fmt="%d %b %Y, %I:%M %p"):
    if not value:
        return "N/A"
    return value.strftime(fmt)


def format_currency(value, currency="INR"):
    if value is None:
        return "N/A"
    symbol = {"INR": "₹", "USD": "$", "EUR": "€"}.get(currency, currency + " ")
    return f"{symbol}{float(value):,.0f}"


def time_until(value):
    """'in 12 days' / '3 days ago' / 'today'; used on trek cards & dashboards."""
    if not value:
        return ""
    today = date.today()
    target = value.date() if isinstance(value, datetime) else value
    delta = (target - today).days
    if delta == 0:
        return "today"
    if delta > 0:
        return f"in {delta} day{'s' if delta != 1 else ''}"
    return f"{abs(delta)} day{'s' if abs(delta) != 1 else ''} ago"


def register_template_helpers(app):
    app.jinja_env.filters["status_meta"] = status_meta
    app.jinja_env.filters["action_meta"] = action_meta
    app.jinja_env.filters["gender_label"] = gender_label
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["format_currency"] = format_currency
    app.jinja_env.filters["time_until"] = time_until
    app.jinja_env.globals["now"] = lambda: datetime.now(timezone.utc)
