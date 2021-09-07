import os
from flask import Flask, render_template, flash, Markup, redirect, url_for, request, send_from_directory
from app import app, db
from app.forms import InquiryForm, EmailForm, SignupForm, LoginForm, StudentForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Student
from werkzeug.urls import url_parse
from datetime import datetime
from app.email import send_contact_email

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
        user = User(first_name=form.first_name.data, email=form.email.data, phone=form.phone.data)
        message = form.message.data
        db.session.add(user)
        db.session.commit()
        send_contact_email(user, message)
        print(app.config['ADMINS'])
        flash("Thank you for your message. We will be in touch!")
        return redirect(url_for('index', _anchor="home"))
    return render_template('index.html', form=form, last_updated=dir_last_updated('app/static'))

@app.route('/about')
def about():
    return render_template('about.html', title="About")

@app.route('/reviews')
def reviews():
    return render_template('reviews.html', title="Reviews")

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
    if form.validate_on_submit():
        student = Student(student_name=form.student_name.data, student_email=form.student_email.data, \
        parent_name=form.parent_name.data, parent_email=form.parent_email.data, \
        timezone=form.timezone.data, location=form.location.data)
        try:
            db.session.add(student)
            db.session.commit()
        except:
            db.session.rollback()
            flash('Student name already exists', 'error')
            return redirect(url_for('students'))
        finally:
            db.session.close()
        flash("Student added")
        return redirect(url_for('students'))
    return render_template('students.html', title="Students", form=form, students=students)

@app.route('/edit_student/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    form = StudentForm()
    student = Student.query.get_or_404(id)
    if form.validate_on_submit():
        if 'save' in request.form:
            student.student_name=form.student_name.data
            student.student_email=form.student_email.data
            student.parent_name=form.parent_name.data
            student.parent_email=form.parent_email.data
            student.timezone=form.timezone.data
            student.location=form.location.data
            student.active=form.active.data
            try:
                db.session.add(student)
                db.session.commit()
                flash("Student updated")
            except:
                db.session.rollback()
                flash('Student name already exists', 'error')
                return redirect(url_for('students'))
            finally:
                db.session.close()
        elif 'delete' in request.form:
            db.session.delete(student)
            db.session.commit()
            flash("Deleted " + student.student_name)
        else:
            flash('Code error in POST request', 'error')
        return redirect(url_for('students'))
    elif request.method == "GET":
        form.student_name.data=student.student_name
        form.student_email.data=student.student_email
        form.parent_name.data=student.parent_name
        form.parent_email.data=student.parent_email
        form.timezone.data=student.timezone
        form.location.data=student.location
        form.active.data=student.active
    return render_template('edit-student.html', title='Edit Student',
                           form=form, student=student)


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
    return render_template('ignup.html', title='Sign up', form=form)

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
