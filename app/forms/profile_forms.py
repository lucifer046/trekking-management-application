from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField
from wtforms.validators import Email, EqualTo, Length, Optional, Regexp, ValidationError

from app.models import User

_PHONE_RE = r"^[0-9+\-\s()]{7,20}$"


class _BaseProfileForm(FlaskForm):
    """Shared name/email/phone/optional-password-change fields. Email
    uniqueness excludes the current user's own row; pass their id in via
    the constructor."""

    name = StringField("Full name", validators=[Length(min=2, max=96)])
    email = StringField("Email", validators=[Email(), Length(max=128)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    new_password = PasswordField(
        "New password (leave blank to keep current)", validators=[Optional(), Length(min=8, max=128)]
    )
    confirm_new_password = PasswordField(
        "Confirm new password", validators=[Optional(), EqualTo("new_password", message="Passwords must match.")]
    )

    def __init__(self, *args, current_user_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_user_id = current_user_id

    def validate_email(self, field):
        existing = User.query.filter(User.email == field.data.lower().strip(), User.id != self._current_user_id).first()
        if existing:
            raise ValidationError("That email is already in use by another account.")


class UserProfileForm(_BaseProfileForm):
    pass


class StaffProfileForm(_BaseProfileForm):
    experience = TextAreaField("Guiding experience", validators=[Optional(), Length(max=2000)])
