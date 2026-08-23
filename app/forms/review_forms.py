from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ReviewForm(FlaskForm):
    rating = IntegerField("Rating", validators=[DataRequired(), NumberRange(min=1, max=5)])
    title = StringField("Title (optional)", validators=[Optional(), Length(max=120)])
    body = TextAreaField("Your review (optional)", validators=[Optional(), Length(max=2000)])
