import os
from flask import Flask, render_template, flash, Markup, redirect, url_for, \
    request, send_from_directory, send_file
from app import app, db, login, hcaptcha
from app.forms import InquiryForm, TestStrategiesForm, SignupForm, LoginForm, \
    StudentForm, ScoreAnalysisForm, PracticeTestForm, TestDateForm, \
    UserForm, RequestPasswordResetForm, ResetPasswordForm
from flask_login import current_user, login_user, logout_user, login_required, login_url
from app.models import User, TestDate, UserTestDate
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_contact_email, send_password_reset_email, \
    send_test_strategies_email, send_score_analysis_email, send_practice_test_email
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

def admin_required(f):
    @login_required
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            flash('You must have administrator privileges to access this page.', 'error')
            logout_user()
            return redirect(login_url('login', next_url=request.url))
    return wrap


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = InquiryForm()
    if form.validate_on_submit():
        if hcaptcha.verify():
            pass
        else:
            flash('Please verify that you are human.', 'error')
            return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))
        user = User(first_name=form.first_name.data, email=form.email.data, phone=form.phone.data)
        message = form.message.data
        subject = form.subject.data
        send_contact_email(user, message, subject)
        flash('Please check ' + user.email + ' for a confirmation email. Thank you for reaching out!')
        return redirect(url_for('index', _anchor="home"))
    return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))


