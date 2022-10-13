import os
from flask import Flask, render_template, flash, Markup, redirect, url_for, \
    request, send_from_directory, send_file
from app import app, db, login, hcaptcha
from app.forms import InquiryForm, EmailListForm, TestStrategiesForm, SignupForm, LoginForm, \
    StudentForm, ScoreAnalysisForm, TestDateForm, UserForm, RequestPasswordResetForm, \
        ResetPasswordForm, TutorForm
from flask_login import current_user, login_user, logout_user, login_required, login_url
from app.models import User, TestDate, UserTestDate
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_contact_email, send_verification_email, send_password_reset_email, \
    send_test_strategies_email, send_score_analysis_email
from functools import wraps

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_viewed = datetime.utcnow()
        db.session.commit()

def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))

hello = app.config['HELLO_EMAIL']
phone = app.config['PHONE']
tests = sorted(set(TestDate.test for TestDate in TestDate.query.all()), reverse=True)

@app.context_processor
def inject_values():
    return dict(last_updated=dir_last_updated('app/static'), hello=hello, phone=phone)

def admin_required(f):
    @login_required
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            flash('You must have administrator privileges to access this page.', 'error')
            logout_user()
            return redirect(login_url('signin', next_url=request.url))
    return wrap


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = InquiryForm()
    if form.validate_on_submit():
        if hcaptcha.verify():
            pass
        else:
            flash('A computer has questioned your humanity. Please try again.', 'error')
            return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))
        user = User(first_name=form.first_name.data, email=form.email.data, phone=form.phone.data)
        message = form.message.data
        subject = form.subject.data
        email_status = send_contact_email(user, message, subject)
        if email_status == 200:
            flash('Please check ' + user.email + ' for a confirmation email. Thank you for reaching out!')
            return redirect(url_for('index', _anchor="home"))
        else:
            flash('Email failed to send, please contact ' + hello, 'error')
    return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))


