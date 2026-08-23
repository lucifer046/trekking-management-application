from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db, limiter
from app.forms.auth_forms import LoginForm, RegisterForm
from app.forms.booking_forms import ConfirmActionForm
from app.models import Staff, StaffStatus, User, UserRole
from app.services import activity_log_service

bp = Blueprint("auth", __name__)


def _role_home_endpoint(user):
    if user.role == UserRole.ADMIN:
        return "admin.dashboard"
    if user.role == UserRole.STAFF:
        return "staff.dashboard" if user.is_approved_staff else "staff.pending_status"
    return "user.dashboard"


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
            return render_template("auth/login.html", form=form), 401

        if not user.account_is_usable:
            flash("Your account has been deactivated or blocked. Contact support for help.", "danger")
            return render_template("auth/login.html", form=form), 403

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.name.split(' ')[0]}!", "success")
        return redirect(url_for(_role_home_endpoint(user)))

    return render_template("auth/login.html", form=form)


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

    return render_template("auth/register.html", form=form)


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    form = ConfirmActionForm()
    if form.validate_on_submit():
        logout_user()
        flash("Logged out successfully.", "info")
    return redirect(url_for("public.home"))
