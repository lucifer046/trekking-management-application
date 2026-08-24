"""
Resource-ownership checks (IDOR guards). These are plain functions, not
decorators, because the target object must already be loaded (typically
via get_or_404 on a URL parameter) before ownership can be checked;
call them right after the fetch, before doing anything with the object.
"""
from flask import abort
from flask_login import current_user


def assert_owns_booking(booking):
    """A trekker may only view/cancel their own bookings. Admins bypass
    this (they reach booking management through admin-only routes that
    already gate on admin_required, so this check only needs to run for
    the user-facing booking routes)."""
    if booking.user_id != current_user.id:
        abort(403)


def assert_assigned_to_trek(trek):
    """Enforces the spec's core staff rule: 'Staff can only manage treks
    assigned to them', checked server-side on every staff-facing trek
    operation, never inferred from what the UI happens to show."""
    if trek.assigned_staff_id != current_user.id:
        abort(403)
