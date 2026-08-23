import os
from datetime import date

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms.admin_forms import StaffAddForm
from app.forms.booking_forms import ConfirmActionForm
from app.forms.trek_forms import AssignStaffForm, TrekForm, TrekImageForm, TrekStatusForm
from app.models import (
    TREK_STATUS_TRANSITIONS,
    ActivityLog,
    Booking,
    BookingStatus,
    Staff,
    StaffStatus,
    Trek,
    TrekImage,
    TrekStatus,
    User,
    UserRole,
)
from app.services import activity_log_service, staff_service, trek_service
from app.services.exceptions import ServiceError
from app.utils.decorators import admin_required
from app.utils.uploads import UploadRejected, delete_trek_image_file, save_trek_image

bp = Blueprint("admin", __name__)


# ---------------------------------------------------------------- dashboard
@bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    stats = {
        "total_users": User.query.filter_by(role=UserRole.USER).count(),
        "total_staff": User.query.filter_by(role=UserRole.STAFF).count(),
        "total_treks": Trek.query.count(),
        "total_bookings": Booking.query.count(),
        "active_bookings": Booking.query.filter_by(status=BookingStatus.BOOKED).count(),
        "upcoming_treks": Trek.query.filter(Trek.status == TrekStatus.OPEN, Trek.start_date >= date.today()).count(),
        "pending_staff": Staff.query.filter_by(staff_status=StaffStatus.PENDING).count(),
    }

    latest_bookings = Booking.query.order_by(Booking.booked_at.desc()).limit(6).all()
    latest_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(8).all()

    return render_template("admin/dashboard.html", stats=stats, latest_bookings=latest_bookings, latest_activity=latest_activity)


# ------------------------------------------------------------------ search
@bp.route("/search")
@login_required
@admin_required
def search():
    query = request.args.get("q", "").strip()
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("admin.dashboard"))

    like = f"%{query}%"
    id_match = int(query) if query.isdigit() else None

    trek_filters = [Trek.name.ilike(like)]
    user_filters = [User.name.ilike(like), User.email.ilike(like)]
    if id_match is not None:
        trek_filters.append(Trek.id == id_match)
        user_filters.append(User.id == id_match)

    treks = Trek.query.filter(or_(*trek_filters)).limit(25).all()
    users = User.query.filter(User.role == UserRole.USER, or_(*user_filters)).limit(25).all()

    staff_filters = [User.name.ilike(like), User.email.ilike(like)]
    if id_match is not None:
        staff_filters.append(Staff.id == id_match)
        staff_filters.append(User.id == id_match)
    staffs = Staff.query.join(Staff.user).filter(or_(*staff_filters)).limit(25).all()

    return render_template("admin/search_results.html", query=query, treks=treks, users=users, staffs=staffs)


# ------------------------------------------------------------------- treks
@bp.route("/treks")
@login_required
@admin_required
def manage_treks():
    status_filter = request.args.get("status", "all")
    query_text = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    treks_query = Trek.query
    if status_filter in {s.value for s in TrekStatus}:
        treks_query = treks_query.filter_by(status=TrekStatus(status_filter))
    if query_text:
        treks_query = treks_query.filter(Trek.name.ilike(f"%{query_text}%"))

    pagination = treks_query.order_by(Trek.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ROWS_PER_PAGE"], error_out=False
    )

    status_counts = {s.value: Trek.query.filter_by(status=s).count() for s in TrekStatus}
    status_counts["all"] = Trek.query.count()

    return render_template(
        "admin/manage_treks.html",
        pagination=pagination,
        treks=pagination.items,
        current_status=status_filter,
        status_counts=status_counts,
        query_text=query_text,
    )


