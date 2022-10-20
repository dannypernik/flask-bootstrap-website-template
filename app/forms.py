from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, \
    SubmitField, IntegerField, SelectField, validators
from wtforms.fields.html5 import DateField
from wtforms.validators import ValidationError, InputRequired, DataRequired, \
    Email, EqualTo, Length
from app.models import User


def validate_email(self, email):
    user = User.query.filter_by(email=email.data).first()
    if user is not None:
        raise ValidationError('An account already exists for ' + user.email + '.')


class ContactForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    phone = StringField('Phone number (optional)', render_kw={"placeholder": "Phone number (optional)"})
    subject = StringField('Subject', render_kw={'placeholder': 'Subject'}, default='Message')
    message = TextAreaField('Message', render_kw={"placeholder": "Message"}, \
        validators=[InputRequired()])
    submit = SubmitField('Submit')


class EmailListForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address"), \
            validate_email])
    submit = SubmitField()


class SignupForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address"), \
            validate_email])
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={"placeholder": "Last name"}, \
        validators=[InputRequired()])
    password = PasswordField('Password', render_kw={"placeholder": "Password"}, \
        validators=[InputRequired()])
    password2 = PasswordField('Repeat Password', render_kw={"placeholder": "Repeat Password"}, \
        validators=[InputRequired(), EqualTo('password',message="Passwords do not match.")])
    submit = SubmitField('Sign up')


class LoginForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    password = PasswordField('Password', render_kw={"placeholder": "Password"}, \
        validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    submit = SubmitField('Request password reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', render_kw={"placeholder": "New password"}, \
        validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', render_kw={"placeholder": "Verify password"}, \
        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset password')


def full_name(User):
    return User.first_name + " " + User.last_name


class UserForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={"placeholder": "Last name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    phone = StringField('Phone', render_kw={"placeholder": "Phone"})
    location = StringField('Location', render_kw={"placeholder": "Location"})
    status = SelectField('Status', choices=[('none','None'),('active', 'Active'),('paused','Paused'),('inactive','Inactive')])
    role = SelectField('Role', choices=[('student', 'Student'),('parent', 'Parent'),('admin','Admin')])
    parent_id = SelectField('Parent', coerce=int)
    is_admin = BooleanField('Admin')
    submit = SubmitField('Save')

    def __init__(self, original_email, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('An account already exists for ' + user.email + '.')