from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, SubmitField, IntegerField
from wtforms.validators import ValidationError, InputRequired, Email, EqualTo, Length
from app.models import User, Student

class InquiryForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    phone = StringField('Phone number (optional)', render_kw={"placeholder": "Phone number (optional)"})
    message = TextAreaField('Message', render_kw={"placeholder": "Message"}, \
        validators=[InputRequired()])
    submit = SubmitField('Submit')

class EmailForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    submit = SubmitField('Join the movement')

class SignupForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={"placeholder": "Last name"}, \
        validators=[InputRequired()])
    password = PasswordField('Password', render_kw={"placeholder": "Password"}, \
        validators=[InputRequired()])
    password2 = PasswordField('Repeat Password', render_kw={"placeholder": "Repeat Password"}, \
        validators=[InputRequired(), EqualTo('password',message="Passwords do not match.")])
    submit = SubmitField('Join the movement')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email address has already been registered.')

class LoginForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    password = PasswordField('Password', render_kw={"placeholder": "Password"}, \
        validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')

class EditProfileForm(FlaskForm):
    username = StringField ('Username', validators=[InputRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=500)])
    submit = SubmitField('Save')

class AddStudentForm(FlaskForm):
    student_name = StringField('Student name', render_kw={"placeholder": "Student name"}, \
        validators=[InputRequired()])
    student_email = StringField('Student Email address', render_kw={"placeholder": "Student Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    parent_name = StringField('Parent name', render_kw={"placeholder": "Parent name"}, \
        validators=[InputRequired()])
    parent_email = StringField('Parent Email address', render_kw={"placeholder": "Parent Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    timezone = IntegerField('Timezone', render_kw={"placeholder": "Timezone"}, \
        validators=[InputRequired()])
    location = StringField('Location', render_kw={"placeholder": "Location"}, \
        validators=[InputRequired()])
    active = BooleanField('Active?')
    submit = SubmitField('Save')
