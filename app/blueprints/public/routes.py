from datetime import date

from flask import Blueprint, abort, current_app, render_template, request
from flask_login import current_user
from sqlalchemy import func, or_

from app.extensions import db
from app.forms.booking_forms import BookingForm
from app.forms.review_forms import ReviewForm
from app.models import (
    BOOKABLE_TREK_STATUSES,
    PUBLIC_TREK_STATUSES,
    Booking,
    BookingStatus,
    Difficulty,
    Location,
    Review,
    StaffStatus,
    Trek,
    TrekStatus,
    User,
)
from app.services import review_service
from app.services.wishlist_service import is_wishlisted

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    featured = (
        Trek.query.filter(Trek.status.in_(PUBLIC_TREK_STATUSES), Trek.is_featured.is_(True))
        .order_by(Trek.start_date.asc())
        .limit(6)
        .all()
    )
    if len(featured) < 3:
        # Not enough curated picks yet — top up with the soonest open treks
        # so the section never looks sparse on a fresh install.
        extra = (
            Trek.query.filter(Trek.status == TrekStatus.OPEN, ~Trek.id.in_([t.id for t in featured]))
            .order_by(Trek.start_date.asc())
            .limit(6 - len(featured))
            .all()
        )
        featured = featured + extra

    popular_locations = (
        db.session.query(Location, func.count(Trek.id).label("trek_count"))
        .join(Trek, Trek.location_id == Location.id)
        .filter(Trek.status.in_(PUBLIC_TREK_STATUSES))
        .group_by(Location.id)
        .order_by(func.count(Trek.id).desc())
        .limit(6)
        .all()
    )

    stats = {
        "treks_completed": Trek.query.filter_by(status=TrekStatus.COMPLETED).count(),
        "happy_trekkers": db.session.query(func.count(func.distinct(Booking.user_id)))
        .filter(Booking.status == BookingStatus.COMPLETED)
        .scalar()
        or 0,
        "destinations": Location.query.count(),
        "active_guides": User.query.join(User.staff_profile).filter_by(staff_status=StaffStatus.APPROVED).count(),
    }

    testimonials = (
        Review.query.filter(Review.rating >= 4, Review.body.isnot(None))
        .order_by(Review.created_at.desc())
        .limit(6)
        .all()
    )

    return render_template(
        "public/home.html",
        featured_treks=featured,
        popular_locations=popular_locations,
        stats=stats,
        testimonials=testimonials,
    )


@bp.route("/explore")
def explore():
    query = request.args.get("q", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    location = request.args.get("location", "").strip()
    duration = request.args.get("duration", "").strip()  # short(<=3) / medium(4-7) / long(8+)
    sort = request.args.get("sort", "start_date")
    only_available = request.args.get("available") == "1"
    page = request.args.get("page", 1, type=int)

    treks_query = Trek.query.filter(Trek.status.in_(PUBLIC_TREK_STATUSES)).join(Location)

    if query:
        like = f"%{query}%"
        treks_query = treks_query.filter(or_(Trek.name.ilike(like), Location.name.ilike(like)))
    if difficulty in {d.value for d in Difficulty}:
        treks_query = treks_query.filter(Trek.difficulty == difficulty)
    if location:
        treks_query = treks_query.filter(Location.name == location)
    if duration == "short":
        treks_query = treks_query.filter(Trek.duration_days <= 3)
    elif duration == "medium":
        treks_query = treks_query.filter(Trek.duration_days.between(4, 7))
    elif duration == "long":
        treks_query = treks_query.filter(Trek.duration_days >= 8)
    if only_available:
        treks_query = treks_query.filter(Trek.status.in_(BOOKABLE_TREK_STATUSES), Trek.available_slots > 0)

    sort_map = {
        "start_date": Trek.start_date.asc(),
        "price_low": Trek.price.asc(),
        "price_high": Trek.price.desc(),
        "duration": Trek.duration_days.asc(),
        "newest": Trek.created_at.desc(),
    }
    treks_query = treks_query.order_by(sort_map.get(sort, Trek.start_date.asc()))

    pagination = treks_query.paginate(page=page, per_page=current_app.config["ITEMS_PER_PAGE"], error_out=False)

    all_locations = Location.query.order_by(Location.name).all()

    return render_template(
        "public/explore.html",
        pagination=pagination,
        treks=pagination.items,
        locations=all_locations,
        difficulties=list(Difficulty),
        filters={
            "q": query,
            "difficulty": difficulty,
            "location": location,
            "duration": duration,
            "sort": sort,
            "available": only_available,
        },
    )


@bp.route("/treks/<slug>")
def trek_detail(slug):
    trek = Trek.query.filter_by(slug=slug).first_or_404()

    # Draft / pending-approval treks are only visible to admins previewing
    # them and the staff member assigned to them — not to the public.
    if trek.status not in PUBLIC_TREK_STATUSES:
        allowed = current_user.is_authenticated and (
            current_user.is_admin or (current_user.is_staff and trek.assigned_staff_id == current_user.id)
        )
        if not allowed:
            abort(404)

    related = (
        Trek.query.filter(
            Trek.location_id == trek.location_id, Trek.status.in_(PUBLIC_TREK_STATUSES), Trek.id != trek.id
        )
        .limit(3)
        .all()
    )

    booking_form = BookingForm()
    review_form = ReviewForm()

    reviewable_booking = None
    saved = False
    if current_user.is_authenticated and current_user.is_trekker:
        pending = review_service.reviewable_bookings(current_user, trek)
        reviewable_booking = pending[0] if pending else None
        saved = is_wishlisted(current_user, trek)

    return render_template(
        "public/trek_detail.html",
        trek=trek,
        related_treks=related,
        booking_form=booking_form,
        review_form=review_form,
        reviewable_booking=reviewable_booking,
        is_saved=saved,
        today=date.today(),
    )
