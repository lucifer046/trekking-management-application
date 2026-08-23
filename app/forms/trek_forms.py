from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, DateField, DecimalField, IntegerField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError

from app.models import Difficulty


class TrekForm(FlaskForm):
    """Admin create/edit form covering every editorial/logistics field.
    Deliberately has NO status field — status only ever changes through
    TrekStatusForm -> trek_service.transition_status(), never a raw
    dropdown save, so the legal-transition table can't be bypassed."""

    name = StringField("Trek name", validators=[DataRequired(), Length(min=3, max=140)])
    location_name = StringField("Location", validators=[DataRequired(), Length(max=80)])
    location_state = StringField("State / Region", validators=[Optional(), Length(max=80)])
    difficulty = SelectField(
        "Difficulty", choices=[(d.value, d.value.capitalize()) for d in Difficulty], validators=[DataRequired()]
    )
    duration_days = IntegerField("Duration (days)", validators=[DataRequired(), NumberRange(min=1, max=90)])
    start_date = DateField("Start date", validators=[DataRequired()])
    end_date = DateField("End date", validators=[DataRequired()])
    capacity = IntegerField("Capacity", validators=[DataRequired(), NumberRange(min=1, max=500)])
    price = DecimalField("Price per person", places=2, validators=[DataRequired(), NumberRange(min=0)])
    meeting_point = StringField("Meeting point", validators=[Optional(), Length(max=255)])
    description = TextAreaField("Overview", validators=[DataRequired(), Length(max=4000)])
    highlights = TextAreaField("Highlights (one per line)", validators=[Optional(), Length(max=4000)])
    itinerary = TextAreaField("Itinerary (one line per day)", validators=[Optional(), Length(max=6000)])
    requirements = TextAreaField("Requirements (one per line)", validators=[Optional(), Length(max=4000)])
    safety_info = TextAreaField("Safety information", validators=[Optional(), Length(max=4000)])
    cancellation_policy = TextAreaField("Cancellation policy", validators=[Optional(), Length(max=2000)])
    is_featured = BooleanField("Feature on homepage")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before the start date.")


class TrekImageForm(FlaskForm):
    image = FileField(
        "Photo", validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only (jpg, png, webp).")]
    )
    alt_text = StringField("Description (for accessibility)", validators=[Optional(), Length(max=160)])
    is_primary = BooleanField("Set as primary photo")


class AssignStaffForm(FlaskForm):
    staff_user_id = SelectField("Assign guide", coerce=int, validators=[DataRequired()])


class TrekStatusForm(FlaskForm):
    """Choices are populated per-request by the route from the legal
    next-states for the trek's *current* status (and further narrowed for
    staff vs admin) — never hardcoded here, so an illegal transition can't
    even be submitted, let alone silently accepted."""

    new_status = SelectField("Change status to", validators=[DataRequired()])


class StaffTrekOperationalForm(FlaskForm):
    """The narrow set of fields the spec allows staff to touch on their
    assigned trek — everything editorial (name/description/price/...)
    stays admin-only via TrekForm."""

    available_slots = IntegerField("Available slots", validators=[DataRequired(), NumberRange(min=0, max=500)])
