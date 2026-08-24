from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError

from app.models import StaffStatus, User

_PHONE_RE = r"^[0-9+\-\s()]{7,20}$"


class StaffAddForm(FlaskForm):
    """Admin manually creating a staff account (spec section 23; distinct
    from a staff member self-registering and waiting for approval)."""

    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=96)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=128)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    password = PasswordField("Temporary password", validators=[DataRequired(), Length(min=8, max=128)])
    experience = TextAreaField("Guiding experience", validators=[Optional(), Length(max=2000)])
    staff_status = SelectField(
        "Initial status",
        choices=[(s.value, s.value.capitalize()) for s in StaffStatus],
        default=StaffStatus.APPROVED.value,
        validators=[DataRequired()],
    )

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("A user with this email already exists.")
