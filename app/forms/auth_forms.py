from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, PasswordField, RadioField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, ValidationError

from app.models import Gender, User

_PHONE_RE = r"^[0-9+\-\s()]{7,20}$"

GENDER_CHOICES = [
    (Gender.MALE.value, "Male"),
    (Gender.FEMALE.value, "Female"),
    (Gender.NON_BINARY.value, "Non-binary"),
    (Gender.PREFER_NOT_TO_SAY.value, "Prefer not to say"),
]


def _dob_not_in_future(form, field):
    if field.data and field.data > date.today():
        raise ValidationError("Date of birth cannot be in the future.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=96)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=128)])

    date_of_birth = DateField("Date of birth", validators=[Optional(), _dob_not_in_future])
    gender = SelectField(
        "Gender",
        choices=[("", "Select (optional)")] + GENDER_CHOICES,
        validators=[Optional()],
    )
    city = StringField("City", validators=[Optional(), Length(max=80)])

    # Rendered as two clickable cards (see auth/register.html), not a
    # dropdown; a RadioField is the right underlying control for a
    # binary, always-visible choice like this one.
    role = RadioField(
        "I am joining as",
        choices=[("user", "Trekker"), ("staff", "Trek Staff")],
        default="user",
        validators=[DataRequired()],
    )
    experience = TextAreaField(
        "Guiding experience (staff applicants)", validators=[Optional(), Length(max=2000)]
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists. Try logging in instead.")

    def validate_role(self, field):
        if field.data not in ("user", "staff"):
            raise ValidationError("Invalid role selection.")
