from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.booking_forms import ConfirmActionForm
from app.forms.profile_forms import ChangePasswordForm, StaffEditProfileForm
from app.forms.trek_forms import StaffTrekOperationalForm, TrekStatusForm
from app.models import TREK_STATUS_TRANSITIONS, Booking, BookingStatus, Trek, TrekStatus
from app.services import activity_log_service, booking_service, trek_service
from app.services.exceptions import ServiceError
from app.utils.decorators import approved_staff_required, staff_required
from app.utils.permissions import assert_assigned_to_trek

bp = Blueprint("staff", __name__)

# Staff may only drive the day-to-day operational part of the lifecycle.
# The pre-launch approval workflow (draft/pending_approval/approved) and
# cancellation are admin-only judgment calls.
STAFF_OPERABLE_STATUSES = {TrekStatus.OPEN, TrekStatus.CLOSED, TrekStatus.STARTED, TrekStatus.COMPLETED}


@bp.route("/pending")
@login_required
@staff_required
def pending_status():
    profile = current_user.staff_profile
    if profile and profile.staff_status.value == "approved":
        return redirect(url_for("staff.dashboard"))
    return render_template("staff/pending_status.html", profile=profile)


@bp.route("/dashboard")
@login_required
@approved_staff_required
def dashboard():
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()
    upcoming = [t for t in assigned_treks if t.status in (TrekStatus.OPEN, TrekStatus.CLOSED, TrekStatus.APPROVED)]
    active = [t for t in assigned_treks if t.status == TrekStatus.STARTED]
    completed = [t for t in assigned_treks if t.status == TrekStatus.COMPLETED]

    total_participants = sum(t.booked_slots for t in assigned_treks)
    recent_bookings = (
        Booking.query.join(Trek).filter(Trek.assigned_staff_id == current_user.id).order_by(Booking.booked_at.desc()).limit(8).all()
    )

    stats = {
        "assigned_count": len(assigned_treks),
        "upcoming_count": len(upcoming),
        "active_count": len(active),
        "completed_count": len(completed),
        "total_participants": total_participants,
    }

    return render_template(
        "staff/dashboard.html",
        assigned_treks=assigned_treks,
        upcoming=upcoming,
        active=active,
        completed=completed,
        recent_bookings=recent_bookings,
        stats=stats,
    )


@bp.route("/treks/<int:trek_id>")
@login_required
@approved_staff_required
def view_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    assert_assigned_to_trek(trek)

    bookings = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booked_at.desc()).all()
    operational_form = StaffTrekOperationalForm(available_slots=trek.available_slots)
    status_form = _build_status_form(trek)

    return render_template(
        "staff/view_trek.html",
        trek=trek,
        bookings=bookings,
        operational_form=operational_form,
        status_form=status_form,
    )


@bp.route("/treks/<int:trek_id>/update", methods=["POST"])
@login_required
@approved_staff_required
def update_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    assert_assigned_to_trek(trek)

    form = StaffTrekOperationalForm()
    if form.validate_on_submit():
        trek.available_slots = min(trek.capacity, form.available_slots.data)
        activity_log_service.log(
            actor=current_user,
            action="trek_slots_updated",
            description=f"{current_user.name} set available slots for '{trek.name}' to {trek.available_slots}.",
            target_type="trek",
            target_id=trek.id,
        )
        db.session.commit()
        flash("Trek availability updated.", "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")

    return redirect(url_for("staff.view_trek", trek_id=trek.id))


@bp.route("/treks/<int:trek_id>/status", methods=["POST"])
@login_required
@approved_staff_required
def change_trek_status(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    assert_assigned_to_trek(trek)

    form = _build_status_form(trek)
    if form.validate_on_submit():
        try:
            trek_service.transition_status(trek, TrekStatus(form.new_status.data), current_user)
            flash(f"Trek status updated to {form.new_status.data.replace('_', ' ').title()}.", "success")
        except ServiceError as err:
            flash(str(err), "danger")
    else:
        flash("Invalid status change requested.", "danger")

    return redirect(url_for("staff.view_trek", trek_id=trek.id))


@bp.route("/treks/<int:trek_id>/remove-participant/<int:booking_id>", methods=["POST"])
@login_required
@approved_staff_required
def remove_participant(trek_id, booking_id):
    trek = Trek.query.get_or_404(trek_id)
    assert_assigned_to_trek(trek)

    booking = Booking.query.get_or_404(booking_id)
    if booking.trek_id != trek.id:
        abort(404)

    form = ConfirmActionForm()
    if form.validate_on_submit():
        try:
            booking_service.cancel_booking(booking, current_user, reason="Removed by trek staff.")
            flash("Participant removed from the roster.", "success")
        except ServiceError as err:
            flash(str(err), "danger")

    return redirect(url_for("staff.view_trek", trek_id=trek.id))


@bp.route("/profile")
@login_required
@staff_required
def profile():
    staff = current_user.staff_profile
    assigned_count = Trek.query.filter_by(assigned_staff_id=current_user.id).count()
    completed_count = Trek.query.filter_by(assigned_staff_id=current_user.id, status=TrekStatus.COMPLETED).count()
    return render_template("staff/profile.html", staff=staff, assigned_count=assigned_count, completed_count=completed_count)


@bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
@staff_required
def profile_edit():
    staff = current_user.staff_profile
    form = StaffEditProfileForm(obj=current_user)
    if request.method == "GET" and staff:
        form.experience.data = staff.experience

    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.phone = (form.phone.data or "").strip() or None
        current_user.date_of_birth = form.date_of_birth.data or None
        current_user.gender = form.gender.data or None
        current_user.city = (form.city.data or "").strip() or None
        if staff:
            staff.contact = current_user.phone
            staff.experience = (form.experience.data or "").strip() or None
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("staff.profile"))

    return render_template("staff/profile_edit.html", form=form, staff=staff)


@bp.route("/profile/password", methods=["GET", "POST"])
@login_required
@staff_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            activity_log_service.log(
                actor=current_user,
                action="password_changed",
                description=f"{current_user.name} changed their password.",
                target_type="user",
                target_id=current_user.id,
            )
            db.session.commit()
            flash("Password updated successfully.", "success")
            return redirect(url_for("staff.profile"))

    return render_template("staff/change_password.html", form=form)


def _build_status_form(trek):
    legal_next = TREK_STATUS_TRANSITIONS.get(trek.status, set()) & STAFF_OPERABLE_STATUSES
    form = TrekStatusForm()
    form.new_status.choices = [(s.value, s.value.replace("_", " ").title()) for s in legal_next]
    return form
