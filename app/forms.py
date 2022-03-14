from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, BooleanField, PasswordField, TextAreaField, SubmitField, IntegerField, RadioField, SelectField
from wtforms.validators import ValidationError, InputRequired, DataRequired, Email, EqualTo, Length
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from app.models import User, Student, Tutor

class InquiryForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    phone = StringField('Phone number (optional)', render_kw={"placeholder": "Phone number (optional)"})
    subject = StringField('Subject', render_kw={'placeholder': 'Subject'}, default='Message')
    message = TextAreaField('Message', render_kw={"placeholder": "Message"}, \
        validators=[InputRequired()])
    submit = SubmitField('Submit')

class TestStrategiesForm(FlaskForm):
    first_name = StringField('Your first name', render_kw={'placeholder': 'Your first name'}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    #test = RadioField('Test preference:', choices=[('sat', 'SAT'),('act','ACT'),('unsure','Not sure')], \
    #    validators=[InputRequired()])
    relation = RadioField('I am a:', choices=[('parent','Parent'),('student','Student')], \
        validators=[InputRequired()])
    parent_name = StringField('Parent\'s name', render_kw={'placeholder': 'Parent\'s name'})
    parent_email = StringField('Parent\'s email', render_kw={'placeholder': 'Parent\'s email'})
    student_name = StringField('Student\'s name', render_kw={'placeholder': 'Student\'s name'})
    #pronouns = RadioField('Student\'s preferred pronouns:', choices=[("he","He/him"),("she","She/her"),("they","They/them")], \
    #    validators=[InputRequired()])
    submit = SubmitField('Send me 10 Strategies to Master the SAT & ACT')

class PracticeTestForm(FlaskForm):
    first_name = StringField('Your first name', render_kw={'placeholder': 'Your first name'}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={'placeholder': 'Email address'}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    test = RadioField('Test preference:', choices=[('sat', 'SAT'),('act','ACT'),('unsure','Not sure')], \
        validators=[InputRequired()])
    relation = RadioField('I am a:', choices=[('parent','Parent'),('student','Student')], \
        validators=[InputRequired()])
    parent_name = StringField('Parent\'s name', render_kw={'placeholder': 'Parent\'s name'})
    parent_email = StringField('Parent\'s email', render_kw={'placeholder': 'Parent\'s email'})
    student_name = StringField('Student\'s name', render_kw={'placeholder': 'Student\'s name'})
    #pronouns = RadioField('Student\'s preferred pronouns:', choices=[("he","He/him"),("she","She/her"),("they","They/them")], \
    #    validators=[InputRequired()])
    submit = SubmitField('Send me a practice test')

class ScoreAnalysisForm(FlaskForm):
    student_first_name = StringField('Student\'s first name', render_kw={'placeholder': 'Student\'s first name'}, \
        validators=[InputRequired()])
    student_last_name = StringField('Student\'s last name', render_kw={'placeholder': 'Student\'s last name'}, \
        validators=[InputRequired()])
    school = StringField('School', render_kw={'placeholder': 'Student\'s school'}, \
        validators=[InputRequired()])
    parent_first_name = StringField('Parent\'s first name', render_kw={'placeholder': 'Parent\'s first name'}, \
        validators=[InputRequired()])
    parent_email = StringField('Parent\'s email address', render_kw={'placeholder': 'Parent\'s email address'}, \
        validators=[InputRequired(), Email(message='Please enter a valid email address')])
    submit = SubmitField('Send me the score analysis')

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


def get_tutors():
    return Tutor.query

def tutor_name(Tutor):
    return Tutor.first_name + " " + Tutor.last_name

class StudentForm(FlaskForm):
    student_name = StringField('Student name', render_kw={"placeholder": "Student name"}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={"placeholder": "Last name (optional)"})
    student_email = StringField('Student Email address', render_kw={"placeholder": "Student Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    parent_name = StringField('Parent name', render_kw={"placeholder": "Parent name"}, \
        validators=[InputRequired()])
    parent_email = StringField('Parent Email address', render_kw={"placeholder": "Parent Email address"}, \
        validators=[InputRequired(), Email(message="Please enter a valid email address")])
    secondary_email = StringField('Secondary Email (optional)', render_kw={"placeholder": "Secondary Email (optional)"})
    timezone = IntegerField('Timezone', render_kw={"placeholder": "Timezone"}, \
        validators=[InputRequired()])
    location = StringField('Location', render_kw={"placeholder": "Location"}, \
        validators=[InputRequired()])
    status = SelectField('Status', choices=[('active', 'Active'),('paused','Paused'),('inactive','Inactive')])
    tutor_id = QuerySelectField('Tutor', default=1, query_factory=get_tutors, get_label=tutor_name, \
        validators=[InputRequired()])
    submit = SubmitField('Save')


class TutorForm(FlaskForm):
    first_name = StringField('First name', render_kw={"placeholder": "First name"}, \
        validators=[InputRequired()])
    last_name = StringField('Last name', render_kw={"placeholder": "Last name"}, \
        validators=[InputRequired()])
    email = StringField('Email address', render_kw={"placeholder": "Email address"})
    timezone = IntegerField('Timezone', render_kw={"placeholder": "Timezone"}, \
        validators=[InputRequired()])
    status = SelectField('Status', choices=[('active', 'Active'),('paused','Paused'),('inactive','Inactive')])
    submit = SubmitField('Save')
