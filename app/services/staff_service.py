"""Staff approval workflow + trek assignment. Both admin actions, both
routed through here so notification + activity-log side effects can never
be forgotten by a route."""
from datetime import datetime, timezone

from app.extensions import db
from app.models import StaffStatus
from app.services import activity_log_service, notification_service
from app.services.exceptions import ServiceError


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def approve_staff(staff, actor):
    staff.staff_status = StaffStatus.APPROVED
    staff.reviewed_at = _utcnow()
    staff.reviewed_by_id = actor.id if actor else None

    notification_service.notify(
        staff.user,
        "staff_approved",
        "Application approved",
        "Your staff application has been approved. You can now access the staff dashboard.",
        link_url="/staff/dashboard",
    )
    activity_log_service.log(
        actor=actor,
        action="staff_approved",
        description=f"Staff application for {staff.user.name} was approved.",
        target_type="staff",
        target_id=staff.id,
    )
    db.session.commit()
    return staff


def reject_staff(staff, actor):
    staff.staff_status = StaffStatus.REJECTED
    staff.reviewed_at = _utcnow()
    staff.reviewed_by_id = actor.id if actor else None

    notification_service.notify(
        staff.user,
        "staff_rejected",
        "Application not approved",
        "Your staff application was not approved this time. Contact the platform admin for details.",
    )
    activity_log_service.log(
        actor=actor,
        action="staff_rejected",
        description=f"Staff application for {staff.user.name} was rejected.",
        target_type="staff",
        target_id=staff.id,
    )
    db.session.commit()
    return staff


def assign_staff(trek, staff_user, actor):
    if not staff_user.is_approved_staff:
        raise ServiceError("Only approved staff can be assigned to a trek.")

    previous = trek.assigned_staff
    trek.assigned_staff_id = staff_user.id

    notification_service.notify(
        staff_user,
        "trek_assigned",
        "New trek assignment",
        f"You've been assigned to lead {trek.name}.",
        link_url=f"/staff/treks/{trek.id}",
    )
    activity_log_service.log(
        actor=actor,
        action="staff_assigned",
        description=f"{staff_user.name} was assigned to trek '{trek.name}'"
        + (f" (previously {previous.name})." if previous else "."),
        target_type="trek",
        target_id=trek.id,
    )
    db.session.commit()
    return trek


def unassign_staff(trek, actor):
    previous = trek.assigned_staff
    trek.assigned_staff_id = None

    if previous:
        activity_log_service.log(
            actor=actor,
            action="staff_unassigned",
            description=f"{previous.name} was removed from trek '{trek.name}'.",
            target_type="trek",
            target_id=trek.id,
        )
    db.session.commit()
    return trek
