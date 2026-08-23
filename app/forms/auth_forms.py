from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp, ValidationError

from app.models import User

_PHONE_RE = r"^[0-9+\-\s()]{7,20}$"


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me")


class RegisterForm(FlaskForm):
    name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=96)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=128)])
    phone = StringField("Phone", validators=[Optional(), Regexp(_PHONE_RE, message="Enter a valid phone number.")])
    role = SelectField(
        "I am registering as a",
        choices=[("user", "Trekker — I want to book treks"), ("staff", "Trek Staff — I want to guide treks")],
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
