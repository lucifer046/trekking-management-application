from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models.enums import UserRole, enum_values
from app.models.mixins import TimestampMixin


class User(UserMixin, TimestampMixin, db.Model):
    """
    Every account on the platform — trekker, staff guide, or admin — lives
    in this one table, distinguished by `role`. Staff carry an additional
    one-to-one Staff profile with approval workflow state.

    Note on Flask-Login: this class defines its own `is_active` *column*,
    which shadows UserMixin's `is_active` property (Python attribute
    resolution finds the column descriptor defined directly on User before
    it would ever consult the mixin), so Flask-Login's notion of "is this
    session allowed" automatically reflects the real business column with
    no extra glue code.
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(96), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum(UserRole, native_enum=False, length=16, values_callable=enum_values), nullable=False, index=True
    )
    avatar_path = db.Column(db.String(255), nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_blocked = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # Relationships
    staff_profile = db.relationship(
        "Staff",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
        # Staff has two FKs to user.id (user_id, reviewed_by_id) — without
        # this, SQLAlchemy can't tell which one defines this relationship.
        foreign_keys="Staff.user_id",
    )
    bookings = db.relationship(
        "Booking", back_populates="trekker", lazy="dynamic", foreign_keys="Booking.user_id"
    )
    assigned_treks = db.relationship(
        "Trek", back_populates="assigned_staff", foreign_keys="Trek.assigned_staff_id"
    )
    wishlist_items = db.relationship(
        "Wishlist", back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Notification.created_at.desc()",
    )
    reviews = db.relationship("Review", back_populates="user")

    # --- password helpers -------------------------------------------------
    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    # --- convenience --------------------------------------------------
    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_staff(self):
        return self.role == UserRole.STAFF

    @property
    def is_trekker(self):
        return self.role == UserRole.USER

    @property
    def is_approved_staff(self):
        from app.models.enums import StaffStatus

        return bool(
            self.is_staff and self.staff_profile and self.staff_profile.staff_status == StaffStatus.APPROVED
        )

    @property
    def account_is_usable(self):
        """False once blocked/deactivated — used by the before_request guard."""
        return self.is_active and not self.is_blocked

    def __repr__(self):
        return f"<User {self.id} {self.email!r} role={self.role}>"
