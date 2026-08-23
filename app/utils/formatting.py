"""
Jinja filters/globals shared by every template. Centralizing status →
label/color mapping here replaces the scattered if/elif badge-coloring
chains that were copy-pasted into almost every template in the original
app (`{% if b.status == 'Booked' %}bg-success{% elif ... %}`).
"""
from datetime import date, datetime

from app.models.enums import BookingStatus, Difficulty, StaffStatus, TrekStatus

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
        return {"label": "—", "tone": "neutral"}
    key = value.value if hasattr(value, "value") else str(value)
    for enum_val, (label, tone) in _STATUS_META.items():
        if enum_val.value == key:
            return {"label": label, "tone": tone}
    return {"label": key.replace("_", " ").title(), "tone": "neutral"}


def format_date(value, fmt="%d %b %Y"):
    if not value:
        return "—"
    return value.strftime(fmt)


def format_datetime(value, fmt="%d %b %Y, %I:%M %p"):
    if not value:
        return "—"
    return value.strftime(fmt)


def format_currency(value, currency="INR"):
    if value is None:
        return "—"
    symbol = {"INR": "₹", "USD": "$", "EUR": "€"}.get(currency, currency + " ")
    return f"{symbol}{float(value):,.0f}"


def time_until(value):
    """'in 12 days' / '3 days ago' / 'today' — used on trek cards & dashboards."""
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
    app.jinja_env.filters["format_date"] = format_date
    app.jinja_env.filters["format_datetime"] = format_datetime
    app.jinja_env.filters["format_currency"] = format_currency
    app.jinja_env.filters["time_until"] = time_until
    app.jinja_env.globals["now"] = datetime.utcnow
