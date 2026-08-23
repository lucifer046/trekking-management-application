"""
Re-exports every model + enum so the rest of the app can do
`from app.models import User, Trek, TrekStatus, ...` without knowing which
submodule each lives in. Import order matters only in that mixins/enums
must be importable before the models that use them — Python handles that
naturally since each model module imports what it needs directly.
"""
from app.models.activity_log import ActivityLog
from app.models.booking import Booking
from app.models.enums import (
    BOOKABLE_TREK_STATUSES,
    PUBLIC_TREK_STATUSES,
    TREK_STATUS_TRANSITIONS,
    BookingStatus,
    Difficulty,
    StaffStatus,
    TrekStatus,
    UserRole,
)
from app.models.location import Location
from app.models.notification import Notification
from app.models.review import Review
from app.models.staff import Staff
from app.models.trek import Trek, TrekImage
from app.models.user import User
from app.models.wishlist import Wishlist

__all__ = [
    "User",
    "Staff",
    "Location",
    "Trek",
    "TrekImage",
    "Booking",
    "Review",
    "Notification",
    "Wishlist",
    "ActivityLog",
    "UserRole",
    "StaffStatus",
    "Difficulty",
    "TrekStatus",
    "BookingStatus",
    "TREK_STATUS_TRANSITIONS",
    "PUBLIC_TREK_STATUSES",
    "BOOKABLE_TREK_STATUSES",
]
