from flask_wtf import FlaskForm
from wtforms import DateField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp, ValidationError

from app.forms.auth_forms import GENDER_CHOICES, _dob_not_in_future

_PHONE_RE = r"^[0-9+\-\s()]{7,20}$"


class EditProfileForm(FlaskForm):
    """The account owner's own edit-profile form. Deliberately carries no
    `email` field at all, not even a disabled one: email immutability (see
    the module docstring on User.email) has to hold even against a
    hand-crafted POST, and the simplest way to guarantee a route can never
    accidentally write an attacker-supplied email is for the form that
    backs it to have no field capable of parsing one out of the request in
    the first place. Password lives in its own ChangePasswordForm/route
    entirely, per the spec's "separate profile editing from password
    changes" (section 29): mixing an optional password change into a
    general profile-edit form is also why the previous version of this
    form never required the current password before accepting a new one.
    """

    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=96)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    date_of_birth = DateField("Date of birth", validators=[Optional(), _dob_not_in_future])
    gender = SelectField("Gender", choices=[("", "Select (optional)")] + GENDER_CHOICES, validators=[Optional()])
    city = StringField("City", validators=[Optional(), Length(max=80)])


class StaffEditProfileForm(EditProfileForm):
    experience = TextAreaField("Guiding experience", validators=[Optional(), Length(max=2000)])


class ChangePasswordForm(FlaskForm):
    """Requires the current password (verified against the logged-in
    user's own hash in the route, not here — this form only shapes/
    validates the submitted data) before accepting a new one; the
    previous combined profile form skipped this entirely."""

    current_password = PasswordField("Current password", validators=[DataRequired()])
    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_new_password = PasswordField(
        "Confirm new password", validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )
