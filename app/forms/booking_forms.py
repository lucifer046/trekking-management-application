from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class BookingForm(FlaskForm):
    participant_count = IntegerField(
        "Number of participants", default=1, validators=[DataRequired(), NumberRange(min=1, max=20)]
    )
    special_requests = TextAreaField("Special requests (optional)", validators=[Optional(), Length(max=1000)])


class CancelBookingForm(FlaskForm):
    reason = StringField("Reason (optional)", validators=[Optional(), Length(max=255)])


class ConfirmActionForm(FlaskForm):
    """CSRF-only form backing every simple destructive POST action (staff
    approve/reject/delete, user blacklist/unblacklist/delete, trek
    delete, unassign, mark-notification-read, ...). These used to be bare
    GET links in the original app; giving each one a real (if tiny) form
    is what makes the POST + CSRF + confirm-modal pattern possible."""

    pass
