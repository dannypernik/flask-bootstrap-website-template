import os
from flask import Flask, render_template, flash, Markup, redirect, url_for, request, send_from_directory, send_file
from app import app, db, hcaptcha
from app.forms import InquiryForm, TestStrategiesForm, SignupForm, LoginForm, StudentForm, ScoreAnalysisForm, PracticeTestForm, TutorForm, TestDateForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Student, Tutor, TestDate
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_contact_email, send_test_strategies_email, send_score_analysis_email, send_practice_test_email

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_viewed = datetime.utcnow()
        db.session.commit()

def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicons/favicon.ico')

@app.route('/manifest.webmanifest')
def webmanifest():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'img/favicons/manifest.webmanifest')

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
        db.session.add(user)
        db.session.commit()
        send_contact_email(user, message, subject)
        flash('Please check ' + user.email + ' for a confirmation email. Thank you for reaching out!')
        return redirect(url_for('index', _anchor="home"))
    return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))


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
            user = Student(student_email=form.email.data, parent_name=form.parent_name.data, \
            parent_email=form.parent_email.data)
            student = form.first_name.data
        elif relation == 'parent':
            user = Student(parent_name=form.first_name.data, parent_email=form.email.data)
            student = form.student_name.data
        send_test_strategies_email(user, relation, student)
        return render_template('test-strategies-sent.html', email=form.email.data, relation=relation)
    return render_template('test-strategies.html', form=form)


@app.route("/download/<filename>")
def download_file (filename):
    path = os.path.join(app.root_path, 'static/files/')
    return send_from_directory(path, filename, as_attachment=False)


@app.route('/practice_test_sent')
def free_test_sent():
    return render_template('practice-test-sent.html')

@app.route('/about')
def about():
    return render_template('about.html', title="About")

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', title="Reviews")

@app.route('/griffin', methods=['GET', 'POST'])
def griffin():
    form = ScoreAnalysisForm()
    school='Griffin School'
    test='ACT'
    if form.validate_on_submit():
        student = Student(student_name=form.student_first_name.data, \
        last_name=form.student_last_name.data, parent_name=form.parent_first_name.data, \
        parent_email=form.parent_email.data)
        send_score_analysis_email(student, school)
        return render_template('score-analysis-requested.html', email=form.parent_email.data)
    return render_template('griffin.html', form=form, school=school, test=test)

@app.route('/skybridge', methods=['GET', 'POST'])
def skybridge():
    form = ScoreAnalysisForm()
    school='Skybridge Academy'
    test='SAT'
    if form.validate_on_submit():
        student = Student(student_name=form.student_first_name.data, \
        last_name=form.student_last_name.data, parent_name=form.parent_first_name.data, \
        parent_email=form.parent_email.data)
        send_score_analysis_email(student, school)
        return render_template('score-analysis-requested.html', email=form.parent_email.data)
    return render_template('skybridge.html', form=form, school=school, test=test)

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
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('students')
        return redirect(next_page)
    return render_template('login.html', title="Login", form=form)

@app.route('/students', methods=['GET', 'POST'])
@login_required
def students():
    form = StudentForm()
    students = Student.query.order_by(Student.student_name).all()
    statuses = Student.query.with_entities(Student.status).distinct()
    if form.validate_on_submit():
        student = Student(student_name=form.student_name.data, last_name=form.last_name.data, \
        student_email=form.student_email.data, parent_name=form.parent_name.data, \
        parent_email=form.parent_email.data, secondary_email=form.secondary_email.data, \
        timezone=form.timezone.data, location=form.location.data, status=form.status.data, \
        tutor=form.tutor_id.data)
        try:
            db.session.add(student)
            db.session.commit()
        except:
            db.session.rollback()
            flash(student.student_name + ' could not be added', 'error')
            return redirect(url_for('students'))
        flash(student.student_name + ' added')
        return redirect(url_for('students'))
    return render_template('students.html', title="Students", form=form, students=students, statuses=statuses)

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    form = StudentForm()
    student = Student.query.get_or_404(id)
    if form.validate_on_submit():
        if 'save' in request.form:
            student.student_name=form.student_name.data
            student.last_name=form.last_name.data
            student.student_email=form.student_email.data
            student.parent_name=form.parent_name.data
            student.parent_email=form.parent_email.data
            student.secondary_email=form.secondary_email.data
            student.timezone=form.timezone.data
            student.location=form.location.data
            student.status=form.status.data
            student.tutor=form.tutor_id.data
            try:
                db.session.add(student)
                db.session.commit()
                flash(student.student_name + ' updated')
            except:
                db.session.rollback()
                flash(student.student_name + ' could not be updated', 'error')
                return redirect(url_for('students'))
            finally:
                db.session.close()
        elif 'delete' in request.form:
            db.session.delete(student)
            db.session.commit()
            flash('Deleted ' + student.student_name)
        else:
            flash('Code error in POST request', 'error')
        return redirect(url_for('students'))
    elif request.method == "GET":
        form.student_name.data=student.student_name
        form.last_name.data=student.last_name
        form.student_email.data=student.student_email
        form.parent_name.data=student.parent_name
        form.parent_email.data=student.parent_email
        form.secondary_email.data=student.secondary_email
        form.timezone.data=student.timezone
        form.location.data=student.location
        form.status.data=student.status
        form.tutor_id.data=student.tutor
    return render_template('edit-student.html', title='Edit Student',
                           form=form, student=student)


