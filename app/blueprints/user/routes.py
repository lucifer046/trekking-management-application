from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms.booking_forms import BookingForm, CancelBookingForm, ConfirmActionForm
from app.forms.profile_forms import UserProfileForm
from app.forms.review_forms import ReviewForm
from app.models import Booking, BookingStatus, Notification, Trek, TrekStatus, Wishlist
from app.services import booking_service, notification_service, review_service
from app.services.exceptions import ServiceError
from app.services.wishlist_service import toggle_wishlist
from app.utils.decorators import user_required
from app.utils.permissions import assert_owns_booking

bp = Blueprint("user", __name__)


@bp.route("/dashboard")
@login_required
@user_required
def dashboard():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
    upcoming = [b for b in bookings if b.status == BookingStatus.BOOKED]
    completed = [b for b in bookings if b.status == BookingStatus.COMPLETED]
    cancelled = [b for b in bookings if b.status == BookingStatus.CANCELLED]

    recommended = (
        Trek.query.filter(Trek.status == TrekStatus.OPEN, Trek.available_slots > 0)
        .order_by(Trek.is_featured.desc(), Trek.start_date.asc())
        .limit(4)
        .all()
    )

    stats = {
        "total_bookings": len(bookings),
        "upcoming": len(upcoming),
        "completed": len(completed),
        "cancelled": len(cancelled),
        "wishlist_count": Wishlist.query.filter_by(user_id=current_user.id).count(),
    }

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template(
        "user/dashboard.html",
        bookings=bookings,
        upcoming=upcoming,
        completed=completed,
        recommended=recommended,
        stats=stats,
        notifications=notifications,
    )


@bp.route("/treks/<int:trek_id>/book", methods=["POST"])
@login_required
@user_required
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = BookingForm()
    if not form.validate_on_submit():
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
        return redirect(url_for("public.trek_detail", slug=trek.slug))

    try:
        booking = booking_service.create_booking(
            current_user, trek, form.participant_count.data, form.special_requests.data
        )
    except ServiceError as err:
        flash(str(err), "danger")
        return redirect(url_for("public.trek_detail", slug=trek.slug))

    flash("Trek booked successfully! Here are your confirmation details.", "success")
    return redirect(url_for("user.booking_detail", booking_id=booking.id))


@bp.route("/bookings")
@login_required
@user_required
def booking_history():
    status_filter = request.args.get("status", "all")
    query = Booking.query.filter_by(user_id=current_user.id)
    if status_filter in {s.value for s in BookingStatus}:
        # Convert the raw query-string value to the real enum member
        # rather than relying on SQLAlchemy's string coercion; explicit
        # and unambiguous.
        query = query.filter_by(status=BookingStatus(status_filter))
    bookings = query.order_by(Booking.booked_at.desc()).all()

    counts = {
        "all": Booking.query.filter_by(user_id=current_user.id).count(),
        "booked": Booking.query.filter_by(user_id=current_user.id, status=BookingStatus.BOOKED).count(),
        "completed": Booking.query.filter_by(user_id=current_user.id, status=BookingStatus.COMPLETED).count(),
        "cancelled": Booking.query.filter_by(user_id=current_user.id, status=BookingStatus.CANCELLED).count(),
    }

    return render_template("user/booking_history.html", bookings=bookings, current_status=status_filter, counts=counts)


@bp.route("/bookings/<int:booking_id>")
@login_required
@user_required
def booking_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    assert_owns_booking(booking)

    review_form = ReviewForm()
    cancel_form = CancelBookingForm()
    return render_template("user/booking_detail.html", booking=booking, review_form=review_form, cancel_form=cancel_form)


@bp.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
@user_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    assert_owns_booking(booking)

    form = CancelBookingForm()
    if not form.validate_on_submit():
        flash("Could not process the cancellation. Please try again.", "danger")
        return redirect(url_for("user.booking_detail", booking_id=booking.id))

    try:
        booking_service.cancel_booking(booking, current_user, form.reason.data)
        flash("Booking cancelled successfully.", "success")
    except ServiceError as err:
        flash(str(err), "danger")

    return redirect(url_for("user.booking_detail", booking_id=booking.id))


@bp.route("/bookings/<int:booking_id>/review", methods=["POST"])
@login_required
@user_required
def submit_review(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    assert_owns_booking(booking)

    form = ReviewForm()
    if form.validate_on_submit():
        try:
            review_service.create_review(booking, form.rating.data, form.title.data, form.body.data)
            flash("Thanks for sharing your experience!", "success")
        except ServiceError as err:
            flash(str(err), "danger")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")

    return redirect(url_for("user.booking_detail", booking_id=booking.id))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@user_required
def profile():
    form = UserProfileForm(current_user_id=current_user.id, obj=current_user)
    if form.validate_on_submit():
        current_user.name = form.name.data.strip()
        current_user.email = form.email.data.lower().strip()
        current_user.phone = (form.phone.data or "").strip() or None
        if form.new_password.data:
            current_user.set_password(form.new_password.data)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("user.profile"))

    booking_count = Booking.query.filter_by(user_id=current_user.id).count()
    completed_count = Booking.query.filter_by(user_id=current_user.id, status=BookingStatus.COMPLETED).count()
    return render_template("user/profile.html", form=form, booking_count=booking_count, completed_count=completed_count)


@bp.route("/wishlist")
@login_required
@user_required
def wishlist():
    items = Wishlist.query.filter_by(user_id=current_user.id).order_by(Wishlist.created_at.desc()).all()
    return render_template("user/wishlist.html", items=items)


@bp.route("/wishlist/<int:trek_id>/toggle", methods=["POST"])
@login_required
@user_required
def wishlist_toggle(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        saved = toggle_wishlist(current_user, trek)
        flash("Saved to your wishlist." if saved else "Removed from your wishlist.", "info")
    return redirect(request.referrer or url_for("public.trek_detail", slug=trek.slug))


@bp.route("/notifications")
@login_required
def notifications():
    items = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    unread_ids = [n.id for n in items if not n.is_read]
    if unread_ids:
        Notification.query.filter(Notification.id.in_(unread_ids)).update({"is_read": True}, synchronize_session=False)
        db.session.commit()
    return render_template("user/notifications.html", notifications=items)


@bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    form = ConfirmActionForm()
    if form.validate_on_submit():
        notification_service.mark_all_read(current_user)
        db.session.commit()
    return redirect(url_for("user.notifications"))
