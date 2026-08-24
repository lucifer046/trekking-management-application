from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, ValidationError

from app.forms.auth_forms import GENDER_CHOICES, _dob_not_in_future
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


class AdminEditUserForm(FlaskForm):
    """Admin editing an *existing* trekker's account (spec section 26).
    No `email` field, same reasoning as EditProfileForm: email immutability
    applies to every role, admin included, and it has to hold against a
    crafted request too, not just the rendered form. No `role` field
    either, per the spec's explicit "do not expose role editing unless the
    existing permission architecture explicitly supports controlled role
    management" (it doesn't; role is fixed at registration in this app)."""

    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=96)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    date_of_birth = DateField("Date of birth", validators=[Optional(), _dob_not_in_future])
    gender = SelectField("Gender", choices=[("", "Select (optional)")] + GENDER_CHOICES, validators=[Optional()])
    city = StringField("City", validators=[Optional(), Length(max=80)])
    is_blocked = BooleanField("Blacklisted")


class AdminEditStaffForm(AdminEditUserForm):
    """Same permitted fields as AdminEditUserForm, plus the staff-specific
    ones; approval state is handled through the existing dedicated
    approve/reject actions (staff_service), not folded into this generic
    save, so it keeps writing its own activity-log entries and
    notifications exactly as it already does."""

    experience = TextAreaField("Guiding experience", validators=[Optional(), Length(max=2000)])
    staff_status = SelectField(
        "Approval status",
        choices=[(s.value, s.value.capitalize()) for s in StaffStatus],
        validators=[DataRequired()],
    )


class AdminResetPasswordForm(FlaskForm):
    """Admin resetting someone else's password. No current-password check
    (the admin doesn't and shouldn't know it); always produces a brand
    new hash, never reveals or reuses the old one."""

    new_password = PasswordField("New password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_new_password = PasswordField(
        "Confirm new password", validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")]
    )