@bp.route("/treks/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_trek():
    form = TrekForm()
    if form.validate_on_submit():
        trek = Trek(status=TrekStatus.DRAFT, created_by_id=current_user.id)
        trek_service.apply_form_to_trek(trek, form)
        trek.slug = trek_service.generate_slug(trek.name)
        db.session.add(trek)
        db.session.flush()

        activity_log_service.log(
            actor=current_user,
            action="trek_created",
            description=f"{current_user.name} created trek '{trek.name}'.",
            target_type="trek",
            target_id=trek.id,
        )
        db.session.commit()
        flash("Trek created as a draft. Move it through approval when it's ready to publish.", "success")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    return render_template("admin/trek_form.html", form=form, trek=None)


@bp.route("/treks/<int:trek_id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = TrekForm(obj=trek)
    if request.method == "GET":
        form.location_name.data = trek.location.name
        form.location_state.data = trek.location.state_region

    if form.validate_on_submit():
        trek_service.apply_form_to_trek(trek, form)
        activity_log_service.log(
            actor=current_user,
            action="trek_edited",
            description=f"{current_user.name} edited trek '{trek.name}'.",
            target_type="trek",
            target_id=trek.id,
        )
        db.session.commit()
        flash("Trek updated successfully.", "success")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    image_form = TrekImageForm()
    status_form = _build_admin_status_form(trek)
    assign_form = _build_assign_form(trek)

    return render_template(
        "admin/trek_form.html",
        form=form,
        trek=trek,
        image_form=image_form,
        status_form=status_form,
        assign_form=assign_form,
    )


@bp.route("/treks/<int:trek_id>/status", methods=["POST"])
@login_required
@admin_required
def change_trek_status(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = _build_admin_status_form(trek)
    if form.validate_on_submit():
        try:
            trek_service.transition_status(trek, TrekStatus(form.new_status.data), current_user)
            flash(f"Trek status updated to {form.new_status.data.replace('_', ' ').title()}.", "success")
        except ServiceError as err:
            flash(str(err), "danger")
    else:
        flash("Invalid status change requested.", "danger")
    return redirect(url_for("admin.edit_trek", trek_id=trek.id))


@bp.route("/treks/<int:trek_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash("Could not process the request.", "danger")
        return redirect(url_for("admin.manage_treks"))

    if trek.bookings.count() > 0:
        flash("This trek has booking history and can't be deleted — cancel it instead to preserve records.", "warning")
        return redirect(url_for("admin.edit_trek", trek_id=trek.id))

    name = trek.name
    db.session.delete(trek)
    activity_log_service.log(
        actor=current_user, action="trek_deleted", description=f"{current_user.name} deleted trek '{name}'.", target_type="trek"
    )
    db.session.commit()
    flash("Trek deleted successfully.", "success")
    return redirect(url_for("admin.manage_treks"))


@bp.route("/treks/<int:trek_id>/images/upload", methods=["POST"])
@login_required
@admin_required
def upload_trek_image(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = TrekImageForm()
    if form.validate_on_submit() and form.image.data:
        upload_root = os.path.join(current_app.static_folder, "uploads", "treks")
        try:
            relative_path = save_trek_image(
                form.image.data, trek.id, upload_root, current_app.config["UPLOAD_ALLOWED_EXTENSIONS"]
            )
        except UploadRejected as err:
            flash(str(err), "danger")
            return redirect(url_for("admin.edit_trek", trek_id=trek.id))

        make_primary = form.is_primary.data or not trek.images
        if make_primary:
            for image in trek.images:
                image.is_primary = False

        image = TrekImage(
            trek_id=trek.id,
            file_path=relative_path,
            alt_text=(form.alt_text.data or "").strip() or trek.name,
            is_primary=make_primary,
            sort_order=len(trek.images),
        )
        db.session.add(image)
        db.session.commit()
        flash("Photo uploaded.", "success")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")

    return redirect(url_for("admin.edit_trek", trek_id=trek.id))


@bp.route("/treks/<int:trek_id>/images/<int:image_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_trek_image(trek_id, image_id):
    image = TrekImage.query.get_or_404(image_id)
    if image.trek_id != trek_id:
        flash("Image does not belong to this trek.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek_id))

    form = ConfirmActionForm()
    if form.validate_on_submit():
        delete_trek_image_file(image.file_path, current_app.static_folder)
        was_primary = image.is_primary
        db.session.delete(image)
        db.session.flush()
        if was_primary:
            remaining = TrekImage.query.filter_by(trek_id=trek_id).order_by(TrekImage.sort_order).first()
            if remaining:
                remaining.is_primary = True
        db.session.commit()
        flash("Photo removed.", "success")

    return redirect(url_for("admin.edit_trek", trek_id=trek_id))


@bp.route("/treks/<int:trek_id>/images/<int:image_id>/primary", methods=["POST"])
@login_required
@admin_required
def set_primary_trek_image(trek_id, image_id):
    image = TrekImage.query.get_or_404(image_id)
    if image.trek_id != trek_id:
        flash("Image does not belong to this trek.", "danger")
        return redirect(url_for("admin.edit_trek", trek_id=trek_id))

    form = ConfirmActionForm()
    if form.validate_on_submit():
        for other in TrekImage.query.filter_by(trek_id=trek_id).all():
            other.is_primary = other.id == image_id
        db.session.commit()
        flash("Primary photo updated.", "success")

    return redirect(url_for("admin.edit_trek", trek_id=trek_id))


@bp.route("/treks/<int:trek_id>/assign", methods=["POST"])
@login_required
@admin_required
def assign_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = _build_assign_form(trek)
    if form.validate_on_submit():
        staff_user = User.query.get_or_404(form.staff_user_id.data)
        try:
            staff_service.assign_staff(trek, staff_user, current_user)
            flash(f"{staff_user.name} assigned to lead this trek.", "success")
        except ServiceError as err:
            flash(str(err), "danger")
    else:
        flash("Select a valid approved staff member.", "danger")
    return redirect(url_for("admin.edit_trek", trek_id=trek.id))


@bp.route("/treks/<int:trek_id>/unassign", methods=["POST"])
@login_required
@admin_required
def unassign_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        staff_service.unassign_staff(trek, current_user)
        flash("Staff unassigned from this trek.", "info")
    return redirect(url_for("admin.edit_trek", trek_id=trek.id))


@bp.route("/assignments")
@login_required
@admin_required
def assignments():
    approved_staff = (
        User.query.join(User.staff_profile).filter(Staff.staff_status == StaffStatus.APPROVED).order_by(User.name).all()
    )
    workload = [(staff, Trek.query.filter_by(assigned_staff_id=staff.id).filter(Trek.status != TrekStatus.CANCELLED).count()) for staff in approved_staff]

    unassigned_treks = (
        Trek.query.filter(Trek.assigned_staff_id.is_(None), Trek.status.notin_([TrekStatus.CANCELLED, TrekStatus.COMPLETED]))
        .order_by(Trek.start_date.asc())
        .all()
    )

    return render_template("admin/assignments.html", workload=workload, unassigned_treks=unassigned_treks)


# ------------------------------------------------------------------- staff
@bp.route("/staff")
@login_required
@admin_required
def manage_staff():
    status_filter = request.args.get("status", "pending")
    page = request.args.get("page", 1, type=int)

    query = Staff.query.join(Staff.user)
    if status_filter in {s.value for s in StaffStatus}:
        query = query.filter(Staff.staff_status == StaffStatus(status_filter))

    pagination = query.order_by(Staff.applied_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ROWS_PER_PAGE"], error_out=False
    )

    status_counts = {s.value: Staff.query.filter_by(staff_status=s).count() for s in StaffStatus}
    status_counts["all"] = Staff.query.count()

    return render_template(
        "admin/manage_staff.html",
        pagination=pagination,
        staffs=pagination.items,
        current_status=status_filter,
        status_counts=status_counts,
    )


@bp.route("/staff/add", methods=["GET", "POST"])
@login_required
@admin_required
def add_staff():
    form = StaffAddForm()
    if form.validate_on_submit():
        user = User(
            name=form.name.data.strip(),
            email=form.email.data.lower().strip(),
            phone=(form.phone.data or "").strip() or None,
            role=UserRole.STAFF,
            is_active=True,
            is_blocked=False,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        staff = Staff(
            user_id=user.id,
            contact=user.phone,
            experience=(form.experience.data or "").strip() or None,
            staff_status=StaffStatus(form.staff_status.data),
            reviewed_at=db.func.now(),
            reviewed_by_id=current_user.id,
        )
        db.session.add(staff)
        activity_log_service.log(
            actor=current_user,
            action="staff_added",
            description=f"{current_user.name} manually added staff account for {user.name}.",
            target_type="staff",
        )
        db.session.commit()
        flash("Staff account created.", "success")
        return redirect(url_for("admin.manage_staff"))

    return render_template("admin/add_staff.html", form=form)


@bp.route("/staff/<int:staff_id>/approve", methods=["POST"])
@login_required
@admin_required
def approve_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        staff_service.approve_staff(staff, current_user)
        flash("Staff application approved.", "success")
    return redirect(url_for("admin.manage_staff"))


@bp.route("/staff/<int:staff_id>/reject", methods=["POST"])
@login_required
@admin_required
def reject_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        staff_service.reject_staff(staff, current_user)
        flash("Staff application rejected.", "info")
    return redirect(url_for("admin.manage_staff"))


@bp.route("/staff/<int:staff_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_staff(staff_id):
    staff = Staff.query.get_or_404(staff_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        user = staff.user
        name = user.name
        db.session.delete(user)  # cascades to Staff via ON DELETE CASCADE
        activity_log_service.log(actor=current_user, action="staff_deleted", description=f"{current_user.name} deleted staff account for {name}.")
        db.session.commit()
        flash("Staff account deleted.", "success")
    return redirect(url_for("admin.manage_staff"))


# ------------------------------------------------------------------- users
@bp.route("/users")
@login_required
@admin_required
def manage_users():
    status_filter = request.args.get("status", "all")
    page = request.args.get("page", 1, type=int)

    query = User.query.filter_by(role=UserRole.USER)
    if status_filter == "active":
        query = query.filter_by(is_blocked=False)
    elif status_filter == "blacklisted":
        query = query.filter_by(is_blocked=True)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ROWS_PER_PAGE"], error_out=False
    )

    status_counts = {
        "all": User.query.filter_by(role=UserRole.USER).count(),
        "active": User.query.filter_by(role=UserRole.USER, is_blocked=False).count(),
        "blacklisted": User.query.filter_by(role=UserRole.USER, is_blocked=True).count(),
    }

    return render_template(
        "admin/manage_users.html", pagination=pagination, users=pagination.items, current_status=status_filter, status_counts=status_counts
    )


@bp.route("/users/<int:user_id>/blacklist", methods=["POST"])
@login_required
@admin_required
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        user.is_blocked = True
        activity_log_service.log(actor=current_user, action="user_blacklisted", description=f"{current_user.name} blacklisted {user.name}.", target_type="user", target_id=user.id)
        db.session.commit()
        flash("User blacklisted. Their active session will be signed out on their next request.", "success")
    return redirect(url_for("admin.manage_users"))


@bp.route("/users/<int:user_id>/unblacklist", methods=["POST"])
@login_required
@admin_required
def unblacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ConfirmActionForm()
    if form.validate_on_submit():
        user.is_blocked = False
        activity_log_service.log(actor=current_user, action="user_unblacklisted", description=f"{current_user.name} removed {user.name} from the blacklist.", target_type="user", target_id=user.id)
        db.session.commit()
        flash("User unblacklisted.", "success")
    return redirect(url_for("admin.manage_users"))


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    form = ConfirmActionForm()
    if not form.validate_on_submit():
        flash("Could not process the request.", "danger")
        return redirect(url_for("admin.manage_users"))

    if Booking.query.filter_by(user_id=user.id).count() > 0:
        flash("This user has booking history and can't be deleted — blacklist them instead to preserve records.", "warning")
        return redirect(url_for("admin.manage_users"))

    name = user.name
    db.session.delete(user)
    activity_log_service.log(actor=current_user, action="user_deleted", description=f"{current_user.name} deleted user account for {name}.")
    db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin.manage_users"))


# ---------------------------------------------------------------- bookings
@bp.route("/bookings")
@login_required
@admin_required
def manage_bookings():
    status_filter = request.args.get("status", "all")
    query_text = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Booking.query.join(Trek)
    if status_filter in {s.value for s in BookingStatus}:
        query = query.filter(Booking.status == BookingStatus(status_filter))
    if query_text:
        query = query.filter(or_(Trek.name.ilike(f"%{query_text}%"), Booking.booking_reference.ilike(f"%{query_text}%")))

    pagination = query.order_by(Booking.booked_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ROWS_PER_PAGE"], error_out=False
    )
    status_counts = {s.value: Booking.query.filter_by(status=s).count() for s in BookingStatus}
    status_counts["all"] = Booking.query.count()

    return render_template(
        "admin/all_bookings.html", pagination=pagination, bookings=pagination.items, current_status=status_filter, status_counts=status_counts, query_text=query_text
    )


# ------------------------------------------------------------------ activity
@bp.route("/activity")
@login_required
@admin_required
def activity_log():
    page = request.args.get("page", 1, type=int)
    pagination = ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(
        page=page, per_page=current_app.config["ADMIN_ROWS_PER_PAGE"], error_out=False
    )
    return render_template("admin/activity_log.html", pagination=pagination, entries=pagination.items)


# ------------------------------------------------------------------- helpers
def _build_admin_status_form(trek):
    legal_next = TREK_STATUS_TRANSITIONS.get(trek.status, set())
    form = TrekStatusForm()
    form.new_status.choices = [(s.value, s.value.replace("_", " ").title()) for s in legal_next]
    return form


def _build_assign_form(trek):
    approved_staff = User.query.join(User.staff_profile).filter(Staff.staff_status == StaffStatus.APPROVED).order_by(User.name).all()
    form = AssignStaffForm()
    form.staff_user_id.choices = [(s.id, s.name) for s in approved_staff]
    if trek.assigned_staff_id:
        form.staff_user_id.data = trek.assigned_staff_id
    return form
