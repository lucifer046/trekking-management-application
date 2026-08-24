from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from sqlalchemy import func

from app.extensions import db, limiter
from app.forms.auth_forms import LoginForm, RegisterForm
from app.forms.booking_forms import ConfirmActionForm
from app.models import PUBLIC_TREK_STATUSES, Location, Staff, StaffStatus, Trek, User, UserRole
from app.services import activity_log_service

bp = Blueprint("auth", __name__)


def _auth_stats():
    """Real, cheap counts (and, where one genuinely exists, a top
    location by trek count) for the auth pages' left-panel info strip
    (spec section 9: never invent fake statistics or a fake "currently
    exploring" location; omit entirely if there's nothing genuine to
    show). Same query shape public.home() already uses for its own
    "Popular Locations" section, just limited to one row here."""
    treks = Trek.query.filter(Trek.status.in_(PUBLIC_TREK_STATUSES)).count()
    locations = Location.query.count()
    staff = Staff.query.filter_by(staff_status=StaffStatus.APPROVED).count()
    if not (treks or locations or staff):
        return None

    top_location_row = (
        db.session.query(Location, func.count(Trek.id).label("trek_count"))
        .join(Trek, Trek.location_id == Location.id)
        .filter(Trek.status.in_(PUBLIC_TREK_STATUSES))
        .group_by(Location.id)
        .order_by(func.count(Trek.id).desc())
        .first()
    )
    top_location = top_location_row[0].display_name if top_location_row else None

    return {"treks": treks, "locations": locations, "staff": staff, "top_location": top_location}


def _role_home_endpoint(user):
    if user.role == UserRole.ADMIN:
        return "admin.dashboard"
    if user.role == UserRole.STAFF:
        return "staff.dashboard" if user.is_approved_staff else "staff.pending_status"
    return "user.dashboard"


def _safe_next_url():
    """Only ever follow a same-site relative path (e.g. '/treks/foo') from
    ?next=...; never an absolute URL, which would make this an
    open-redirect an attacker could use in a phishing link."""
    target = request.args.get("next") or request.form.get("next")
    if not target:
        return None
    parts = urlsplit(target)
    if parts.netloc or parts.scheme or not target.startswith("/"):
        return None
    return target


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for(_role_home_endpoint(current_user)))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form, stats=_auth_stats()), 401

        if not user.account_is_usable:
            flash("Your account has been deactivated or blocked. Contact support for help.", "danger")
            return render_template("auth/login.html", form=form, stats=_auth_stats()), 403

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.name.split(' ')[0]}!", "success")
        return redirect(_safe_next_url() or url_for(_role_home_endpoint(user)))

    return render_template("auth/login.html", form=form, stats=_auth_stats())


@bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for(_role_home_endpoint(current_user)))

    form = RegisterForm()
    if form.validate_on_submit():
        role = UserRole.STAFF if form.role.data == "staff" else UserRole.USER
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=(form.phone.data or "").strip() or None,
            date_of_birth=form.date_of_birth.data or None,
            gender=form.gender.data or None,
            city=(form.city.data or "").strip() or None,
            role=role,
            is_active=True,
            is_blocked=False,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        if role == UserRole.STAFF:
            staff = Staff(
                user_id=user.id,
                contact=user.phone,
                experience=(form.experience.data or "").strip() or None,
                staff_status=StaffStatus.PENDING,
            )
            db.session.add(staff)

        activity_log_service.log(
            actor=user,
            action="user_registered",
            description=f"{user.name} registered as {role.value}.",
            target_type="user",
            target_id=user.id,
        )
        db.session.commit()

        login_user(user)
        if role == UserRole.STAFF:
            flash("Registration successful! Your staff application is pending admin approval.", "success")
            return redirect(url_for("staff.pending_status"))

        flash("Registration successful! Welcome to TMA.", "success")
        return redirect(url_for("user.dashboard"))

    return render_template("auth/register.html", form=form, stats=_auth_stats())


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    form = ConfirmActionForm()
    if form.validate_on_submit():
        logout_user()
        flash("Logged out successfully.", "info")
    return redirect(url_for("public.home"))