@app.route('/about')
def about():
    return render_template('about.html', title="About")

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', title="Reviews")


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if current_user.is_authenticated:
        flash('You are already signed in.')
        return redirect(url_for('start_page'))
    form = LoginForm()
    signup_form = SignupForm()
    return render_template('signin.html', title='Sign in', form=form, signup_form=signup_form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = LoginForm()
    signup_form = SignupForm()
    if signup_form.validate_on_submit():
        user = User(first_name=signup_form.first_name.data, last_name=signup_form.last_name.data, \
        email=signup_form.email.data)
        user.set_password(signup_form.password.data)
        db.session.add(user)
        db.session.commit()
        email_status = send_verification_email(user)
        login_user(user)
        if email_status == 200:
            flash("Welcome! Please check your inbox to verify your email.")
        else:
            flash('Verification email failed to send, please contact ' + hello, 'error')
        next = request.args.get('next')
        if not next or url_parse(next).netloc != '':
            return redirect(url_for('start_page'))
        return redirect(next)
    return render_template('signin.html', title='Sign in', form=form, signup_form=signup_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already signed in.')
        return redirect(url_for('start_page'))
    form = LoginForm()
    signup_form = SignupForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('signin'))
        login_user(user)
        if user.is_verified != True:
            email_status = send_verification_email(user)
            if email_status == 200:
                flash('Please check your inbox to verify your email.')
            else:
                flash('Verification email did not send. Please contact ' + hello)
        next = request.args.get('next')
        if not next or url_parse(next).netloc != '':
            return redirect(url_for('start_page'))
        return redirect(next)
    return render_template('signin.html', title='Sign in', form=form, signup_form=signup_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('signin'))


@app.route('/start-page')
@login_required
def start_page():
    if current_user.is_admin:
        return redirect(url_for('students'))
    else:
        return redirect(url_for('test_reminders'))


@app.route('/verify-email/<token>', methods=['GET', 'POST'])
def verify_email(token):
    logout_user()
    user = User.verify_email_token(token)
    if user:
        login_user(user)
        user.is_verified = True
        db.session.add(user)
        db.session.commit()
        flash('Thank you for verifying your account.')
        return redirect(url_for('start_page'))
    else:
        flash('Your verification link is expired or invalid. Log in to receive a new link.')
        return redirect(url_for('signin'))


@app.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        if hcaptcha.verify():
            pass
        else:
            flash('A computer has questioned your humanity. Please try again.', 'error')
            return redirect(url_for('request_password_reset'))
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            email_status = send_password_reset_email(user)
            if email_status == 200:
                flash('Check your email for instructions to reset your password.')
            else:
                flash('Email failed to send, please contact ' + hello, 'error')
        else:
            flash('Check your email for instructions to reset your password')
        return redirect(url_for('signin'))
    return render_template('request-password-reset.html', title='Reset password', form=form)


@app.route('/set-password/<token>', methods=['GET', 'POST'])
def set_password(token):
    user = User.verify_email_token(token)
    if not user:
        flash('The password reset link is expired or invalid. Please try again.')
        return redirect(url_for('request_password_reset'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_verified = True
        db.session.commit()
        login_user(user)
        flash('Your password has been saved.')
        return redirect(url_for('start_page'))
    return render_template('set-password.html', form=form)


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    form = UserForm(None)
    roles = ['parent', 'tutor', 'student', 'admin']
    active_users = User.query.order_by(User.first_name).filter((User.status == 'active'))
    other_users = User.query.order_by(User.first_name).filter((User.status != 'active') | (User.status == None) | \
        (User.role.notin_(roles)) | (User.role == None))
    parents = User.query.filter_by(role='parent')
    parent_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in parents]
    tutors = User.query.filter_by(role='tutor')
    tutor_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in tutors]
    form.parent_id.choices = parent_list
    form.tutor_id.choices = tutor_list
    if form.validate_on_submit():
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, \
            email=form.email.data, secondary_email=form.secondary_email.data, \
            phone=form.phone.data, timezone=form.timezone.data, location=form.location.data, \
            role=form.role.data, status='active', is_admin=False)
        user.tutor_id=form.tutor_id.data
        user.status=form.status.data
        user.parent_id=form.parent_id.data
        if form.tutor_id.data == 0:
            user.tutor_id=None
        if form.parent_id.data == 0:
            user.parent_id=None
        if form.status.data == 'none':
            user.status=None
        try:
            db.session.add(user)
            db.session.commit()
            flash(user.first_name + ' added')
        except:
            db.session.rollback()
            flash(user.first_name + ' could not be added', 'error')
            return redirect(url_for('users'))
        return redirect(url_for('users'))
    return render_template('users.html', title="Users", form=form, active_users=active_users, \
        other_users=other_users, roles=roles)