@app.route('/tutors', methods=['GET', 'POST'])
@login_required
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

@app.route('/edit_tutor/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tutor(id):
    form = TutorForm()
    tutor = Tutor.query.get_or_404(id)
    if form.validate_on_submit():
        if 'save' in request.form:
            tutor.first_name=form.first_name.data
            tutor.last_name=form.last_name.data
            tutor.email=form.email.data
            tutor.timezone=form.timezone.data
            tutor.status=form.status.data
            try:
                db.session.add(tutor)
                db.session.commit()
                flash(tutor.first_name + ' updated')
            except:
                db.session.rollback()
                flash(tutor.first_name + ' could not be updated', 'error')
                return redirect(url_for('tutors'))
            finally:
                db.session.close()
        elif 'delete' in request.form:
            db.session.delete(tutor)
            db.session.commit()
            flash('Deleted ' + tutor.first_name)
        else:
            flash('Code error in POST request', 'error')
        return redirect(url_for('tutors'))
    elif request.method == "GET":
        form.first_name.data=tutor.first_name
        form.last_name.data=tutor.last_name
        form.email.data=tutor.email
        form.timezone.data=tutor.timezone
        form.status.data=tutor.status
    return render_template('edit-tutor.html', title='Edit Tutor', form=form, tutor=tutor)


@app.route('/test_dates', methods=['GET', 'POST'])
@login_required
def test_dates():
    form = TestDateForm()
    tests = TestDate.query.with_entities(TestDate.test).distinct()
    dates = TestDate.query.order_by(TestDate.date).all()
    if form.validate_on_submit():
        print(form.test.data, form.date.data)
        date = TestDate(test=form.test.data, date=form.date.data, \
        reg_date=form.reg_date.data, late_date=form.late_date.data, status=form.status.data)
        try:
            db.session.add(date)
            db.session.commit()
            flash(date.date.strftime('%b %-d') + ' added')
        except:
            db.session.rollback()
            flash(date.date.strftime('%b %-d') + ' could not be added', 'error')
            return redirect(url_for('test_dates'))
        return redirect(url_for('test_dates'))
    return render_template('test-dates.html', title="Test dates", form=form, dates=dates, tests=tests)


@app.route('/edit_date/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_date(id):
    form = TestDateForm()
    date = TestDate.query.get_or_404(id)
    if form.validate_on_submit():
        if 'save' in request.form:
            date.test=form.test.data
            date.date=form.date.data
            date.reg_date=form.reg_date.data
            date.late_date=form.late_date.data
            date.status=form.status.data
            try:
                db.session.add(date)
                db.session.commit()
                flash(date.date.strftime('%b %-d') + ' updated')
            except:
                db.session.rollback()
                flash(date.date.strftime('%b %-d') + ' could not be updated', 'error')
                return redirect(url_for('test_dates'))
            finally:
                db.session.close()
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
        form.status.data=date.status
    return render_template('edit-date.html', title='Edit date', form=form, date=date)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        flash('You are already signed in')
        return redirect(url_for('index'))
    form = SignupForm()
    if form.validate_on_submit():
        username_check = User.query.filter_by(username=form.email.data).first()
        if username_check is not None:
            flash('User already exists', 'error')
            return redirect(url_for('signup'))
        user = User(first_name=form.first_name.data, last_name=form.last_name.data, \
        email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("You are now registered. We're glad you're here!")
        return redirect(url_for('index'))
    return render_template('signup.html', title='Sign up', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile/<username>')
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('profile.html', user=user, posts=posts)

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def static_from_root():
    return send_from_directory(app.static_folder, request.path[1:])