@app.route('/about')
def about():
    return render_template('about.html', title="About")

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', title="Reviews")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash('You are already signed in')
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        email_check = User.query.filter_by(email=form.email.data).first()
        if email_check is not None:
            flash('A user with that email already exists', 'error')
            return redirect(url_for('signup'))
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, \
        email=form.email.data)
        # TODO: Add user fields
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        # TODO: Send verification email
        flash("You are now registered. We're glad you're here!")
        return redirect(url_for('index'))
    return render_template('signup.html', title='Sign up', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('You are already signed in')
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next = request.args.get('next')
        if not next or url_parse(next).netloc != '':
            next = url_for('students')
        return redirect(next)
    return render_template('login.html', title="Login", form=form)


@app.route('/request_password_reset', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for instructions to reset your password.')
        return redirect(url_for('login'))
    return render_template('request-password-reset.html', title='Reset password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset-password.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    form = UserForm()
    active_users = User.query.order_by(User.first_name).filter((User.status=='active'))# & (User.role != 'student'))
    other_users = User.query.order_by(User.first_name).filter((User.status != 'active') | (User.status == None) | \
        (User.role == None))
    roles = ['student', 'tutor', 'admin']
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
        if form.tutor_id.data == 0:
            user.tutor_id=None
        else:
            user.tutor_id=form.tutor_id.data
        if form.parent_id.data == 0:
            user.parent_id=None
        else:
            user.parent_id=form.parent_id.data
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


@app.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    form = UserForm()
    user = User.query.get_or_404(id)
    selected_date_ids = []
    parents = User.query.order_by(User.first_name).filter_by(role='parent')
    parent_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in parents]
    tutors = User.query.order_by(User.first_name).filter_by(role='tutor')
    tutor_list = [(0,'')]+[(u.id, u.first_name + " " + u.last_name) for u in tutors]
    form.parent_id.choices = parent_list
    form.tutor_id.choices = tutor_list
    upcoming_dates = TestDate.query.order_by(TestDate.date).filter(TestDate.status != 'past')
    tests = sorted(set(TestDate.test for TestDate in TestDate.query.all()), reverse=True)
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

        selected_dates = request.form.getlist('test_dates')
        for d in upcoming_dates:
            if str(d.date) in selected_dates:
                student.add_test_date(d)

        try:
            db.session.add(parent)
            db.session.flush()
            student.parent_id = parent.id
            db.session.add(student)
            db.session.commit()
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
    tutors = Tutor.query.order_by(Tutor.first_name).all()
    statuses = Tutor.query.with_entities(Tutor.status).distinct()
    if form.validate_on_submit():
        tutor = Tutor(first_name=form.first_name.data, last_name=form.last_name.data, \
        email=form.email.data, timezone=form.timezone.data)
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


@app.route('/test_dates', methods=['GET', 'POST'])
@admin_required
def test_dates():
    form = TestDateForm()
    tests = TestDate.query.with_entities(TestDate.test).distinct()
    upcoming_dates = TestDate.query.order_by(TestDate.date).filter(TestDate.status != 'past')
    past_dates = TestDate.query.order_by(TestDate.date.desc()).filter(TestDate.status == 'past')
    if form.validate_on_submit():
        print(form.test.data, form.date.data)
        date = TestDate(test=form.test.data, date=form.date.data, \
            reg_date=form.reg_date.data, late_date=form.late_date.data, \
            other_date=form.other_date.data, status=form.status.data)
        try:
            db.session.add(date)
            db.session.commit()
            flash(date.date.strftime('%b %-d') + ' added')
        except:
            db.session.rollback()
            flash(date.date.strftime('%b %-d') + ' could not be added', 'error')
            return redirect(url_for('test_dates'))
        return redirect(url_for('test_dates'))
    return render_template('test-dates.html', title="Test dates", form=form, \
        upcoming_dates=upcoming_dates, past_dates=past_dates, tests=tests)


@app.route('/edit_date/<int:id>', methods=['GET', 'POST'])
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
                if str(s.student_id) in registered_students:
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


@app.route('/griffin', methods=['GET', 'POST'])
def griffin():
    form = ScoreAnalysisForm()
    school='Griffin School'
    test='ACT'
    if form.validate_on_submit():
        student = User(first_name=form.student_first_name.data, last_name=form.student_last_name.data)
        parent = User(first_name=form.parent_first_name.data, email=form.parent_email.data)
        send_score_analysis_email(student, parent, school)
        return render_template('score-analysis-requested.html', email=form.parent_email.data)
    return render_template('school.html', form=form, school=school, test=test)

@app.route('/appamada', methods=['GET', 'POST'])
def appamada():
    form = ScoreAnalysisForm()
    school='Appamada School'
    test='mini SAT'
    if form.validate_on_submit():
        student = User(first_name=form.student_first_name.data, last_name=form.student_last_name.data)
        parent = User(first_name=form.parent_first_name.data, email=form.parent_email.data)
        send_score_analysis_email(student, parent, school)
        return render_template('score-analysis-requested.html', email=form.parent_email.data)
    return render_template('school.html', form=form, school=school, test=test)


@app.route('/huntington-surrey', methods=['GET', 'POST'])
def huntington_surrey():
    form = ScoreAnalysisForm()
    school='Huntington-Surrey School'
    test='SAT'
    if form.validate_on_submit():
        student = Student(student_name=form.student_first_name.data, \
        last_name=form.student_last_name.data, parent_name=form.parent_first_name.data, \
        parent_email=form.parent_email.data)
        send_score_analysis_email(student, school)
        return render_template('score-analysis-requested.html', email=form.parent_email.data)
    return render_template('school.html', form=form, school=school, test=test)


@app.route('/sat-act-data')
def sat_act_data():
    return render_template('sat-act-data.html', title="SAT & ACT data")


@app.route('/practice_test', methods=['GET', 'POST'])
def practice_test():
    form = PracticeTestForm()
    if form.validate_on_submit():
        relation = form.relation.data
        if relation == 'student':
            user = Student(student_email=form.email.data, parent_name=form.parent_name.data, \
            parent_email=form.parent_email.data)
            student = form.first_name.data
        elif relation == 'parent':
            user = Student(parent_name=form.first_name.data, parent_email=form.email.data)
            student = form.student_name.data
        test = form.test.data
        send_practice_test_email(user, test, relation, student)
        return render_template('practice-test-sent.html', test=test, email=form.email.data, relation=relation)
    return render_template('practice-test.html', form=form)


@app.route('/test_strategies', methods=['GET', 'POST'])
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
        send_test_strategies_email(student, parent, relation)
        return render_template('test-strategies-sent.html', email=form.email.data, relation=relation)
    return render_template('test-strategies.html', form=form)


@app.route("/download/<filename>")
def download_file (filename):
    path = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(path, filename, as_attachment=False)


@app.route('/practice_test_sent')
def free_test_sent():
    return render_template('practice-test-sent.html')


@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('profile.html', user=user, posts=posts)


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