@app.route('/edit-user/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(user.email, obj=user)
    selected_date_ids = []
    upcoming_dates = TestDate.query.order_by(TestDate.date).filter(TestDate.status != 'past')
    parents = User.query.order_by(User.first_name).filter_by(role='parent')
    parent_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in parents]
    tutors = User.query.order_by(User.first_name).filter_by(role='tutor')
    tutor_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in tutors]
    form.parent_id.choices = parent_list
    form.tutor_id.choices = tutor_list
    if form.validate_on_submit():
        if 'save' in request.form:
            user.first_name=form.first_name.data
            user.last_name=form.last_name.data
            user.email=form.email.data
            user.phone=form.phone.data
            user.secondary_email=form.secondary_email.data
            user.timezone=form.timezone.data
            user.location=form.location.data
            user.status=form.status.data
            user.role=form.role.data
            user.is_admin=form.is_admin.data
            user.session_reminders=form.session_reminders.data
            if form.tutor_id.data == 0:
                user.tutor_id=None
            else:
                user.tutor_id=form.tutor_id.data
            if form.parent_id.data == 0:
                user.parent_id=None
            else:
                user.parent_id=form.parent_id.data

            selected_date_ids = request.form.getlist('test_dates')
            for d in upcoming_dates:
                if str(d.id) in selected_date_ids:
                    user.add_test_date(d)
                else:
                    user.remove_test_date(d)
            try:
                db.session.add(user)
                db.session.commit()
                flash(user.first_name + ' updated')
            except:
                db.session.rollback()
                flash(user.first_name + ' could not be updated', 'error')
                return redirect(url_for('users'))
        elif 'delete' in request.form:
            db.session.delete(user)
            db.session.commit()
            flash('Deleted ' + user.first_name)
        else:
            flash('Code error in POST request', 'error')
        if user.role == 'student' or user.role == 'tutor':
            return redirect(url_for(user.role + 's'))
        else:
            return redirect(url_for('users'))
    elif request.method == "GET":
        form.first_name.data=user.first_name
        form.last_name.data=user.last_name
        form.email.data=user.email
        form.phone.data=user.phone
        form.secondary_email.data=user.secondary_email
        form.timezone.data=user.timezone
        form.location.data=user.location
        form.status.data=user.status
        form.role.data=user.role
        form.tutor_id.data=user.tutor_id
        form.parent_id.data=user.parent_id
        form.is_admin.data=user.is_admin
        form.session_reminders.data=user.session_reminders

        selected_dates = user.get_dates().all()
        for d in upcoming_dates:
            if d in selected_dates:
                selected_date_ids.append(d.id)

    return render_template('edit-user.html', title='Edit User', form=form, \
        user=user, upcoming_dates=upcoming_dates, selected_date_ids=selected_date_ids, \
        tests=tests)


@app.route('/students', methods=['GET', 'POST'])
@admin_required
def students():
    form = StudentForm()
    students = User.query.order_by(User.first_name).filter_by(role='student')
    tutors = User.query.filter_by(role='tutor')
    tutor_list = [(u.id, u.first_name + " " + u.last_name) for u in tutors]
    form.tutor_id.choices = tutor_list
    statuses = ['active', 'paused', 'inactive']
    other_students = User.query.filter((User.role=='student') & (User.status.notin_(statuses)))
    upcoming_dates = TestDate.query.order_by(TestDate.date).filter(TestDate.status != 'past')
    tests = sorted(set(TestDate.test for TestDate in TestDate.query.all()), reverse=True)
    if form.validate_on_submit():
        student = User(first_name=form.student_name.data, last_name=form.student_last_name.data, \
            email=form.student_email.data, phone=form.student_phone.data, timezone=form.timezone.data, \
            location=form.location.data, status=form.status.data, \
            tutor_id=form.tutor_id.data, role='student')
        parent = User(first_name=form.parent_name.data, last_name=form.parent_last_name.data, \
            email=form.parent_email.data, secondary_email=form.secondary_email.data, \
            phone=form.parent_phone.data, timezone=form.timezone.data, role='parent')

        try:
            db.session.add(parent)
            db.session.flush()
            student.parent_id = parent.id
            db.session.add(student)
            db.session.commit()
            selected_dates = request.form.getlist('test_dates')
            for d in upcoming_dates:
                if str(d.date) in selected_dates:
                    student.add_test_date(d)
        except:
            db.session.rollback()
            flash(student.first_name + ' could not be added', 'error')
            return redirect(url_for('students'))
        flash(student.first_name + ' added')
        return redirect(url_for('students'))
    return render_template('students.html', title="Students", form=form, students=students, \
        statuses=statuses, upcoming_dates=upcoming_dates, tests=tests, other_students=other_students)


@app.route('/tutors', methods=['GET', 'POST'])
@admin_required
def tutors():
    form = TutorForm()
    tutors = User.query.order_by(User.first_name).filter_by(role='tutor')
    statuses = User.query.with_entities(User.status).distinct()
    if form.validate_on_submit():
        tutor = User(first_name=form.first_name.data, last_name=form.last_name.data, \
            email=form.email.data, phone=form.phone.data, timezone=form.timezone.data, \
            session_reminders=form.session_reminders.data, status='active', role='tutor')
        try:
            db.session.add(tutor)
            db.session.commit()
            flash(tutor.first_name + ' added')
        except:
            db.session.rollback()
            flash(tutor.first_name + ' could not be added', 'error')
            return redirect(url_for('tutors'))
        return redirect(url_for('tutors'))
    return render_template('tutors.html', title="Tutors", form=form, tutors=tutors, statuses=statuses)


