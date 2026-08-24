"""
Single choke point for every Notification row the platform creates; see
spec section 24's trigger list (booking confirmed/cancelled, trek
updated/opened/closed/started/completed, staff approved/rejected, account
deactivated, ...). Nothing should ever `db.session.add(Notification(...))`
directly outside this module.

Does NOT call db.session.commit(); the calling service (booking_service,
trek_service, staff_service, ...) owns the transaction boundary so the
notification commits atomically together with whatever triggered it.
"""
from app.extensions import db
from app.models import Notification


def notify(user, type_, title, message, link_url=None):
    if user is None:
        return None
    notification = Notification(
        user_id=user.id,
        type=type_,
        title=title,
        message=message,
        link_url=link_url,
    )
    db.session.add(notification)
    return notification


def mark_read(notification):
    notification.is_read = True


def mark_all_read(user):
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
