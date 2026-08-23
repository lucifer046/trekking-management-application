"""Save/unsave a trek. Shared by the plain-form route (user blueprint,
works with JS disabled) and the JSON toggle endpoint (api blueprint, used
for the optimistic heart-icon toggle on trek cards)."""
from app.extensions import db
from app.models import Wishlist


def toggle_wishlist(user, trek):
    """Returns True if the trek is now saved, False if it was just removed."""
    existing = Wishlist.query.filter_by(user_id=user.id, trek_id=trek.id).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        return False

    db.session.add(Wishlist(user_id=user.id, trek_id=trek.id))
    db.session.commit()
    return True


def is_wishlisted(user, trek):
    if not user or not user.is_authenticated:
        return False
    return Wishlist.query.filter_by(user_id=user.id, trek_id=trek.id).first() is not None