@app.route('/test-dates', methods=['GET', 'POST'])
def test_dates():
    form = TestDateForm()
    tests = TestDate.query.with_entities(TestDate.test).distinct()
    dates_filter = (TestDate.status == 'confirmed') | (TestDate.status == 'unconfirmed')
    upcoming_weekend_dates = TestDate.query.order_by(TestDate.date).filter(dates_filter)
    other_dates = TestDate.query.order_by(TestDate.date).filter(~dates_filter)
    if form.validate_on_submit():
        date = TestDate(test=form.test.data, date=form.date.data, \
            reg_date=form.reg_date.data, late_date=form.late_date.data, \
            other_date=form.other_date.data, status=form.status.data)
        try:
            db.session.add(date)
            db.session.commit()
            flash(date.date.strftime('%b %-d') + date.test.upper() + ' added')
        except:
            db.session.rollback()
            flash(date.date.strftime('%b %-d') + date.test.upper() + ' could not be added', 'error')
            return redirect(url_for('test_dates'))
        return redirect(url_for('test_dates'))
    return render_template('test-dates.html', title="Test dates", form=form, tests=tests, \
        upcoming_weekend_dates=upcoming_weekend_dates, other_dates=other_dates)


@app.route('/edit-date/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_date(id):
    form = TestDateForm()
    date = TestDate.query.get_or_404(id)
    students = date.students
    print(students)
    if form.validate_on_submit():
        if 'save' in request.form:
            date.test=form.test.data
            date.date=form.date.data
            date.reg_date=form.reg_date.data
            date.late_date=form.late_date.data
            date.other_date=form.other_date.data
            date.score_date=form.score_date.data
            date.status=form.status.data

            registered_students = request.form.getlist('registered_students')
            for s in students:
                if s in registered_students:
                    s.is_registered = True
                else:
                    s.is_registered = False
            try:
                db.session.add(date)
                db.session.commit()
                flash(date.date.strftime('%b %-d') + ' updated')
            except:
                db.session.rollback()
                flash(date.date.strftime('%b %-d') + ' could not be updated', 'error')
                return redirect(url_for('test_dates'))
        elif 'delete' in request.form:
            db.session.delete(date)
            db.session.commit()
            flash('Deleted ' + date.date.strftime('%b %-d'))
        else:
            flash('Code error in POST request', 'error')
        return redirect(url_for('test_dates'))
    elif request.method == "GET":
        form.test.data=date.test
        form.date.data=date.date
        form.reg_date.data=date.reg_date
        form.late_date.data=date.late_date
        form.other_date.data=date.other_date
        form.score_date.data=date.score_date
        form.status.data=date.status
    return render_template('edit-date.html', title='Edit date', form=form, date=date, students=students)


@app.route('/test-reminders', methods=['GET', 'POST'])
def test_reminders():
    form = EmailListForm()
    upcoming_dates = TestDate.query.order_by(TestDate.date).filter(TestDate.status != 'past')
    selected_date_ids = []
    if current_user.is_authenticated:
        user = User.query.filter_by(id=current_user.id).first_or_404()
        selected_dates = user.get_dates().all()
        for d in upcoming_dates:
            if d in selected_dates:
                selected_date_ids.append(d.id)
    if request.method == "POST":
        selected_date_ids = request.form.getlist('test_dates')
        if not current_user.is_authenticated:
            user = User.query.filter_by(email=form.email.data).first()
            if not user:
                user = User(first_name=form.first_name.data, last_name="", email=form.email.data)
            elif user and not user.password_hash:   # User exists without password
                email_status = send_password_reset_email(user)
            else:   # User has saved password
                flash('An account with this email already exists. Please log in.')
                return redirect(url_for('signin'))
        try:
            db.session.add(user)
            db.session.commit()
            for d in upcoming_dates:
                if str(d.id) in selected_date_ids:
                    user.add_test_date(d)
                else:
                    user.remove_test_date(d)
            if current_user.is_authenticated:
                flash('Test dates updated')
            else:
                email_status = send_password_reset_email(user)
                if email_status == 200:
                    flash("Welcome! Please check your inbox to verify your email.")
                else:
                    flash('Verification email did not send. Please contact ' + hello, 'error')
        except:
            db.session.rollback()
            flash('Test dates were not updated, please contact '+ hello, 'error')
        return redirect(url_for('index'))
    return render_template('test-reminders.html', form=form, tests=tests, \
        upcoming_dates=upcoming_dates, selected_date_ids=selected_date_ids)


@app.route('/griffin', methods=['GET', 'POST'])
def griffin():
    form = ScoreAnalysisForm()
    school='Griffin School'
    test='ACT'
    if form.validate_on_submit():
        student = User(first_name=form.student_first_name.data, last_name=form.student_last_name.data)
        parent = User(first_name=form.parent_first_name.data, email=form.parent_email.data)
        email_status = send_score_analysis_email(student, parent, school)
        if email_status == 200:
            return render_template('score-analysis-requested.html', email=form.parent_email.data)
        else:
            flash('Email failed to send, please contact ' + hello, 'error')
    return render_template('school.html', form=form, school=school, test=test)


@app.route('/appamada', methods=['GET', 'POST'])
def appamada():
    form = ScoreAnalysisForm()
    school='Appamada School'
    test='mini SAT'
    if form.validate_on_submit():
        student = User(first_name=form.student_first_name.data, last_name=form.student_last_name.data)
        parent = User(first_name=form.parent_first_name.data, email=form.parent_email.data)
        email_status = send_score_analysis_email(student, parent, school)
        if email_status == 200:
            return render_template('score-analysis-requested.html', email=form.parent_email.data)
        else:
            flash('Email failed to send, please contact ' + hello, 'error')
    return render_template('school.html', form=form, school=school, test=test)


@app.route('/huntington-surrey', methods=['GET', 'POST'])
def huntington_surrey():
    form = ScoreAnalysisForm()
    school='Huntington-Surrey School'
    test='SAT'
    if form.validate_on_submit():
        student = User(first_name=form.student_first_name.data, last_name=form.student_last_name.data)
        parent = User(first_name=form.parent_first_name.data, email=form.parent_email.data)
        email_status = send_score_analysis_email(student, parent, school)
        if email_status == 200:
            return render_template('score-analysis-requested.html', email=form.parent_email.data)
        else:
            flash('Email failed to send, please contact ' + hello, 'error')
    return render_template('school.html', form=form, school=school, test=test)


@app.route('/sat-act-data')
def sat_act_data():
    return render_template('sat-act-data.html', title="SAT & ACT data")


@app.route('/test-strategies', methods=['GET', 'POST'])
def test_strategies():
    form = TestStrategiesForm()
    if form.validate_on_submit():
        relation = form.relation.data
        if relation == 'student':
            student = User(first_name=form.first_name.data, email=form.email.data)
            parent = User(first_name=form.parent_name.data, email=form.parent_email.data)
        elif relation == 'parent':
            parent = User(first_name=form.first_name.data, email=form.email.data)
            student = User(first_name=form.student_name.data)
        email_status = send_test_strategies_email(student, parent, relation)
        if email_status == 200:
            return render_template('test-strategies-sent.html', email=form.email.data, relation=relation)
        else:
            flash('Email failed to send, please contact ' + hello, 'error')
    return render_template('test-strategies.html', form=form)


@app.route("/download/<filename>")
def download_file (filename):
    path = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(path, filename, as_attachment=False)


@app.route('/practice-test-sent')
def free_test_sent():
    return render_template('practice-test-sent.html')


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicons/favicon.ico')

@app.route('/manifest.webmanifest')
def webmanifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicons/manifest.webmanifest')

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
