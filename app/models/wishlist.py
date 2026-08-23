from app.extensions import db


class Wishlist(db.Model):
    """
    A trekker's saved/favorited trek. Unlike Booking, a plain DB-level
    UniqueConstraint is safe here — toggling save/unsave is idempotent and
    carries no historical-record requirement, so there's no need for the
    service-layer "active row" workaround Booking requires.
    """

    __tablename__ = "wishlist"
    __table_args__ = (db.UniqueConstraint("user_id", "trek_id", name="uq_wishlist_user_trek"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    trek_id = db.Column(db.Integer, db.ForeignKey("trek.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=db.func.now(), nullable=False)

    user = db.relationship("User", back_populates="wishlist_items")
    trek = db.relationship("Trek", back_populates="wishlisted_by")

    def __repr__(self):
        return f"<Wishlist user={self.user_id} trek={self.trek_id}>"
