"""
Centralized role-check decorators; replaces the four near-identical
`login_required` + role-check pairs copy-pasted across the original app's
route files.

Plain login gating still comes straight from flask_login.login_required;
these decorators only add the role layer on top, and are meant to be
stacked directly beneath it, e.g.:

    @bp.route("/admin/treks")
    @login_required
    @admin_required
    def manage_treks(): ...
"""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user

from app.models.enums import StaffStatus, UserRole


def role_required(*roles):
    """Aborts 403 if the logged-in user's role isn't one of `roles`.

    A 403 (not a silent redirect-with-flash like the original app) is
    intentional: reaching this decorator already implies the visitor is
    authenticated (it's always stacked under login_required), so a wrong
    role here is a genuine authorization failure, not a "please log in"
    situation, and should read that way to the visitor.
    """

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))
            if current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


admin_required = role_required(UserRole.ADMIN)
staff_required = role_required(UserRole.STAFF)
user_required = role_required(UserRole.USER)


def approved_staff_required(view):
    """staff_required, plus a live approval-status check.

    Unlike a bare role mismatch, "staff but not yet approved" isn't
    treated as a hard 403; it's a normal, expected state for a brand new
    staff account, so it redirects to a friendly status page explaining
    where their application stands instead. This is defense-in-depth: the
    global before_request guard (app/__init__.py) already force-logs-out
    any staff member whose approval is revoked mid-session, so in practice
    this mostly protects the moment right after registration.
    """

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if current_user.role != UserRole.STAFF:
            abort(403)
        profile = current_user.staff_profile
        if not profile or profile.staff_status != StaffStatus.APPROVED:
            return redirect(url_for("staff.pending_status"))
        return view(*args, **kwargs)

    return wrapped
