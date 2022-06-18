from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, \
    SubmitField, IntegerField, RadioField, SelectField
from wtforms.fields.html5 import DateField, EmailField
from wtforms.validators import ValidationError, InputRequired, DataRequired, \
    Email, EqualTo, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from app.models import User, Idea

class IntroForm(FlaskForm):
    description = TextAreaField('Description', render_kw={'rows':'2'}, validators=[InputRequired()])
    first_name = StringField('First name', render_kw={'placeholder': 'First name'}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={'placeholder': 'Last name'}, \
        validators=[InputRequired()])
    email = EmailField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    submit = SubmitField('Save')

class InquiryForm(FlaskForm):
    first_name = StringField('First name', render_kw={'placeholder': 'First name'}, \
        validators=[InputRequired()])
    email = EmailField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    phone = StringField('Phone number (optional)', render_kw={'placeholder': 'Phone number (optional)'})
    subject = StringField('Subject', render_kw={'placeholder': 'Subject'}, default='Message')
    message = TextAreaField('Message', render_kw={'placeholder': 'Message'}, \
        validators=[InputRequired()])
    submit = SubmitField('Submit')

class IdeaForm(FlaskForm):
    name = StringField('Idea name', render_kw={'placeholder': 'Idea name'}, \
        validators=[InputRequired()])
    tagline = StringField('Tagline', render_kw={'placeholder': 'Tagline'}, \
        validators=[InputRequired()])
    description = TextAreaField('Description', render_kw={'placeholder': 'Description', 'rows':'10'}, \
        validators=[InputRequired()])
    submit = SubmitField('Save')


class SignupForm(FlaskForm):
    email = StringField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    first_name = StringField('First name', render_kw={'placeholder': 'First name'}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={'placeholder': 'Last name'}, \
        validators=[InputRequired()])
    password = PasswordField('Password', render_kw={'placeholder': 'Password'}, \
        validators=[InputRequired()])
    password2 = PasswordField('Repeat Password', render_kw={'placeholder': 'Repeat Password'}, \
        validators=[InputRequired(), EqualTo('password',message='Passwords do not match.')])
    submit = SubmitField('Join the movement')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('This email address has already been registered.')


class LoginForm(FlaskForm):
    email = StringField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    password = PasswordField('Password', render_kw={'placeholder': 'Password'}, \
        validators=[InputRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Log in')


class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    submit = SubmitField('Request password reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', render_kw={'placeholder': 'New password'}, \
        validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', render_kw={'placeholder': 'Verify password'}, \
        validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset password')


def get_tutors():
    return Tutor.query

def tutor_name(Tutor):
    return Tutor.first_name + ' ' + Tutor.last_name


class UserForm(FlaskForm):
    first_name = StringField('First name', render_kw={'placeholder': 'First name'}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={'placeholder': 'Last name'}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={'placeholder': 'Email address'})
    phone = StringField('Phone', render_kw={'placeholder': 'Phone'})
    about_me = StringField('About me', render_kw={'placeholder': 'About me'})
    is_admin = BooleanField('Admin')
    submit = SubmitField('Save')