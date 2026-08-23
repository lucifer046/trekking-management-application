from app.extensions import db
from app.models.mixins import TimestampMixin


class Location(db.Model, TimestampMixin):
    """
    A normalized trek destination (e.g. "Uttarakhand"). Kept as its own
    table rather than a free-text column on Trek so the homepage's "Popular
    Locations" section and the explore-page location filter can group/count
    treks reliably instead of matching inconsistently-formatted strings.
    """

    __tablename__ = "location"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    state_region = db.Column(db.String(80), nullable=True)
    country = db.Column(db.String(80), nullable=False, default="India")
    slug = db.Column(db.String(90), unique=True, nullable=False, index=True)
    cover_image_path = db.Column(db.String(255), nullable=True)

    treks = db.relationship("Trek", back_populates="location")

    @property
    def display_name(self):
        return f"{self.name}, {self.state_region}" if self.state_region else self.name

    def __repr__(self):
        return f"<Location {self.name!r}>"
