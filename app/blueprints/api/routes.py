"""
JSON/AJAX endpoints. Kept separate from the HTML-rendering blueprints so
CSRF-header handling and response-content-type conventions stay
consistent in one place. Every mutating endpoint here is still protected
by Flask-WTF's CSRFProtect — the frontend JS sends the token via the
`X-CSRFToken` header (read from the <meta name="csrf-token"> tag in the
base layout) instead of a form field.

Every chart endpoint aggregates real rows from the database — per the
spec's explicit "do not generate fake random numbers" instruction, there
is no synthetic/randomized data anywhere in this module.
"""
from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Booking, BookingStatus, Difficulty, Notification, Trek, TrekStatus
from app.services.wishlist_service import toggle_wishlist
from app.utils.decorators import admin_required, user_required

bp = Blueprint("api", __name__)


@bp.route("/wishlist/toggle/<int:trek_id>", methods=["POST"])
@login_required
@user_required
def wishlist_toggle(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    saved = toggle_wishlist(current_user, trek)
    return jsonify({"saved": saved})


@bp.route("/notifications")
@login_required
def recent_notifications():
    items = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(8)
        .all()
    )
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify(
        {
            "unread_count": unread_count,
            "notifications": [
                {
                    "id": n.id,
                    "title": n.title,
                    "message": n.message,
                    "link_url": n.link_url,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in items
            ],
        }
    )


@bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.user_id != current_user.id:
        return jsonify({"error": "not found"}), 404
    notification.is_read = True
    db.session.commit()
    return jsonify({"ok": True})


# ------------------------------------------------------------- admin charts
@bp.route("/charts/booking-trends")
@login_required
@admin_required
def booking_trends():
    month = db.func.strftime("%Y-%m", Booking.booked_at)
    rows = (
        db.session.query(month.label("month"), db.func.count(Booking.id))
        .group_by("month")
        .order_by("month")
        .limit(12)
        .all()
    )
    return jsonify({"labels": [r[0] for r in rows], "data": [r[1] for r in rows]})


@bp.route("/charts/trek-popularity")
@login_required
@admin_required
def trek_popularity():
    rows = (
        db.session.query(Trek.name, db.func.count(Booking.id).label("bookings"))
        .join(Booking, Booking.trek_id == Trek.id)
        .group_by(Trek.id)
        .order_by(db.func.count(Booking.id).desc())
        .limit(8)
        .all()
    )
    return jsonify({"labels": [r[0] for r in rows], "data": [r[1] for r in rows]})


@bp.route("/charts/difficulty-distribution")
@login_required
@admin_required
def difficulty_distribution():
    rows = db.session.query(Trek.difficulty, db.func.count(Trek.id)).group_by(Trek.difficulty).all()
    counts = {d.value: 0 for d in Difficulty}
    for difficulty, count in rows:
        counts[difficulty.value if hasattr(difficulty, "value") else difficulty] = count
    return jsonify({"labels": list(counts.keys()), "data": list(counts.values())})


@bp.route("/charts/booking-status")
@login_required
@admin_required
def booking_status_breakdown():
    rows = db.session.query(Booking.status, db.func.count(Booking.id)).group_by(Booking.status).all()
    counts = {s.value: 0 for s in BookingStatus}
    for status, count in rows:
        counts[status.value if hasattr(status, "value") else status] = count
    return jsonify({"labels": list(counts.keys()), "data": list(counts.values())})


@bp.route("/charts/capacity-utilization")
@login_required
@admin_required
def capacity_utilization():
    treks = Trek.query.filter(Trek.status.in_([TrekStatus.OPEN, TrekStatus.CLOSED, TrekStatus.STARTED])).order_by(
        Trek.start_date
    ).limit(10).all()
    return jsonify({"labels": [t.name for t in treks], "data": [t.occupancy_pct for t in treks]})
