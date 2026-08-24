from decimal import Decimal

from app.extensions import db
from app.models.enums import TREK_STATUS_TRANSITIONS, Difficulty, TrekStatus, enum_values
from app.models.mixins import TimestampMixin


class Trek(db.Model, TimestampMixin):
    """
    A single trekking trip offering. `status` is the *only* lifecycle
    field (no separate approval_status; the state machine below already
    folds approval into one sequence, which avoids the two-source-of-truth
    bug a second field would invite). Never set `.status` directly from a
    route or template; always go through `can_transition_to()` /
    `app.services.trek_service.transition_status()`, which also handles the
    side effects (auto-completing bookings, cascading cancellation, etc.).
    """

    __tablename__ = "trek"
    __table_args__ = (
        db.CheckConstraint("capacity > 0", name="ck_trek_capacity_positive"),
        db.CheckConstraint("available_slots >= 0 AND available_slots <= capacity", name="ck_trek_slots_in_range"),
        db.CheckConstraint("end_date >= start_date", name="ck_trek_end_after_start"),
        db.CheckConstraint("duration_days > 0", name="ck_trek_duration_positive"),
        db.CheckConstraint("price >= 0", name="ck_trek_price_non_negative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)

    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=False, index=True)
    difficulty = db.Column(
        db.Enum(Difficulty, native_enum=False, length=16, values_callable=enum_values), nullable=False, index=True
    )

    duration_days = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False, index=True)
    end_date = db.Column(db.Date, nullable=False)

    capacity = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

    price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    currency = db.Column(db.String(3), nullable=False, default="INR")

    description = db.Column(db.Text, nullable=False, default="")
    highlights = db.Column(db.Text, nullable=True)
    itinerary = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    safety_info = db.Column(db.Text, nullable=True)
    cancellation_policy = db.Column(db.Text, nullable=True)
    meeting_point = db.Column(db.String(255), nullable=True)

    status = db.Column(
        db.Enum(TrekStatus, native_enum=False, length=24, values_callable=enum_values),
        nullable=False,
        default=TrekStatus.DRAFT,
        index=True,
    )
    is_featured = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # SET NULL (not the default NO ACTION/RESTRICT) so deleting a staff or
    # admin User account never blankly fails with an FK violation; both
    # of these are informational references, not data that needs to
    # block or cascade a user deletion the way Booking intentionally does.
    assigned_staff_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    location = db.relationship("Location", back_populates="treks")
    assigned_staff = db.relationship("User", back_populates="assigned_treks", foreign_keys=[assigned_staff_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    bookings = db.relationship("Booking", back_populates="trek", lazy="dynamic")
    images = db.relationship(
        "TrekImage",
        back_populates="trek",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TrekImage.sort_order",
    )
    reviews = db.relationship("Review", back_populates="trek", cascade="all, delete-orphan", passive_deletes=True)
    wishlisted_by = db.relationship(
        "Wishlist", back_populates="trek", cascade="all, delete-orphan", passive_deletes=True
    )

    # --- state machine ------------------------------------------------
    def can_transition_to(self, new_status: TrekStatus) -> bool:
        """Pure adjacency-table check; no DB access, no side effects."""
        return new_status in TREK_STATUS_TRANSITIONS.get(self.status, set())

    # --- derived / display helpers -------------------------------------
    @property
    def booked_slots(self):
        return self.capacity - self.available_slots

    @property
    def occupancy_pct(self):
        if not self.capacity:
            return 0
        return round((self.booked_slots / self.capacity) * 100)

    @property
    def is_bookable(self):
        from app.models.enums import BOOKABLE_TREK_STATUSES

        return self.status in BOOKABLE_TREK_STATUSES and self.available_slots > 0

    @property
    def average_rating(self):
        ratings = [r.rating for r in self.reviews]
        return round(sum(ratings) / len(ratings), 1) if ratings else None

    @property
    def review_count(self):
        return len(self.reviews)

    @property
    def primary_image(self):
        for image in self.images:
            if image.is_primary:
                return image
        return self.images[0] if self.images else None

    def itinerary_lines(self):
        return [line.strip() for line in (self.itinerary or "").splitlines() if line.strip()]

    def highlight_lines(self):
        return [line.strip() for line in (self.highlights or "").splitlines() if line.strip()]

    def requirement_lines(self):
        return [line.strip() for line in (self.requirements or "").splitlines() if line.strip()]

    def __repr__(self):
        return f"<Trek {self.id} {self.name!r} status={self.status}>"


class TrekImage(db.Model):
    """One of up to a few photos attached to a Trek. Exactly one row per
    trek should have is_primary=True; that invariant is enforced in
    app.utils.uploads (service code), not a DB-level partial unique index,
    since SQLite partial indexes need dialect-specific syntax for a
    low-value guarantee here."""

    __tablename__ = "trek_image"

    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("trek.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = db.Column(db.String(255), nullable=False)
    alt_text = db.Column(db.String(160), nullable=True)
    is_primary = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    uploaded_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    trek = db.relationship("Trek", back_populates="images")

    def __repr__(self):
        return f"<TrekImage {self.id} trek_id={self.trek_id}>"
